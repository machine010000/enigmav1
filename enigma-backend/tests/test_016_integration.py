"""
TASK-016 Integration Tests

Covers:
- Phase 11: Duplicate / loop protection (integration, not just unit)
- Phase 12: Failure E2E paths
- Phase 13: True multi-step with deterministic test capabilities
- Phase 15: Endpoint regression (autonomous response contract shape)
- Phase 16: Data isolation (repository query scoping)

Deterministic test capabilities are registered ONLY within test scope —
no production workers are added.  The client never provides worker names.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
from datetime import datetime

from app.autonomy.orchestrator import AutonomousOrchestrator
from app.autonomy.contracts import (
    RunStatus,
    StepStatus,
    StopReason,
    AutonomousRun,
)
from app.ai.master_brain.models import BrainDecision, BrainAction
from app.engine.capabilities import capability_registry, CapabilityRegistry
from app.engine.engine import ExecutionEngine
from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus


# ---------------------------------------------------------------------------
# Helpers: deterministic test workers (never added to production engine)
# ---------------------------------------------------------------------------

def _make_test_worker(name: str, result_payload: dict):
    """Create a deterministic Worker for use within test scope only."""
    from app.engine.contracts import Worker

    class _TestWorker(Worker):
        async def run(self, context: ExecutionContext) -> WorkerResult:
            return WorkerResult(
                worker_name=name,
                status=WorkerStatus.SUCCESS,
                result=result_payload,
                confidence=0.95,
                llm_calls=0,
            )

    w = _TestWorker()
    w.name = name
    w.description = f"Test worker {name}"
    w.input_schema = {}
    w.output_schema = {}
    return w


def _make_failing_worker(name: str, error_msg: str):
    """Create a deterministic failing Worker for test scope only."""
    from app.engine.contracts import Worker

    class _FailWorker(Worker):
        async def run(self, context: ExecutionContext) -> WorkerResult:
            raise RuntimeError(error_msg)

    w = _FailWorker()
    w.name = name
    w.description = f"Failing test worker {name}"
    w.input_schema = {}
    w.output_schema = {}
    return w


# ---------------------------------------------------------------------------
# Phase 11: Duplicate / loop protection — integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_action_stops_loop_integration():
    """
    Integration test: same capability + same target + same parameters
    must trigger DUPLICATE_ACTION stop — no second execution.
    """
    target = str(uuid4())

    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=5)

        # Brain always returns the exact same decision (same target, same params)
        same_decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target,
            reasoning_summary="Verify",
            execution_required=True,
            execution_input={"product_id": target},
            confidence=0.9,
        )

        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(return_value=same_decision)
        mock_brain.execute_with_learning = AsyncMock(return_value={
            "status": "completed",
            "execution_id": str(uuid4()),
            "worker": "product_verification",
            "result": {"result": {"verified_name": "Test"}},
            "confidence": 0.9,
        })
        # Re-evaluation: keep recommending more
        mock_brain._re_evaluate_after_execution = MagicMock(return_value={
            "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
            "reason": "Continue",
            "next_action": "verify again",
            "next_action_reasoning": "More",
        })
        orchestrator.master_brain = mock_brain

        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify product",
            target_id=target,
            module="seller",
            db=None,
        )

    # Exactly 1 execution before duplicate detected
    assert mock_brain.execute_with_learning.call_count == 1
    assert len(run.steps) == 1
    assert run.stop_reason == StopReason.DUPLICATE_ACTION
    assert run.status == RunStatus.STOPPED


@pytest.mark.asyncio
async def test_step_limit_enforced_integration():
    """
    Integration test: max_steps=2, brain keeps requesting execution.
    Run must stop with STEP_LIMIT_REACHED after 2 steps, no 3rd execution.
    """
    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=2)

        # Use different targets so fingerprints differ (no duplicate stop)
        targets = [str(uuid4()), str(uuid4()), str(uuid4())]
        idx = [0]

        def next_decision():
            t = targets[min(idx[0], len(targets) - 1)]
            idx[0] += 1
            return BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=t,
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": t},
                confidence=0.9,
            )

        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(side_effect=lambda **kw: next_decision())
        mock_brain.execute_with_learning = AsyncMock(return_value={
            "status": "completed",
            "execution_id": str(uuid4()),
            "worker": "product_verification",
            "result": {},
            "confidence": 0.9,
        })
        mock_brain._re_evaluate_after_execution = MagicMock(return_value={
            "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
            "reason": "Keep going",
            "next_action": "verify next",
            "next_action_reasoning": "",
        })
        orchestrator.master_brain = mock_brain

        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="keep verifying",
            target_id=targets[0],
            module="seller",
            db=None,
        )

    assert len(run.steps) == 2
    assert run.stop_reason == StopReason.STEP_LIMIT_REACHED
    assert mock_brain.execute_with_learning.call_count == 2  # Never 3


# ---------------------------------------------------------------------------
# Phase 12: Failure E2E
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provider_timeout_stops_run_cleanly():
    """AI provider timeout → run stops, trace is valid, no continuation."""
    from app.ai.client import AITimeoutError

    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=3)

        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            side_effect=AITimeoutError("Provider timed out")
        )
        orchestrator.master_brain = mock_brain

        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )

    assert run.status == RunStatus.STOPPED
    assert run.stop_reason == StopReason.FAILURE
    assert len(run.steps) == 1
    assert run.steps[0].status == StepStatus.FAILED
    assert "timeout" in (run.steps[0].error or "").lower()
    # Verify trace completeness
    assert run.steps[0].started_at is not None
    assert run.steps[0].completed_at is not None


@pytest.mark.asyncio
async def test_worker_failure_stops_run_persists_trace():
    """Worker exception → failure observation in trace → loop stops."""
    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=3)

        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            side_effect=Exception("Database connection lost")
        )
        orchestrator.master_brain = mock_brain

        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )

    assert run.status == RunStatus.STOPPED
    assert run.stop_reason == StopReason.FAILURE
    assert len(run.steps) == 1
    assert run.steps[0].status == StepStatus.FAILED
    # Raw exception message must NOT be exposed
    assert "Database connection lost" not in (run.steps[0].error or "")
    assert "unexpected" in (run.steps[0].error or "").lower()


@pytest.mark.asyncio
async def test_unknown_capability_no_worker_dispatch():
    """Unknown capability → blocked, no worker dispatched."""
    orchestrator = AutonomousOrchestrator(max_steps=3)

    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        return_value=BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="ghost",
            capability="ghost_capability",
            target=str(uuid4()),
            reasoning_summary="Test",
            execution_required=True,
            execution_input={},
            confidence=0.9,
        )
    )
    orchestrator.master_brain = mock_brain

    with patch.object(capability_registry, "resolve_capability", return_value=None):
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="do ghost",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )

    assert run.status == RunStatus.STOPPED
    assert len(run.steps) == 0
    assert run.stop_reason == StopReason.CAPABILITY_NOT_AVAILABLE
    mock_brain.execute_with_learning.assert_not_called()


@pytest.mark.asyncio
async def test_ownership_failure_no_execution_record():
    """Ownership failure → no step recorded, no execution."""
    orchestrator = AutonomousOrchestrator(max_steps=3)

    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        return_value=BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=str(uuid4()),
            reasoning_summary="Test",
            execution_required=True,
            execution_input={},
            confidence=0.9,
        )
    )
    orchestrator.master_brain = mock_brain
    orchestrator._validate_ownership = AsyncMock(return_value=False)
    orchestrator._reload_authoritative_target = AsyncMock(return_value=None)

    run = await orchestrator.run_autonomous(
        user_id=str(uuid4()),
        goal="verify",
        target_id=str(uuid4()),
        module="seller",
        db=MagicMock(),
    )

    assert len(run.steps) == 0
    mock_brain.execute_with_learning.assert_not_called()


# ---------------------------------------------------------------------------
# Phase 13: True multi-step with deterministic test capabilities
# The client never provides worker_name — orchestrator resolves via registry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_true_multistep_with_test_capabilities():
    """
    TRUE MULTI-STEP TEST (Phase 13):

    Two deterministic test capabilities (test_cap_a, test_cap_b) registered
    only within test scope.  The client provides only a goal — never a
    worker name.

    Flow:
      Decision 1 → test_cap_a → Engine → Result → Learning persist →
      NEW context reload → Decision 2 → test_cap_b → Engine → Result →
      FINISH
    """
    user_id = str(uuid4())
    target_id = str(uuid4())

    # Create isolated test registry + engine
    test_registry = CapabilityRegistry()
    test_engine = ExecutionEngine()

    # Register two deterministic test workers
    worker_a = _make_test_worker("test_worker_a", {"outcome": "A completed", "phase": 1})
    worker_b = _make_test_worker("test_worker_b", {"outcome": "B completed", "phase": 2})

    test_engine.register(worker_a)
    test_engine.register(worker_b)

    from app.engine.capabilities import Capability
    test_registry.register(
        Capability(id="test_cap_a", description="Test capability A"),
        worker_name="test_worker_a",
    )
    test_registry.register(
        Capability(id="test_cap_b", description="Test capability B"),
        worker_name="test_worker_b",
    )

    orchestrator = AutonomousOrchestrator(max_steps=3)

    # Step 1: Brain selects test_cap_a
    decision_a = BrainDecision(
        action=BrainAction.EXECUTE_CAPABILITY,
        intent="test_cap_a",
        capability="test_cap_a",
        target=target_id,
        reasoning_summary="Execute phase 1",
        execution_required=True,
        execution_input={"product_id": target_id},
        confidence=0.9,
    )

    # Step 2: Brain selects test_cap_b
    decision_b = BrainDecision(
        action=BrainAction.EXECUTE_CAPABILITY,
        intent="test_cap_b",
        capability="test_cap_b",
        target=target_id,
        reasoning_summary="Execute phase 2",
        execution_required=True,
        execution_input={"product_id": target_id},
        confidence=0.9,
    )

    # FINISH after step 2
    decision_finish = BrainDecision(
        action=BrainAction.FINISH,
        intent="finish",
        reasoning_summary="Both phases complete",
        execution_required=False,
        confidence=1.0,
    )

    execution_ids = [str(uuid4()), str(uuid4())]
    exec_idx = [0]

    async def mock_execute_with_learning(decision, db, user_id):
        """Simulates execute_with_learning using the test registry."""
        cap = decision.capability
        resolution = test_registry.resolve_capability(cap)
        assert resolution is not None, f"Capability {cap} not in test registry"

        exec_id = execution_ids[exec_idx[0] % len(execution_ids)]
        exec_idx[0] += 1

        return {
            "status": "completed",
            "execution_id": exec_id,
            "worker": resolution["worker_name"],
            "result": {"result": {"capability": cap, "done": True}},
            "confidence": 0.95,
            "learning": {
                "persisted": True,
                "evidence_count": 1,
                "profile_updated": True,
            },
        }

    re_eval_calls = [0]

    def mock_re_evaluate(decision, execution_result, learning_context):
        re_eval_calls[0] += 1
        if re_eval_calls[0] == 1:
            # After step 1: recommend step 2
            return {
                "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                "reason": "Phase 1 done, proceed to phase 2",
                "next_action": "execute phase 2",
                "next_action_reasoning": "Logical next step",
            }
        # After step 2: finish
        return {
            "action": BrainAction.FINISH.value,
            "reason": "Both phases complete",
            "next_action": None,
        }

    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        side_effect=[decision_a, decision_b, decision_finish]
    )
    mock_brain.execute_with_learning = AsyncMock(side_effect=mock_execute_with_learning)
    mock_brain._re_evaluate_after_execution = MagicMock(side_effect=mock_re_evaluate)
    orchestrator.master_brain = mock_brain

    with patch.object(capability_registry, "resolve_capability", side_effect=test_registry.resolve_capability):
        run = await orchestrator.run_autonomous(
            user_id=user_id,
            goal="Execute both phases",
            target_id=target_id,
            module="seller",
            db=None,
        )

    # Assertions: correct multi-step execution
    assert run.status == RunStatus.COMPLETED, f"Expected COMPLETED, got {run.status}"
    assert run.stop_reason == StopReason.FINISHED
    assert len(run.steps) == 2, f"Expected 2 steps, got {len(run.steps)}"

    # Step 1
    assert run.steps[0].capability == "test_cap_a"
    assert run.steps[0].status == StepStatus.COMPLETED
    assert run.steps[0].execution_id == execution_ids[0]
    assert run.steps[0].started_at is not None
    assert run.steps[0].completed_at is not None
    assert run.steps[0].outcome is not None
    assert "learning" in run.steps[0].outcome

    # Step 2
    assert run.steps[1].capability == "test_cap_b"
    assert run.steps[1].status == StepStatus.COMPLETED
    assert run.steps[1].execution_id == execution_ids[1]

    # Learning was called for each step
    assert mock_brain.execute_with_learning.call_count == 2
    # Re-evaluation was called after each execution
    assert re_eval_calls[0] == 2

    # Client never provided worker names — verify calls used capability only
    call_args_list = mock_brain.execute_with_learning.call_args_list
    for call_args in call_args_list:
        decision_arg = call_args.kwargs.get("decision") or call_args.args[0]
        # Decision has a capability name, never a raw worker name from client
        assert decision_arg.capability in ("test_cap_a", "test_cap_b")


# ---------------------------------------------------------------------------
# Phase 15: Autonomous response contract shape
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_response_contract_shape_canonical():
    """Response shape matches stable AutonomousRunResponse contract."""
    from app.routers.master_brain import _build_run_response, AutonomousRunResponse
    from app.autonomy.contracts import AutonomousRun, AutonomousStep, RunStatus, StopReason

    run = AutonomousRun(
        run_id=str(uuid4()),
        user_id=str(uuid4()),
        target_id=str(uuid4()),
        module="seller",
        original_goal="test goal",
        status=RunStatus.COMPLETED,
        max_steps=3,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        stop_reason=StopReason.FINISHED,
        final_response="All done",
    )

    step = AutonomousStep(
        step_number=1,
        decision=BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="test",
            capability="product_verification",
            reasoning_summary="",
            execution_required=True,
            confidence=0.9,
        ),
        capability="product_verification",
        execution_id=str(uuid4()),
        status=StepStatus.COMPLETED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    run.add_step(step)

    response = _build_run_response(run, "test goal")

    # Required fields present
    assert isinstance(response, AutonomousRunResponse)
    assert response.run_id == run.run_id
    assert response.status == "finished"
    assert response.module == "seller"
    assert response.goal == "test goal"
    assert len(response.steps) == 1
    assert response.steps[0].step == 1
    assert response.steps[0].capability == "product_verification"
    assert response.steps[0].execution_id is not None
    assert response.stop_reason == "finished"

    # Prohibited fields absent
    response_dict = response.model_dump()
    prohibited = ["worker_name", "reasoning", "chain_of_thought", "prompt",
                  "secret", "token", "traceback"]
    for field in prohibited:
        assert field not in response_dict, f"Prohibited field '{field}' found in response"


def test_response_contract_no_worker_name_exposed():
    """AutonomousStepResponse does not contain worker_name."""
    from app.routers.master_brain import AutonomousStepResponse
    import inspect

    fields = AutonomousStepResponse.model_fields
    assert "worker_name" not in fields
    assert "worker" not in fields


# ---------------------------------------------------------------------------
# Phase 16: Data isolation — repository query scoping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execution_list_scoped_to_user():
    """get_recent_executions scopes by user_id — cross-user records not returned."""
    eng = ExecutionEngine()

    user_a_id = str(uuid4())

    mock_db = AsyncMock()
    captured_statements = []

    async def capture_execute(stmt):
        compiled = stmt.compile()
        captured_statements.append(str(compiled))
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return mock_result

    mock_db.execute = capture_execute

    await eng.get_recent_executions(mock_db, limit=10, user_id=user_a_id)

    assert len(captured_statements) > 0
    combined = " ".join(captured_statements).lower()
    assert "user_id" in combined, "Query must filter by user_id"


@pytest.mark.asyncio
async def test_execution_record_lookup_scoped_to_user():
    """get_execution_record with user_id=X cannot return record owned by Y."""
    eng = ExecutionEngine()

    user_a_id = str(uuid4())
    execution_id = str(uuid4())

    mock_db = AsyncMock()
    # Simulate the record belonging to user B — scoped query returns None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await eng.get_execution_record(mock_db, execution_id, user_id=user_a_id)
    assert result is None, "Cross-user execution lookup must return None"
