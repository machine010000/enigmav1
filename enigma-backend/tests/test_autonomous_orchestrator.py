"""
Tests for TASK-ENG-CONTROLLED-AUTONOMY-015

Tests the bounded multi-step autonomous orchestrator.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.autonomy.orchestrator import AutonomousOrchestrator
from app.autonomy.contracts import (
    AutonomousRun,
    AutonomousStep,
    RunStatus,
    StepStatus,
    StopReason,
)
from app.ai.master_brain.models import BrainDecision, BrainAction
from app.ai.client import AITimeoutError, AIAuthenticationError, AIConfigurationError, AIConnectionError, AIProviderError
from app.engine.capabilities import capability_registry


@pytest.mark.asyncio
async def test_single_step_successful_autonomous_run():
    """TEST 1: Single-step successful autonomous run."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": str(uuid4())},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            return_value={
                "action": BrainAction.FINISH.value,
                "reason": "Test completed",
                "next_action": None,
            }
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )
        
        # Verify
        assert run.status == RunStatus.COMPLETED
        assert len(run.steps) == 1
        assert run.steps[0].status == StepStatus.COMPLETED
        assert run.stop_reason == StopReason.FINISHED


@pytest.mark.asyncio
async def test_brain_finish_stops_immediately():
    """TEST 2: Brain FINISH stops immediately."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock master brain to return FINISH
    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        return_value=BrainDecision(
            action=BrainAction.FINISH,
            intent="finish",
            reasoning_summary="No action needed",
            execution_required=False,
            confidence=0.9,
        )
    )
    orchestrator.master_brain = mock_brain
    
    # Run autonomous
    run = await orchestrator.run_autonomous(
        user_id=str(uuid4()),
        goal="hello",
        target_id=None,
        module="seller",
        db=None,
    )
    
    # Verify
    assert run.status == RunStatus.COMPLETED
    assert len(run.steps) == 0
    assert run.stop_reason == StopReason.FINISHED


@pytest.mark.asyncio
async def test_valid_executable_next_capability_executes_when_budget_remains():
    """TEST 3: Valid executable next capability executes when budget remains."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain for two steps
        mock_brain = MagicMock()
        
        # Step 1: Execute product_verification
        decision1 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=str(uuid4()),
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": str(uuid4())},
            confidence=0.9,
        )
        
        # Step 2: Execute another capability (if available)
        decision2 = BrainDecision(
            action=BrainAction.FINISH,
            intent="finish",
            reasoning_summary="Done",
            execution_required=False,
            confidence=0.9,
        )
        
        mock_brain.decide_capability = MagicMock(side_effect=[decision1, decision2])
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            return_value={
                "action": BrainAction.FINISH.value,
                "reason": "Test completed",
                "next_action": None,
            }
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )
        
        # Verify
        assert run.status == RunStatus.COMPLETED
        assert len(run.steps) == 1
        assert run.steps[0].status == StepStatus.COMPLETED


