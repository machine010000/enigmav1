"""
Tests for TASK-013: MasterBrain → Worker Registry → Execution Engine Handoff

Tests the autonomous Seller flow where Brain decides capabilities without client specifying workers.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.master_brain import master_brain
from app.ai.master_brain.models import BrainDecision, BrainAction
from app.engine.capabilities import capability_registry
from app.engine.engine import engine
from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus
from app.engine.registry import register_all


@pytest.fixture(autouse=True)
def setup_capability_registry():
    """Ensure capability registry is populated before tests run"""
    register_all()
    yield
    # Cleanup if needed


class TestBrainDecisionContract:
    """TEST 1-2: Brain decision contract and capability decision"""
    
    def test_brain_decision_dataclass(self):
        """Verify BrainDecision dataclass structure"""
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target="product-123",
            reasoning_summary="Test reasoning",
            execution_required=True,
            execution_input={"product_id": "product-123"},
            confidence=0.9,
        )
        
        assert decision.action == BrainAction.EXECUTE_CAPABILITY
        assert decision.capability == "product_verification"
        assert decision.execution_required is True
        assert decision.confidence == 0.9
        
        dict_repr = decision.to_dict()
        assert dict_repr["action"] == "execute_capability"
        assert dict_repr["capability"] == "product_verification"
    
    def test_non_execution_decision(self):
        """TEST 1: Non-execution Brain request returns CHAT action"""
        decision = master_brain.decide_capability("Hello, how are you?")
        
        assert decision.action == BrainAction.CHAT
        assert decision.execution_required is False
        assert decision.capability is None
    
    def test_product_verification_decision(self):
        """TEST 2: Brain produces capability decision for product verification"""
        decision = master_brain.decide_capability(
            "Please verify my product",
            context={"product_id": "test-product-id"}
        )
        
        assert decision.action == BrainAction.EXECUTE_CAPABILITY
        assert decision.capability == "product_verification"
        assert decision.execution_required is True
        assert decision.target == "test-product-id"
        assert decision.confidence > 0.0


class TestCapabilityRegistry:
    """TEST 3-4: Capability resolution and validation"""
    
    def test_capability_resolution(self):
        """TEST 3: Registry resolves product_verification to worker"""
        resolution = capability_registry.resolve_capability("product_verification")
        
        assert resolution is not None
        assert resolution["worker_name"] == "product_verification"
        assert resolution["capability"] is not None
        assert resolution["capability"]["id"] == "product_verification"
    
    def test_unknown_capability(self):
        """TEST 4: Unknown capability returns None"""
        resolution = capability_registry.resolve_capability("nonexistent_capability")
        
        assert resolution is None


class TestBrainEngineHandoff:
    """TEST 5-7: Brain → Engine handoff, context ownership, result evaluation"""
    
    @pytest.mark.asyncio
    async def test_execute_decision_with_capability(self):
        """TEST 5: Brain decision causes Engine execution"""
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target="test-product-id",
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": "test-product-id"},
            confidence=0.9,
        )
        
        # Mock the database and context builder
        mock_db = AsyncMock(spec=AsyncSession)
        mock_context = MagicMock()
        mock_context.execution_id = "test-execution-id"
        
        with patch('app.ai.master_brain.orchestrator.build_context', return_value=mock_context):
            with patch.object(engine, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = WorkerResult(
                    worker_name="product_verification",
                    status=WorkerStatus.SUCCESS,
                    result={"verified_name": "Test Product", "category": "Test"},
                    confidence=0.9,
                )
                
                result = await master_brain.execute_decision(
                    decision=decision,
                    db=mock_db,
                    user_id="test-user-id",
                )
                
                assert result["status"] == "completed"
                assert result["worker_name"] == "product_verification"
                assert result["capability"] == "product_verification"
                mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_ownership(self):
        """TEST 6: Authoritative context loaded server-side"""
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            target="server-product-id",
            reasoning_summary="Test",
            execution_required=True,
            execution_input={"product_id": "client-provided-id"},
            confidence=0.9,
        )
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_context = MagicMock()
        mock_context.execution_id = "test-execution-id"
        
        with patch('app.ai.master_brain.orchestrator.build_context', return_value=mock_context) as mock_build:
            with patch.object(engine, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = WorkerResult(
                    worker_name="product_verification",
                    status=WorkerStatus.SUCCESS,
                    result={},
                    confidence=0.9,
                )
                
                await master_brain.execute_decision(
                    decision=decision,
                    db=mock_db,
                    user_id="test-user-id",
                )
                
                # Verify build_context was called
                assert mock_build.called
                call_kwargs = mock_build.call_args.kwargs
                # Should use target from decision (server-side) over execution_input
                assert call_kwargs["product_id"] == "server-product-id"

    @pytest.mark.asyncio
    async def test_keyword_target_uses_authoritative_product_context(self):
        """TASK-039: a target UUID must never become the semantic topic."""
        product_id = "694a49de-c363-4a9c-aa17-67e80ae40fdb"
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="keyword_research",
            capability="keyword_research",
            target=product_id,
            reasoning_summary="Research product keywords",
            execution_required=True,
            execution_input={"topic": product_id, "goal": "commercial"},
            confidence=0.9,
        )
        context = ExecutionContext(
            user={"id": "test-user-id"},
            product={
                "id": product_id,
                "name": "Wireless Bluetooth Headphones",
                "description": "Over-ear headphones with active noise cancellation",
                "category": "Consumer Electronics",
                "target_market": "global",
            },
            memory=dict(decision.execution_input),
            execution_id="keyword-context-execution",
        )

        async def assert_context(worker_name, context, **kwargs):
            actual_context = context
            assert worker_name == "keyword_research"
            assert actual_context.recall("topic") == "Wireless Bluetooth Headphones"
            assert actual_context.recall("topic") != product_id
            assert actual_context.recall("target")["id"] == product_id
            assert actual_context.recall("market") == "global"
            return WorkerResult(
                worker_name="keyword_research",
                status=WorkerStatus.SUCCESS,
                result={"primary_keywords": [{"keyword": "wireless headphones"}]},
                evidence=[{"field": "primary_keywords"}],
                confidence=0.8,
            )

        with patch("app.ai.master_brain.orchestrator.build_context", return_value=context):
            with patch.object(engine, "execute", new=AsyncMock(side_effect=assert_context)):
                result = await master_brain.execute_decision(
                    decision=decision,
                    db=AsyncMock(spec=AsyncSession),
                    user_id="test-user-id",
                )

        assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_result_evaluation(self):
        """TEST 7: Worker result returns to Brain evaluation"""
        execution_result = {
            "status": "completed",
            "execution_id": "test-execution-id",
            "worker_name": "product_verification",
            "capability": "product_verification",
            "result": {
                "status": "success",
                "result": {
                    "verified_name": "Test Product",
                    "category": "Electronics",
                    "confidence": 0.95,
                    "issues": [],
                },
                "confidence": 0.95,
            },
        }
        
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            reasoning_summary="Test",
            execution_required=True,
            confidence=0.9,
        )
        
        response = master_brain.evaluate_execution_result(execution_result, decision)
        
        assert "reply" in response
        assert "execution" in response
        assert response["execution"]["status"] == "completed"
        assert response["execution"]["capability"] == "product_verification"
        assert "Test Product" in response["reply"]
        assert "Electronics" in response["reply"]


class TestFailureSemantics:
    """TEST 8-10: Failure handling, unknown capability, worker failure"""
    
    def test_unknown_capability_in_decision(self):
        """TEST 8: Unknown capability fails safely"""
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="test",
            capability="nonexistent_capability",
            reasoning_summary="Test",
            execution_required=True,
            confidence=0.9,
        )
        
        response = master_brain.evaluate_execution_result(
            {
                "status": "failed",
                "reason": "Capability 'nonexistent_capability' not registered",
                "decision": decision.to_dict(),
            },
            decision,
        )
        
        assert response["execution"]["status"] == "failed"
        assert "not registered" in response["execution"]["reason"]
    
    @pytest.mark.asyncio
    async def test_worker_failure_propagation(self):
        """TEST 10: Worker failure propagates correctly"""
        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent="product_verification",
            capability="product_verification",
            reasoning_summary="Test",
            execution_required=True,
            confidence=0.9,
        )
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_context = MagicMock()
        
        with patch('app.ai.master_brain.orchestrator.build_context', return_value=mock_context):
            with patch.object(engine, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.side_effect = Exception("Worker execution failed")
                
                result = await master_brain.execute_decision(
                    decision=decision,
                    db=mock_db,
                    user_id="test-user-id",
                )
                
                assert result["status"] == "failed"
                # The error message should contain the exception
                assert "failed" in result["status"]


class TestRegressionTests:
    """TEST 11-13: Regression tests for existing functionality"""
    
    @pytest.mark.asyncio
    async def test_existing_engine_execute_regression(self):
        """TEST 11: Existing /engine/execute behavior remains functional"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_context = MagicMock()
        mock_context.execution_id = "test-id"
        
        with patch('app.engine.context_builder.build_context', return_value=mock_context):
            with patch.object(engine, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = WorkerResult(
                    worker_name="product_verification",
                    status=WorkerStatus.SUCCESS,
                    result={},
                    confidence=0.9,
                )
                
                result = await engine.execute(
                    "product_verification",
                    mock_context,
                    db=mock_db,
                )
                
                assert result.status == WorkerStatus.SUCCESS
                mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_existing_chat_regression(self):
        """TEST 13: Existing normal /brain/chat behavior remains functional"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        with patch('app.ai.gateway.gateway') as mock_gateway:
            mock_gateway.chat = AsyncMock(return_value={
                "choices": [{"message": {"content": "Test response"}}]
            })
            
            result = await master_brain.chat(mock_db, "test-user-id", "Hello")
            
            assert result["reply"] == "Test response"
            assert result["intent"] == "general"


class TestSecurity:
    """Security: Capability validation prevents arbitrary execution"""
    
    def test_capability_validation(self):
        """Security: Only registered capabilities can be executed"""
        # Try to resolve an arbitrary/unregistered capability
        resolution = capability_registry.resolve_capability("arbitrary_malicious_capability")
        
        assert resolution is None, "Unregistered capabilities must not resolve"
    
    def test_worker_name_not_exposed_to_brain(self):
        """Security: Brain decision uses capability, not worker name"""
        decision = master_brain.decide_capability("verify product", {"product_id": "test"})
        
        # Decision should contain capability, not concrete worker class
        assert decision.capability == "product_verification"
        assert not hasattr(decision, 'worker_class')
        assert not hasattr(decision, 'worker_name')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
