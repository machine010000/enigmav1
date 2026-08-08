"""
ENIGMA Engine Smoke Test — validates Sprint 1 tasks:

  TASK-001  Execution Engine  : register / execute / status / result / time
  TASK-002  Worker Contract   : Worker.run(context) -> WorkerResult
  TASK-003  Execution Context : User, Product, Memory, Knowledge, Settings, History
  TASK-006  Live Console Events: worker emits events, EventBus captures them

Run from the repo root:
    python test_engine.py
"""
import asyncio
import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "enigma-backend"))

from app.engine.contracts import (
    ExecutionContext, Worker, WorkerResult, WorkerStatus,
    WorkerEvent, EvidenceItem,
)
from app.engine.engine import engine, ExecutionEngine
from app.engine.events import event_bus


# ---------------------------------------------------------------------------
# Dummy worker for engine-level testing (does NOT need an LLM API key)
# ---------------------------------------------------------------------------

class EchoWorker(Worker):
    name = "echo_test"
    description = "A simple worker that echoes back the input with evidence."
    input_schema = ["message"]
    output_schema = ["echoed", "reversed"]

    async def run(self, context: ExecutionContext) -> WorkerResult:
        # Emit a live event (TASK-006)
        if context.emit:
            await context.emit(WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Echo worker started processing",
                data={"input": context.product.get("name", "unknown")},
                execution_id=context.execution_id,
            ))

        message = context.product.get("name", "hello")
        echoed = f"echo: {message}"

        return WorkerResult(
            worker_name=self.name,
            status=WorkerStatus.SUCCESS,
            result={"echoed": echoed, "original": message, "reversed": message[::-1]},
            evidence=[
                EvidenceItem(
                    worker=self.name,
                    field="echoed",
                    value=echoed,
                    source="context.input",
                    confidence=1.0,
                ).to_dict()
            ],
            confidence=0.99,
            llm_calls=0,
        )


class FailingWorker(Worker):
    name = "failing_test"
    description = "A worker that always fails, to test error handling."
    input_schema = []
    output_schema = []

    async def run(self, context: ExecutionContext) -> WorkerResult:
        raise RuntimeError("Intentional failure for testing")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_register_and_list():
    """TASK-001: Register Worker"""
    print("\n[TASK-001] Register Worker")
    engine._workers.clear()  # clean slate
    echo = EchoWorker()
    engine.register(echo)

    workers = engine.list_workers()
    assert len(workers) == 1, f"Expected 1 worker, got {len(workers)}"
    assert workers[0]["name"] == "echo_test"
    print("    PASS — worker registered & listed")


async def test_execute_returns_result_time_status():
    """TASK-001: Execute Worker, Return Status, Result, Execution Time"""
    print("\n[TASK-001] Execute Worker — status / result / time")
    ctx = ExecutionContext(
        user={"id": "test-user", "name": "Test User"},
        product={"name": "Black T-Shirt"},
        execution_id="exec-001",
    )

    result = await engine.execute("echo_test", ctx, save=False)

    assert result.status == WorkerStatus.SUCCESS, f"Expected SUCCESS, got {result.status}"
    assert result.execution_time > 0, f"Expected execution_time > 0, got {result.execution_time}"
    assert result.result["echoed"] == "echo: Black T-Shirt"
    assert result.confidence == 0.99
    assert result.llm_calls == 0
    assert result.error is None
    print(f"    PASS — status={result.status.value}, "
          f"time={result.execution_time:.4f}s, "
          f"result={result.result}")
    print(f"    PASS — evidence count={len(result.evidence)}")


async def test_execution_context_fields():
    """TASK-003: Execution Context has all required fields"""
    print("\n[TASK-003] Execution Context fields")
    ctx = ExecutionContext(
        user={"id": "u1", "name": "Alice"},
        product={"name": "Widget", "category": "Tech"},
        memory={"prev_result": 42},
        knowledge=[{"category": "pricing", "key": "rule1", "value": "premium"}],
        settings={"confidence_threshold": 0.7},
        history=[{"worker_name": "prev", "status": "success"}],
        execution_id="ctx-test-001",
    )

    assert ctx.user["name"] == "Alice"
    assert ctx.product["name"] == "Widget"
    assert ctx.knowledge[0]["key"] == "rule1"
    assert ctx.settings["confidence_threshold"] == 0.7
    assert len(ctx.history) == 1
    assert ctx.recall("prev_result") == 42

    # test remember + history
    ctx.remember("new_val", True)
    assert ctx.recall("new_val") is True

    result = WorkerResult(
        worker_name="test",
        status=WorkerStatus.SUCCESS,
        confidence=0.8,
        result={"x": 1},
    )
    ctx.add_history(result)
    assert len(ctx.history) == 2
    print("    PASS — all context fields present & working")