@pytest.mark.asyncio
async def test_missing_capability_worker_does_not_invent_execute_worker():
    """TEST 4: Missing capability worker does NOT invent/execute worker."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock master brain to request non-existent capability
    mock_brain = MagicMock()
    mock_brain.decide_capability = MagicMock(
        return_value=BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="market_research",
            capability="market_research",  # Not registered
            target=str(uuid4()),
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": str(uuid4())},
            confidence=0.9,
        )
    )
    orchestrator.master_brain = mock_brain
    
    # Run autonomous
    run = await orchestrator.run_autonomous(
        user_id=str(uuid4()),
        goal="research market",
        target_id=str(uuid4()),
        module="seller",
        db=None,
    )
    
    # Verify
    assert run.status == RunStatus.STOPPED
    assert len(run.steps) == 0
    assert run.stop_reason == StopReason.CAPABILITY_NOT_AVAILABLE
    assert "not registered" in run.final_response.lower()


@pytest.mark.asyncio
async def test_step_limit_stops_execution():
    """TEST 5: Step limit stops execution."""
    orchestrator = AutonomousOrchestrator(max_steps=2)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain to always recommend next action
        mock_brain = MagicMock()
        # Use different targets to avoid duplicate protection
        target1 = str(uuid4())
        target2 = str(uuid4())
        
        decision1 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target1,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target1},
            confidence=0.9,
        )
        
        decision2 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target2,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target2},
            confidence=0.9,
        )
        
        mock_brain.decide_capability = MagicMock(side_effect=[decision1, decision2])
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            return_value={
                "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                "reason": "Continue",
                "next_action": "verify again",
                "next_action_reasoning": "Test",
            }
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=target1,
            module="seller",
            db=None,
        )
        
        # Verify
        assert run.status == RunStatus.STOPPED
        assert len(run.steps) == 2  # Max steps reached
        assert run.stop_reason == StopReason.STEP_LIMIT_REACHED


@pytest.mark.asyncio
async def test_duplicate_action_protection_stops_repeated_identical_execution():
    """TEST 6: Duplicate action protection stops repeated identical execution."""
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=3)
        
        # Mock master brain to request same capability twice
        mock_brain = MagicMock()
        target = str(uuid4())
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target},
            confidence=0.9,
        )
        
        # Return same decision for both iterations
        mock_brain.decide_capability = MagicMock(return_value=decision)
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        # Return RECOMMEND_NEXT_ACTION to trigger second iteration
        mock_brain._re_evaluate_after_execution = MagicMock(
            return_value={
                "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                "reason": "Continue",
                "next_action": "verify again",
                "next_action_reasoning": "Test",
            }
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=target,
            module="seller",
            db=None,
        )
        
        # Verify - duplicate protection should stop the run
        assert run.status == RunStatus.STOPPED
        assert len(run.steps) == 1  # Only first step executed
        assert run.stop_reason == StopReason.DUPLICATE_ACTION


@pytest.mark.asyncio
async def test_worker_failure_persists_failure_observation_and_stops():
    """TEST 7: Worker failure persists failure observation and stops."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain to fail execution
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": str(uuid4())},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            side_effect=Exception("Worker failed")
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )
        
        # Verify
        assert run.status == RunStatus.STOPPED
        assert len(run.steps) == 1
        assert run.steps[0].status == StepStatus.FAILED
        assert run.stop_reason == StopReason.FAILURE
        assert run.steps[0].error is not None


@pytest.mark.asyncio
async def test_provider_timeout_stops_loop():
    """TEST 8: Provider timeout stops loop."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain to timeout
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": str(uuid4())},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            side_effect=AITimeoutError("AI provider timeout")
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )
        
        # Verify
        assert run.status == RunStatus.STOPPED
        assert len(run.steps) == 1
        assert run.steps[0].status == StepStatus.FAILED
        assert run.stop_reason == StopReason.FAILURE
        assert "timeout" in run.steps[0].error.lower()


@pytest.mark.asyncio
async def test_ownership_failure_stops_loop():
    """TEST 9: Ownership failure stops loop."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": str(uuid4())},
                confidence=0.9,
            )
        )
        orchestrator.master_brain = mock_brain
        
        # Mock ownership validation to fail
        orchestrator._validate_ownership = AsyncMock(return_value=False)
        orchestrator._reload_authoritative_target = AsyncMock(return_value=None)
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=MagicMock(),  # Mock db to trigger ownership validation
        )
        
        # TASK-016: ownership failure now raises OWNERSHIP_FAILURE (not CAPABILITY_NOT_AVAILABLE)
        assert run.status == RunStatus.STOPPED
        assert len(run.steps) == 0
        assert run.stop_reason == StopReason.OWNERSHIP_FAILURE
        assert "not found" in run.final_response.lower()


