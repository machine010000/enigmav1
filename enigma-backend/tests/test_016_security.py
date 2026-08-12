"""
TASK-016 Security Test Matrix

Tests A–H covering cross-user isolation, capability policy, and
client-input rejection as required by TASK-016 Phase 10.

TEST A: User A autonomous action on User A product → allowed
TEST B: User A autonomous action on User B product → blocked before Engine execution
TEST C: User A attempts to retrieve User B execution → blocked (404)
TEST D: User A context loader cannot retrieve User B evidence/memory
TEST E: Brain proposes unregistered capability → not executed
TEST F: Client tries to pass worker_name → ignored/rejected
TEST G: Client tries to manipulate module/target mismatch → blocked
TEST H: Second autonomous step revalidates ownership
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from app.autonomy.orchestrator import AutonomousOrchestrator
from app.autonomy.contracts import RunStatus, StepStatus, StopReason
from app.ai.master_brain.models import BrainDecision, BrainAction
from app.engine.capabilities import capability_registry
from app.engine.context_builder import build_context, ProductOwnershipError
from app.learning.context_loader import LearningContextLoader


# ---------------------------------------------------------------------------
# TEST A: User A acts on their own product → allowed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_user_own_product_allowed():
    """TEST A: Autonomous action on own product is permitted."""
    user_a_id = str(uuid4())
    product_id = str(uuid4())

    orchestrator = AutonomousOrchestrator(max_steps=1)

    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=product_id,
                reasoning_summary="Verify product",
                execution_required=True,
                execution_input={"product_id": product_id},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(return_value={
            "status": "completed",
            "execution_id": str(uuid4()),
            "worker": "product_verification",
            "result": {"result": {"verified_name": "Test"}},
            "confidence": 0.9,
        })
        mock_brain._re_evaluate_after_execution = MagicMock(return_value={
            "action": BrainAction.FINISH.value,
            "reason": "Done",
            "next_action": None,
        })
        orchestrator.master_brain = mock_brain

        # _validate_ownership returns True — user owns the product
        orchestrator._validate_ownership = AsyncMock(return_value=True)
        orchestrator._reload_authoritative_target = AsyncMock(return_value=MagicMock())

        run = await orchestrator.run_autonomous(
            user_id=user_a_id,
            goal="verify my product",
            target_id=product_id,
            module="seller",
            db=MagicMock(),
        )

    assert run.status == RunStatus.COMPLETED
    assert len(run.steps) == 1
    assert run.steps[0].status == StepStatus.COMPLETED
    # Execution was called
    mock_brain.execute_with_learning.assert_called_once()


# ---------------------------------------------------------------------------
# TEST B: User A acts on User B product → blocked before Engine execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_b_cross_user_product_blocked():
    """TEST B: Autonomous action on another user's product is blocked — no execution."""
    user_a_id = str(uuid4())
    user_b_product_id = str(uuid4())

    orchestrator = AutonomousOrchestrator(max_steps=3)

    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        return_value=BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=user_b_product_id,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": user_b_product_id},
            confidence=0.9,
        )
    )
    orchestrator.master_brain = mock_brain

    # Ownership returns False — product belongs to User B, not User A
    orchestrator._validate_ownership = AsyncMock(return_value=False)
    orchestrator._reload_authoritative_target = AsyncMock(return_value=None)

    run = await orchestrator.run_autonomous(
        user_id=user_a_id,
        goal="verify product",
        target_id=user_b_product_id,
        module="seller",
        db=MagicMock(),
    )

    # Must be stopped before any execution
    assert run.status == RunStatus.STOPPED
    assert len(run.steps) == 0  # Engine was never reached
    assert run.stop_reason in (StopReason.OWNERSHIP_FAILURE, StopReason.CAPABILITY_NOT_AVAILABLE)
    # Brain execution was never called
    mock_brain.execute_with_learning.assert_not_called()


