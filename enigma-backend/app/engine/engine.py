"""
ENIGMA Engine — Execution Engine

Implements TASK-001 (Execution Engine) and TASK-004 (Execution Pipeline).

The ExecutionEngine is the single entry point for running any Worker:

    engine = ExecutionEngine()
    engine.register(my_worker)              # TASK-001: Register Worker
    result = await engine.execute("my_worker", ctx)  # Execute

Every WorkerResult returned by ``execute`` carries:
    - status          (pending/running/success/failed)
    - result          (worker payload)
    - execution_time  (wall-clock seconds, measured by the Engine)
    - confidence      (0–1, set by the Worker)
    - llm_calls       (count of LLM requests, set by the Worker)
    - memory_usage_mb (peak Python allocations during the run)
    - evidence        (Evidence-First Architecture)

The Engine also emits WorkerEvents to the EventBus for the Live Console,
persists execution records to the database for the Developer Dashboard, and
can orchestrate multi-worker pipelines (User Brain -> Engine -> Worker -> ...).
"""
from __future__ import annotations

import asyncio
import time
import tracemalloc
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.engine.contracts import (
    ExecutionContext,
    Worker,
    WorkerEvent,
    WorkerResult,
    WorkerStatus,
)
from app.engine.events import event_bus


class ExecutionEngine:
    """
    Central orchestrator for Worker execution.

    Thread/async-safe: a per-execution ``asyncio.Lock`` keyed by execution_id
    ensures that concurrent execute() calls for the same pipeline don't
    interleave event emissions.
    """

    def __init__(self) -> None:
        self._workers: Dict[str, Worker] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    # ------------------------------------------------------------------ register
    def register(self, worker: Worker) -> Worker:
        """Register a Worker so the Engine can discover and execute it.

        Emits a ``worker_registered`` event to the EventBus history (replayed
        to any future WebSocket client).  Uses ``emit_sync`` because
        ``register`` is a synchronous call that may happen outside an async
        context (e.g. during FastAPI lifespan / import time).
        """
        if not worker.name:
            raise ValueError("Worker must have a non-empty 'name' attribute")
        self._workers[worker.name] = worker
        event_bus.emit_sync(WorkerEvent(
            worker_name=worker.name,
            type="worker_registered",
            message=f"Worker '{worker.name}' registered",
            data={
                "description": worker.description,
                "input_schema": worker.input_schema,
                "output_schema": worker.output_schema,
            },
        ))
        return worker

    def register_many(self, workers: List[Worker]) -> None:
        """Register a list of Workers."""
        for w in workers:
            self.register(w)

    # ------------------------------------------------------------------ registry
    def get_worker(self, name: str) -> Optional[Worker]:
        return self._workers.get(name)

    def list_workers(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": w.name,
                "description": w.description,
                "input_schema": w.input_schema,
                "output_schema": w.output_schema,
            }
            for w in self._workers.values()
        ]

    @property
    def registered_names(self) -> List[str]:
        return list(self._workers.keys())

    # ------------------------------------------------------------------ execute
    async def execute(
        self,
        worker_name: str,
        context: ExecutionContext,
        *,
        save: bool = True,
        db: Optional[AsyncSession] = None,
    ) -> WorkerResult:
        """
        Execute a single registered Worker.

        Parameters
        ----------
        worker_name : str
            Name of the registered Worker to run.
        context : ExecutionContext
            Shared execution context.  May carry an ``emit`` callable for
            live events (the Engine wires one up automatically).
        save : bool
            If True (and a DB session is available), persist the execution
            record + event log for the Developer Dashboard.
        db : AsyncSession | None
            Optional DB session for persistence.

        Returns
        -------
        WorkerResult
        """
        worker = self._workers.get(worker_name)
        if worker is None:
            raise KeyError(f"Worker '{worker_name}' is not registered")

        execution_id = context.execution_id or str(uuid.uuid4())
        if not context.execution_id:
            context.execution_id = execution_id

        lock = self._locks.setdefault(execution_id, asyncio.Lock())

        async with lock:
            # Wire up the event emitter so workers can emit live events
            if context.emit is None:
                async def _emit(event: WorkerEvent) -> None:
                    event.execution_id = execution_id
                    await event_bus.broadcast(event)
                    if save and db is not None:
                        await self._log_event(db, execution_id, worker_name, event)
                context.emit = _emit

            # Announce start
            started_at = datetime.utcnow()
            await event_bus.broadcast(WorkerEvent(
                worker_name=worker_name,
                type="execution_started",
                message=f"Execution started for '{worker_name}'",
                data={"execution_id": execution_id},
            ))

            tracemalloc.start()
            start_perf = time.perf_counter()

            result = WorkerResult(
                worker_name=worker_name,
                status=WorkerStatus.RUNNING,
                started_at=started_at,
            )

            try:
                # Call optional setup hook
                await worker.setup(context)

                # The worker returns its own WorkerResult; we merge timing/memory
                worker_result = await worker.run(context)

                elapsed = time.perf_counter() - start_perf
                current, peak = tracemalloc.get_traced_memory()

                # Merge engine-measured fields onto the worker's result
                result.status = worker_result.status
                result.result = worker_result.result
                result.evidence = worker_result.evidence
                result.confidence = worker_result.confidence
                result.llm_calls = worker_result.llm_calls
                result.memory_usage_mb = peak / (1024 * 1024)
                result.execution_time = elapsed
                result.completed_at = datetime.utcnow()

                if worker_result.error:
                    result.status = WorkerStatus.FAILED
                    result.error = worker_result.error

                if result.status == WorkerStatus.SUCCESS:
                    await event_bus.broadcast(WorkerEvent(
                        worker_name=worker_name,
                        type="finished",
                        message=f"Worker '{worker_name}' completed in {elapsed:.2f}s",
                        data={
                            "execution_id": execution_id,
                            "confidence": result.confidence,
                            "llm_calls": result.llm_calls,
                            "result": result.result,
                            "evidence_count": len(result.evidence),
                        },
                    ))
                else:
                    await event_bus.broadcast(WorkerEvent(
                        worker_name=worker_name,
                        type="error",
                        message=f"Worker '{worker_name}' finished with status {result.status.value}",
                        data={"execution_id": execution_id, "error": result.error or ""},
                    ))

            except Exception as exc:
                elapsed = time.perf_counter() - start_perf
                result.status = WorkerStatus.FAILED
                result.error = str(exc)
                result.execution_time = elapsed
                result.completed_at = datetime.utcnow()
                await event_bus.broadcast(WorkerEvent(
                    worker_name=worker_name,
                    type="error",
                    message=f"Worker '{worker_name}' failed: {exc}",
                    data={"execution_id": execution_id, "error": str(exc)},
                ))
                import traceback
                tb = traceback.format_exc()
                if result.metadata is None:
                    result.metadata = {}
                result.metadata["traceback"] = tb
            finally:
                tracemalloc.stop()
                # Call optional teardown hook
                try:
                    await worker.teardown(context)
                except Exception:
                    pass

            # Persist to DB
            if save and db is not None:
                await self._save_execution(db, execution_id, worker_name, result)

            # Remember in context history
            context.add_history(result)

            return result

    # ------------------------------------------------------------------ orchestrate
    async def orchestrate(
        self,
        plan: List[Dict[str, Any]],
        context: ExecutionContext,
        *,
        db: Optional[AsyncSession] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a multi-worker pipeline.

        ``plan`` is a list of steps, each describing a worker to run:

            [
                {"step": 1, "worker": "title_analysis", "input": {...}},
                {"step": 2, "worker": "category_classification", "input": {...}},
            ]

        Each step's output is written to ``context.memory`` under the worker
        name so downstream steps can read it.  This implements the
        User Brain -> Engine -> Worker -> Result -> ... pipeline.
        """
        results: List[Dict[str, Any]] = []
        pipeline_id = context.execution_id or str(uuid.uuid4())
        context.execution_id = pipeline_id

        await event_bus.broadcast(WorkerEvent(
            worker_name="pipeline",
            type="execution_started",
            message=f"Pipeline started with {len(plan)} steps",
            data={"execution_id": pipeline_id, "workers": [s["worker"] for s in plan]},
        ))

        for step in plan:
            worker_name = step["worker"]
            step_input = step.get("input", {})

            # merge step input into context.memory
            for k, v in step_input.items():
                context.remember(k, v)

            try:
                result = await self.execute(
                    worker_name,
                    context,
                    save=save,
                    db=db,
                )
                results.append(result.to_dict())
            except KeyError:
                await event_bus.broadcast(WorkerEvent(
                    worker_name=worker_name,
                    type="error",
                    message=f"Worker '{worker_name}' not registered (pipeline step skipped)",
                    data={"execution_id": pipeline_id},
                ))
                results.append({
                    "worker_name": worker_name,
                    "status": "failed",
                    "error": "worker not registered",
                })

        await event_bus.broadcast(WorkerEvent(
            worker_name="pipeline",
            type="finished",
            message=f"Pipeline completed: {len(results)} steps",
            data={"execution_id": pipeline_id, "results": results},
        ))

        return {"execution_id": pipeline_id, "results": results, "context_memory": context.memory}

    # ------------------------------------------------------------------ persistence
    async def _save_execution(
        self,
        db: AsyncSession,
        execution_id: str,
        worker_name: str,
        result: WorkerResult,
    ) -> None:
        try:
            from app.models.execution import WorkerExecution
            exec_record = WorkerExecution(
                id=execution_id,
                worker_name=worker_name,
                status=result.status.value if isinstance(result.status, WorkerStatus) else result.status,
                execution_time=result.execution_time,
                confidence=result.confidence,
                llm_calls=result.llm_calls,
                memory_usage_mb=result.memory_usage_mb,
                error=result.error,
                result=result.result,
                evidence=result.evidence,
                started_at=result.started_at,
                completed_at=result.completed_at,
            )
            db.add(exec_record)
            await db.commit()
        except Exception:
            await db.rollback()

    async def _log_event(
        self,
        db: AsyncSession,
        execution_id: str,
        worker_name: str,
        event: WorkerEvent,
    ) -> None:
        try:
            from app.models.execution import WorkerEventLog
            log = WorkerEventLog(
                id=str(uuid.uuid4()),
                execution_id=execution_id,
                worker_name=worker_name,
                event_type=event.type,
                message=event.message,
                data=event.data,
                timestamp=event.timestamp,
            )
            db.add(log)
            await db.commit()
        except Exception:
            await db.rollback()

    # ------------------------------------------------------------------ queries
    async def get_execution_record(
        self,
        db: AsyncSession,
        execution_id: str,
    ) -> Optional[Dict[str, Any]]:
        from app.models.execution import WorkerExecution
        result = await db.execute(
            select(WorkerExecution).where(WorkerExecution.id == execution_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return {
            "id": str(record.id),
            "worker_name": record.worker_name,
            "status": record.status,
            "result": record.result,
            "evidence": record.evidence,
            "confidence": record.confidence,
            "execution_time": record.execution_time,
            "llm_calls": record.llm_calls,
            "memory_usage_mb": record.memory_usage_mb,
            "error": record.error,
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        }

    async def get_recent_executions(
        self,
        db: AsyncSession,
        limit: int = 50,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        from app.models.execution import WorkerExecution
        stmt = select(WorkerExecution).order_by(desc(WorkerExecution.started_at))
        if status_filter:
            stmt = stmt.where(WorkerExecution.status == status_filter)
        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "worker_name": r.worker_name,
                "status": r.status,
                "confidence": r.confidence,
                "execution_time": r.execution_time,
                "llm_calls": r.llm_calls,
                "memory_usage_mb": r.memory_usage_mb,
                "error": r.error,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in records
        ]

    async def get_event_logs(
        self,
        db: AsyncSession,
        execution_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        from app.models.execution import WorkerEventLog
        stmt = select(WorkerEventLog).order_by(desc(WorkerEventLog.timestamp))
        if execution_id:
            stmt = stmt.where(WorkerEventLog.execution_id == execution_id)
        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "execution_id": r.execution_id,
                "worker_name": r.worker_name,
                "event_type": r.event_type,
                "message": r.message,
                "data": r.data,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in records
        ]


# Global singleton engine
engine = ExecutionEngine()
