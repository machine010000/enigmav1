"""
Developer Dashboard API Router — TASK-005

Provides the aggregate metrics the Developer Dashboard needs:
  - Running workers (currently in-memory)
  - Completed executions
  - Failed executions
  - Execution time summary
  - Logs (event log entries)
  - Memory usage
  - LLM call counts
  - Confidence scores
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engine.engine import engine
from app.engine.events import event_bus
from app.models.decision import Decision
from app.models.execution import WorkerExecution, WorkerEventLog
from app.routers.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
async def dashboard_overview(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a full dashboard snapshot."""
    # Aggregate stats from DB
    total = await db.execute(select(func.count()).select_from(WorkerExecution))
    total_count = total.scalar_one()

    completed = await db.execute(
        select(func.count()).where(WorkerExecution.status == "success")
    )
    completed_count = completed.scalar_one()

    failed = await db.execute(
        select(func.count()).where(WorkerExecution.status == "failed")
    )
    failed_count = failed.scalar_one()

    running = await db.execute(
        select(func.count()).where(WorkerExecution.status == "running")
    )
    running_count = running.scalar_one()

    total_time = await db.execute(select(func.sum(WorkerExecution.execution_time)))
    total_exec_time = float(total_time.scalar_one() or 0)

    total_llm = await db.execute(select(func.sum(WorkerExecution.llm_calls)))
    total_llm_calls = int(total_llm.scalar_one() or 0)

    total_mem = await db.execute(select(func.max(WorkerExecution.memory_usage_mb)))
    max_memory = float(total_mem.scalar_one() or 0)

    avg_conf = await db.execute(select(func.avg(WorkerExecution.confidence)))
    avg_confidence = round(float(avg_conf.scalar_one() or 0), 4)

    # Recent executions
    recent = await engine.get_recent_executions(db, limit=20)

    # Recent event logs
    logs = await engine.get_event_logs(db, limit=50)

    decision_stmt = (
        select(Decision)
        .order_by(desc(Decision.created_at))
        .limit(20)
    )
    decision_result = await db.execute(decision_stmt)
    decisions = [decision.to_dict() for decision in decision_result.scalars().all()]

    # Worker breakdown
    breakdown_stmt = (
        select(
            WorkerExecution.worker_name,
            func.count().label("count"),
            func.avg(WorkerExecution.execution_time).label("avg_time"),
            func.avg(WorkerExecution.confidence).label("avg_conf"),
            func.sum(WorkerExecution.llm_calls).label("llm_calls"),
        )
        .group_by(WorkerExecution.worker_name)
    )
    breakdown_result = await db.execute(breakdown_stmt)
    worker_breakdown = [
        {
            "worker": row.worker_name,
            "count": int(row.count),
            "avg_execution_time": round(float(row.avg_time or 0), 4),
            "avg_confidence": round(float(row.avg_conf or 0), 4),
            "llm_calls": int(row.llm_calls or 0),
        }
        for row in breakdown_result
    ]

    return {
        "summary": {
            "total_executions": total_count,
            "running": running_count,
            "completed": completed_count,
            "failed": failed_count,
            "total_execution_time": round(total_exec_time, 4),
            "total_llm_calls": total_llm_calls,
            "max_memory_mb": round(max_memory, 4),
            "avg_confidence": avg_confidence,
        },
        "workers": engine.list_workers(),
        "recent_executions": recent,
        "recent_logs": logs,
        "recent_decisions": decisions,
        "worker_breakdown": worker_breakdown,
        "live_connections": event_bus.connected_clients,
    }


@router.get("/running")
async def running_workers(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Workers currently running."""
    stmt = select(WorkerExecution).where(
        WorkerExecution.status == "running"
    ).order_by(desc(WorkerExecution.started_at))
    result = await db.execute(stmt)
    records = result.scalars().all()
    return {"running": [r.to_dict() for r in records], "count": len(records)}


@router.get("/completed")
async def completed_workers(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recently completed workers."""
    stmt = (
        select(WorkerExecution)
        .where(WorkerExecution.status == "success")
        .order_by(desc(WorkerExecution.completed_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return {"completed": [r.to_dict() for r in records], "count": len(records)}


@router.get("/failed")
async def failed_workers(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recently failed workers."""
    stmt = (
        select(WorkerExecution)
        .where(WorkerExecution.status == "failed")
        .order_by(desc(WorkerExecution.completed_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return {"failed": [r.to_dict() for r in records], "count": len(records)}


@router.get("/logs")
async def execution_logs(
    execution_id: Optional[str] = Query(default=None),
    limit: int = 200,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """TASK-005: Get logs (event log entries)."""
    stmt = select(WorkerEventLog).order_by(desc(WorkerEventLog.timestamp))
    if execution_id:
        stmt = stmt.where(WorkerEventLog.execution_id == execution_id)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return {"logs": [r.to_dict() for r in records], "count": len(records)}


@router.get("/metrics")
async def metrics_summary(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """TASK-005: Aggregate metrics for charts."""
    exec_times = await db.execute(
        select(WorkerExecution.execution_time).where(
            WorkerExecution.execution_time > 0
        )
    )
    times = [float(r) for r in exec_times.scalars().all()]

    confs = await db.execute(
        select(WorkerExecution.confidence).where(
            WorkerExecution.confidence > 0
        )
    )
    confidences = [float(c) for c in confs.scalars().all()]

    llm = await db.execute(
        select(WorkerExecution.llm_calls).where(
            WorkerExecution.llm_calls > 0
        )
    )
    llm_counts = [int(c) for c in llm.scalars().all()]

    mem = await db.execute(
        select(WorkerExecution.memory_usage_mb).where(
            WorkerExecution.memory_usage_mb.isnot(None)
        )
    )
    memory_vals = [float(m) for m in mem.scalars().all()]

    return {
        "execution_time": {
            "values": times,
            "avg": round(sum(times) / len(times), 4) if times else 0,
            "max": round(max(times), 4) if times else 0,
        },
        "confidence": {
            "values": confidences,
            "avg": round(sum(confidences) / len(confidences), 4) if confidences else 0,
        },
        "llm_calls": {
            "values": llm_counts,
            "total": sum(llm_counts),
        },
        "memory_usage": {
            "values": memory_vals,
            "avg": round(sum(memory_vals) / len(memory_vals), 4) if memory_vals else 0,
            "max": round(max(memory_vals), 4) if memory_vals else 0,
        },
    }