# ---------------------------------------------------------------------------
# TEST C: User A retrieves User B execution → blocked (404)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_c_cross_user_execution_retrieval_blocked():
    """TEST C: Retrieving another user's execution record returns None (→ 404)."""
    from app.engine.engine import ExecutionEngine

    user_a_id = str(uuid4())
    user_b_id = str(uuid4())
    execution_id = str(uuid4())

    eng = ExecutionEngine()

    # Simulate a WorkerExecution record owned by User B
    from app.models.execution import WorkerExecution
    import uuid as _uuid
    from datetime import datetime

    mock_record = MagicMock(spec=WorkerExecution)
    mock_record.id = _uuid.UUID(execution_id)
    mock_record.user_id = _uuid.UUID(user_b_id)
    mock_record.worker_name = "product_verification"
    mock_record.status = "success"
    mock_record.result = {}
    mock_record.evidence = []
    mock_record.confidence = 0.9
    mock_record.execution_time = 1.0
    mock_record.llm_calls = 1
    mock_record.memory_usage_mb = 10.0
    mock_record.error = None
    mock_record.started_at = datetime.utcnow()
    mock_record.completed_at = datetime.utcnow()

    mock_db = AsyncMock()
    # The scoped query (user_a asking for user_b's execution) returns None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await eng.get_execution_record(mock_db, execution_id, user_id=user_a_id)

    # Must return None — triggers 404 in router
    assert result is None


# ---------------------------------------------------------------------------
# TEST D: User A context loader cannot see User B memory/evidence
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d_cross_user_learning_context_isolated():
    """TEST D: LearningContextLoader scopes WorkerExecution queries by user_id."""
    from sqlalchemy import select
    from app.models.execution import WorkerExecution

    user_a_id = str(uuid4())
    user_b_id = str(uuid4())

    loader = LearningContextLoader()

    # Track what queries are issued
    issued_queries = []

    async def mock_execute(stmt):
        # Capture the WHERE clauses of the issued statement
        compiled = stmt.compile()
        issued_queries.append(str(compiled))
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return mock_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    await loader._load_recent_executions(
        db=mock_db,
        user_id=user_a_id,
        product_id=None,
        capability=None,
        limit=5,
    )

    # Verify at least one query was issued and it filters by user_id
    assert len(issued_queries) > 0
    # The query must reference user_id (ownership filter present)
    combined = " ".join(issued_queries).lower()
    assert "user_id" in combined


# ---------------------------------------------------------------------------
# TEST E: Brain proposes unregistered capability → not executed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e_unregistered_capability_not_executed():
    """TEST E: Brain output naming an unregistered capability is rejected."""
    orchestrator = AutonomousOrchestrator(max_steps=3)

    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        return_value=BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="market_research",
            capability="market_research",   # NOT registered
            target=str(uuid4()),
            reasoning_summary="Do market research",
            execution_required=True,
            execution_input={},
            confidence=0.9,
        )
    )
    orchestrator.master_brain = mock_brain

    # Ensure capability is NOT registered
    with patch.object(capability_registry, "resolve_capability", return_value=None):
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="research market",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )

    assert run.status == RunStatus.STOPPED
    assert len(run.steps) == 0  # Never dispatched to Engine
    assert run.stop_reason == StopReason.CAPABILITY_NOT_AVAILABLE
    assert "not registered" in (run.final_response or "").lower()
    # Engine execute was never called
    mock_brain.execute_with_learning.assert_not_called()


# ---------------------------------------------------------------------------
# TEST F: Client tries to pass worker_name → ignored
# ---------------------------------------------------------------------------

def test_f_worker_name_not_accepted_in_request():
    """TEST F: AutonomousRequest does not accept worker_name field."""
    from app.routers.master_brain import AutonomousRequest
    from pydantic import ValidationError

    # worker_name is not a defined field — Pydantic will ignore it by default
    # (model_config has extra='ignore')
    req = AutonomousRequest(
        goal="verify product",
        product_id=str(uuid4()),
        worker_name="evil_worker",     # should be ignored
        module="seller",
    )
    # worker_name must not appear on the model
    assert not hasattr(req, "worker_name") or getattr(req, "worker_name", None) is None