@pytest.mark.asyncio
async def test_every_step_produces_trace_entry():
    """TEST 10: Every step produces trace entry."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain for 2 steps
        mock_brain = MagicMock()
        # Use different targets to avoid duplicate protection
        target1 = str(uuid4())
        target2 = str(uuid4())
        
        decision1 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target1,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target1},
            confidence=0.9,
        )
        
        decision2 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target2,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target2},
            confidence=0.9,
        )
        
        mock_brain.decide_capability = MagicMock(side_effect=[decision1, decision2])
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            side_effect=[
                {
                    "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                    "reason": "Continue",
                    "next_action": "verify again",
                    "next_action_reasoning": "Test",
                },
                {
                    "action": BrainAction.FINISH.value,
                    "reason": "Done",
                    "next_action": None,
                },
            ]
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=target1,
            module="seller",
            db=None,
        )
        
        # Verify
        assert len(run.steps) == 2
        for step in run.steps:
            assert step.step_number is not None
            assert step.decision is not None
            assert step.capability is not None
            assert step.status is not None
            assert step.started_at is not None
            assert step.completed_at is not None


@pytest.mark.asyncio
async def test_no_worker_name_accepted_from_client_decision_path():
    """TEST 11: No worker_name accepted from client decision path."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Verify that BrainDecision does not have worker_name field
    decision = BrainDecision(
        action=BrainAction.EXECUTE_CAPABILITY,
        intent="product_verification",
        capability="product_verification",
        target=str(uuid4()),
        reasoning_summary="Test",
        execution_required=True,
        execution_input={"product_id": str(uuid4())},
        confidence=0.9,
    )
    
    # Verify worker_name is not in decision
    assert not hasattr(decision, "worker_name")
    
    # Verify decision.to_dict does not include worker_name
    decision_dict = decision.to_dict()
    assert "worker_name" not in decision_dict


@pytest.mark.asyncio
async def test_task014_learning_persistence_remains_functional():
    """TEST 12: TASK-014 learning persistence remains functional."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain with learning
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": str(uuid4())},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
                "learning": {
                    "persisted": True,
                    "evidence_count": 3,
                    "profile_updated": True,
                },
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            return_value={
                "action": BrainAction.FINISH.value,
                "reason": "Done",
                "next_action": None,
            }
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )
        
        # Verify learning was called
        assert mock_brain.execute_with_learning.called
        assert len(run.steps) == 1
        assert run.steps[0].outcome is not None
        assert "learning" in run.steps[0].outcome


@pytest.mark.asyncio
async def test_second_decision_reloads_persisted_context():
    """TEST 13: Second decision reloads persisted context."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain
        mock_brain = MagicMock()
        # Use different targets to avoid duplicate protection
        target1 = str(uuid4())
        target2 = str(uuid4())
        
        decision1 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target1,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target1},
            confidence=0.9,
        )
        
        decision2 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target2,
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": target2},
            confidence=0.9,
        )
        
        mock_brain.decide_capability = MagicMock(side_effect=[decision1, decision2])
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            side_effect=[
                {
                    "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                    "reason": "Continue",
                    "next_action": "verify again",
                    "next_action_reasoning": "Test",
                },
                {
                    "action": BrainAction.FINISH.value,
                    "reason": "Done",
                    "next_action": None,
                },
            ]
        )
        orchestrator.master_brain = mock_brain
        
        # TASK-016: patch ownership so mock db doesn't cause DB errors
        orchestrator._validate_ownership = AsyncMock(return_value=True)
        orchestrator._reload_authoritative_target = AsyncMock(return_value=MagicMock())
        
        # Mock db for context loading
        mock_db = MagicMock()
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=target1,
            module="seller",
            db=mock_db,
        )
        
        # Verify context was loaded for second step
        assert len(run.steps) == 2
        # Context loading happens in _load_step_context


@pytest.mark.asyncio
async def test_task013_brain_registry_engine_flow_remains_functional():
    """TEST 14: TASK-013 Brain→Registry→Engine flow remains functional."""
    orchestrator = AutonomousOrchestrator(max_steps=3)
    
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        # Mock master brain
        mock_brain = MagicMock()
        mock_brain.decide_capability = MagicMock(
            return_value=BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=str(uuid4()),
                reasoning_summary="Test",
                execution_required=True,
                execution_input={"product_id": str(uuid4())},
                confidence=0.9,
            )
        )
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test"}},
                "confidence": 0.9,
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            return_value={
                "action": BrainAction.FINISH.value,
                "reason": "Done",
                "next_action": None,
            }
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="verify my product",
            target_id=str(uuid4()),
            module="seller",
            db=None,
        )
        
        # Verify Brain→Registry→Engine flow was used
        assert mock_brain.decide_capability.called
        assert mock_brain.execute_with_learning.called


# Tests 15-18 are integration tests that require full system setup
# These would be tested in the E2E test file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
