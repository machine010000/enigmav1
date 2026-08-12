"""
E2E test for TASK-ENG-CONTROLLED-AUTONOMY-015

Tests the multi-step autonomous orchestration end-to-end.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.autonomy.orchestrator import AutonomousOrchestrator
from app.autonomy.contracts import RunStatus, StopReason
from app.ai.master_brain.models import BrainDecision, BrainAction
from app.engine.capabilities import capability_registry


@pytest.mark.asyncio
async def test_multi_step_autonomous_e2e():
    """E2E test: Multi-step autonomous run with learning loop."""
    # Mock capability registry
    with patch.object(capability_registry, 'resolve_capability', return_value={
        "worker_name": "product_verification",
        "capability": {"id": "product_verification", "description": "Test"},
    }):
        orchestrator = AutonomousOrchestrator(max_steps=3)
        
        # Mock master brain for multi-step scenario
        mock_brain = MagicMock()
        
        # Step 1: Verify product
        target1 = str(uuid4())
        decision1 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target1,
            reasoning_summary="Verify product details",
            execution_required=True,
            execution_input={"product_id": target1},
            confidence=0.9,
        )
        
        # Step 2: Analyze results (different target to avoid duplicate protection)
        target2 = str(uuid4())
        decision2 = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target=target2,
            reasoning_summary="Analyze related product",
            execution_required=True,
            execution_input={"product_id": target2},
            confidence=0.85,
        )
        
        # Step 3: Finish
        decision3 = BrainDecision(
            action=BrainAction.FINISH,
            intent="finish",
            reasoning_summary="Analysis complete",
            execution_required=False,
            confidence=0.95,
        )
        
        mock_brain.decide_capability = MagicMock(side_effect=[decision1, decision2, decision3])
        mock_brain.execute_with_learning = AsyncMock(
            return_value={
                "status": "completed",
                "execution_id": str(uuid4()),
                "worker": "product_verification",
                "result": {"result": {"verified_name": "Test Product"}},
                "confidence": 0.9,
                "learning": {
                    "persisted": True,
                    "evidence_count": 2,
                    "profile_updated": True,
                },
            }
        )
        mock_brain._re_evaluate_after_execution = MagicMock(
            side_effect=[
                {
                    "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                    "reason": "Need to analyze related product",
                    "next_action": "analyze related product",
                    "next_action_reasoning": "Found related items",
                },
                {
                    "action": BrainAction.FINISH.value,
                    "reason": "Analysis complete",
                    "next_action": None,
                },
            ]
        )
        orchestrator.master_brain = mock_brain
        
        # Run autonomous
        run = await orchestrator.run_autonomous(
            user_id=str(uuid4()),
            goal="Analyze my products",
            target_id=target1,
            module="seller",
            db=None,
        )
        
        # Verify
        assert run.status == RunStatus.COMPLETED
        assert len(run.steps) == 2  # Two execution steps
        assert run.stop_reason == StopReason.FINISHED
        
        # Verify learning was called for each step
        assert mock_brain.execute_with_learning.call_count == 2
        
        # Verify re-evaluation was called after each step
        assert mock_brain._re_evaluate_after_execution.call_count == 2
        
        # Verify step traces
        for step in run.steps:
            assert step.step_number is not None
            assert step.decision is not None
            assert step.capability == "product_verification"
            assert step.status.name == "COMPLETED"
            assert step.started_at is not None
            assert step.completed_at is not None
            assert step.outcome is not None
            assert "learning" in step.outcome


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