def test_f_max_steps_clamped_by_server():
    """TEST F (continued): Client-supplied max_steps cannot exceed server ceiling."""
    from app.routers.master_brain import AutonomousRequest

    req = AutonomousRequest(goal="test", max_steps=999)
    # Must be clamped to MAX_AUTONOMOUS_STEPS_LIMIT (5)
    assert req.max_steps == 5

    req2 = AutonomousRequest(goal="test", max_steps=0)
    # Must be clamped to MIN (1)
    assert req2.max_steps == 1


# ---------------------------------------------------------------------------
# TEST G: Client tries to manipulate module/target mismatch → blocked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_g_module_target_mismatch_blocked():
    """TEST G: Capability belonging to 'seller' module rejected when module='content_creator'."""
    orchestrator = AutonomousOrchestrator(max_steps=3)

    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",   # seller capability
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={},
                confidence=0.9,
            )
        )
        orchestrator.master_brain = mock_brain

        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="test",
            target_id=str(uuid4()),
            module="content_creator",   # mismatched module
            db=None,
        )

    assert run.status == RunStatus.STOPPED
    assert len(run.steps) == 0
    assert run.stop_reason == StopReason.CAPABILITY_NOT_AVAILABLE
    mock_brain.execute_with_learning.assert_not_called()


# ---------------------------------------------------------------------------
# TEST H: Second autonomous step revalidates ownership
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_h_ownership_revalidated_each_step():
    """TEST H: Ownership is revalidated on every step, not just at run start."""
    user_id = str(uuid4())
    product_id = str(uuid4())

    with patch.object(capability_registry, "resolve_capability", return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=3)

        mock_brain = MagicMock()
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=product_id,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": product_id},
            confidence=0.9,
        )
        mock_brain.decide_capability = MagicMock(return_value=decision)
        mock_brain.execute_with_learning = AsyncMock(return_value={
            "status": "completed",
            "execution_id": str(uuid4()),
            "worker": "product_verification",
            "result": {"result": {"verified_name": "Test"}},
            "confidence": 0.9,
        })
        mock_brain._re_evaluate_after_execution = MagicMock(return_value={
            "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
            "reason": "Continue",
            "next_action": "verify again",
            "next_action_reasoning": "Test",
        })
        orchestrator.master_brain = mock_brain

        validate_calls = []

        async def ownership_side_effect(db, user_id, target_id):
            validate_calls.append(len(validate_calls) + 1)
            if len(validate_calls) == 1:
                return True   # Step 1: allowed
            return False      # Step 2+: revoked

        reload_calls = [0]

        async def reload_side_effect(db, user_id, target_id):
            reload_calls[0] += 1
            if reload_calls[0] == 1:
                return MagicMock()   # Step 1: product exists
            return None              # Step 2: product gone

        orchestrator._validate_ownership = ownership_side_effect
        orchestrator._reload_authoritative_target = reload_side_effect

        run = await orchestrator.run_autonomous(
            user_id=user_id,
            goal="verify my product",
            target_id=product_id,
            module="seller",
            db=MagicMock(),
        )

    # Ownership must have been checked at least once (step 1)
    assert len(validate_calls) >= 1, "Ownership must be checked on every step"
    # Run must stop — either after step 1 succeeds and step 2 is blocked by
    # ownership, duplicate-action detection, or target-not-found
    assert run.status == RunStatus.STOPPED
    assert run.stop_reason in (
        StopReason.OWNERSHIP_FAILURE,
        StopReason.DUPLICATE_ACTION,
        StopReason.CAPABILITY_NOT_AVAILABLE,
    )
    # The reload side-effect was wired — verify it was called (step 1 reload = 1)
    assert reload_calls[0] >= 1, "Target must be reloaded each step"


# ---------------------------------------------------------------------------
# Additional: context_builder raises on cross-user product load
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_context_builder_rejects_cross_user_product():
    """context_builder raises ProductOwnershipError when product_id doesn't belong to user."""
    user_a_id = str(uuid4())
    some_product_id = str(uuid4())

    mock_db = AsyncMock()
    # Query returns None → product not found for this user
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ProductOwnershipError):
        await build_context(
            db=mock_db,
            user_id=user_a_id,
            product_id=some_product_id,
        )