async def test_worker_failure_handling():
    """TASK-001: failed workers get FAILED status + error message"""
    print("\n[TASK-001] Worker failure handling")
    engine._workers.clear()
    engine.register(FailingWorker())

    ctx = ExecutionContext(execution_id="exec-fail-001")
    result = await engine.execute("failing_test", ctx, save=False)

    assert result.status == WorkerStatus.FAILED
    assert result.error is not None
    assert "Intentional failure" in result.error
    assert result.execution_time > 0
    print(f"    PASS — status={result.status.value}, error={result.error[:50]}...")


async def test_live_console_events():
    """TASK-006: workers emit events captured by EventBus"""
    print("\n[TASK-006] Live Console events")
    engine._workers.clear()
    event_bus.clear()
    engine.register(EchoWorker())

    ctx = ExecutionContext(
        product={"name": "Live T-Shirt"},
        execution_id="exec-events-001",
    )

    await engine.execute("echo_test", ctx, save=False)

    # EventBus should have captured events (worker_registered + execution_started + progress + finished)
    history = event_bus.get_history(limit=20)
    event_types = [e["type"] for e in history]
    assert "worker_registered" in event_types, f"worker_registered not in {event_types}"
    assert "execution_started" in event_types
    assert "progress" in event_types
    assert "finished" in event_types
    print(f"    PASS — {len(history)} events captured: {event_types}")


async def test_worker_abc_contract():
    """TASK-002: Worker ABC enforces run() implementation"""
    print("\n[TASK-002] Worker Contract (ABC)")

    # Concrete worker is fine
    w = EchoWorker()
    assert hasattr(w, "run")

    # Abstract class cannot be instantiated directly
    try:
        Worker()  # type: ignore[abstract]
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
    print("    PASS — Worker is abstract; subclasses must implement run()")


async def test_worker_result_has_all_fields():
    """TASK-001/002: WorkerResult has status, result, time, confidence, evidence"""
    print("\n[TASK-001/002] WorkerResult fields")
    result = WorkerResult(
        worker_name="test",
        status=WorkerStatus.SUCCESS,
        result={"a": 1},
        evidence=[{"worker": "test", "value": 1}],
        confidence=0.9,
        execution_time=0.5,
        llm_calls=2,
        memory_usage_mb=12.3,
    )
    d = result.to_dict()
    for key in ["worker_name", "status", "result", "evidence",
                "confidence", "execution_time", "llm_calls",
                "memory_usage_mb", "error", "started_at", "completed_at"]:
        assert key in d, f"Missing key: {key}"
    print(f"    PASS -- WorkerResult.to_dict() has all required keys")


async def test_orchestrate_pipeline():
    """TASK-004: Execution Pipeline — run multiple workers in sequence"""
    print("\n[TASK-004] Execution Pipeline (orchestrate)")
    engine._workers.clear()
    event_bus.clear()
    engine.register(EchoWorker())

    plan = [
        {"step": 1, "worker": "echo_test", "input": {"name": "Product A"}},
        {"step": 2, "worker": "echo_test", "input": {"name": "Product B"}},
    ]
    ctx = ExecutionContext(execution_id="pipeline-test-001")
    pipeline_result = await engine.orchestrate(plan, ctx, save=False)

    assert "execution_id" in pipeline_result
    assert len(pipeline_result["results"]) == 2
    assert all(r["status"] == "success" for r in pipeline_result["results"])
    print(f"    PASS -- pipeline ran {len(plan)} steps, "
          f"memory keys: {list(pipeline_result['context_memory'].keys())}")


async def test_product_verification_worker_registered():
    """Sprint 2: ProductVerificationWorker is registered and executable."""
    print("\n[Sprint 2] ProductVerificationWorker registration")
    from app.workers.product_verification import product_verification_worker
    engine._workers.clear()
    engine.register(product_verification_worker)

    workers = engine.list_workers()
    names = [w["name"] for w in workers]
    assert "product_verification" in names
    assert product_verification_worker.input_schema == ["title", "name", "images", "description", "category"]
    assert "verified_name" in product_verification_worker.output_schema
    print(f"    PASS -- {product_verification_worker.name} registered")
    print(f"    PASS -- input_schema={product_verification_worker.input_schema}")
    print(f"    PASS -- output_schema={product_verification_worker.output_schema}")


async def run_all():
    await test_register_and_list()
    await test_execute_returns_result_time_status()
    await test_execution_context_fields()
    await test_worker_failure_handling()
    await test_live_console_events()
    await test_worker_abc_contract()
    await test_worker_result_has_all_fields()
    await test_orchestrate_pipeline()
    await test_product_verification_worker_registered()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED  (Sprint 1 + Sprint 2 foundation)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all())
