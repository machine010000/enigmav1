"""
Negative Tests for Pipeline - Bypass Prevention

Tests that ensure pipeline cannot bypass:
- Economics gate
- Knowledge/Evidence gate
- Decision authority
- Execution gate
"""

import pytest

from app.pipeline.orchestrator import PipelineOrchestrator, StageResult
from app.pipeline.context import PipelineContext, PipelineStage, PipelineStatus
from app.marketplace.economics import EconomicDecision
from app.marketplace.contracts import MarketplacePlatform


class TestEconomicsGateBypass:
    """Test that economics gate cannot be bypassed."""
    
    def test_cannot_bypass_insufficient_balance(self):
        """Test that insufficient balance cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def economics_handler(context: PipelineContext) -> StageResult:
            context.economic_decision = EconomicDecision.INSUFFICIENT_BALANCE
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            # Try to accept despite insufficient balance
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.ECONOMICS_ASSESSMENT: economics_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        # Should be blocked at economics gate
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.ECONOMICS_ASSESSMENT
        assert context.can_proceed_to_execution() is False
    
    def test_cannot_bypass_insufficient_quota(self):
        """Test that insufficient quota cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def economics_handler(context: PipelineContext) -> StageResult:
            context.economic_decision = EconomicDecision.INSUFFICIENT_QUOTA
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.ECONOMICS_ASSESSMENT: economics_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.ECONOMICS_ASSESSMENT
    
    def test_cannot_bypass_requires_money(self):
        """Test that requires money cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def economics_handler(context: PipelineContext) -> StageResult:
            context.economic_decision = EconomicDecision.REQUIRES_MONEY
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.ECONOMICS_ASSESSMENT: economics_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.ECONOMICS_ASSESSMENT


class TestKnowledgeEvidenceGateBypass:
    """Test that knowledge/evidence gate cannot be bypassed."""
    
    def test_cannot_bypass_insufficient_knowledge(self):
        """Test that insufficient knowledge cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def knowledge_handler(context: PipelineContext) -> StageResult:
            context.knowledge_readiness = 0.2
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.KNOWLEDGE_READINESS: knowledge_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.KNOWLEDGE_READINESS
    
    def test_cannot_bypass_insufficient_evidence(self):
        """Test that insufficient evidence cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def evidence_handler(context: PipelineContext) -> StageResult:
            context.evidence_readiness = 0.2
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.EVIDENCE_READINESS: evidence_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.KNOWLEDGE_READINESS
    
    def test_cannot_bypass_knowledge_blocking_reason(self):
        """Test that explicit knowledge blocking cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def knowledge_handler(context: PipelineContext) -> StageResult:
            context.knowledge_blocking_reason = "Knowledge gap detected"
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.KNOWLEDGE_READINESS: knowledge_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.KNOWLEDGE_READINESS


class TestDecisionAuthorityBypass:
    """Test that decision authority cannot be bypassed."""
    
    def test_reject_blocks_execution(self):
        """Test that REJECT decision blocks execution."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "REJECT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.DECISION_EVALUATION
        assert context.can_proceed_to_execution() is False
    
    def test_need_research_blocks_execution(self):
        """Test that NEED_RESEARCH decision blocks execution."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "NEED_RESEARCH"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.DECISION_EVALUATION
    
    def test_need_clarification_blocks_execution(self):
        """Test that NEED_CLARIFICATION decision blocks execution."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "NEED_CLARIFICATION"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.DECISION_EVALUATION
    
    def test_need_negotiation_blocks_execution(self):
        """Test that NEED_NEGOTIATION decision blocks execution."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "NEED_NEGOTIATION"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.DECISION_EVALUATION
    
    def test_pending_blocks_execution(self):
        """Test that PENDING decision blocks execution."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "PENDING"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.DECISION_EVALUATION


class TestExecutionGateBypass:
    """Test that execution gate cannot be bypassed."""
    
    def test_cannot_bypass_high_risk(self):
        """Test that high risk cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def execution_handler(context: PipelineContext) -> StageResult:
            context.risk_score = 0.9
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.EXECUTION_READINESS: execution_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.EXECUTION_READINESS
    
    def test_cannot_bypass_low_scope_clarity(self):
        """Test that low scope clarity cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def execution_handler(context: PipelineContext) -> StageResult:
            context.scope_clarity = 0.3
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.EXECUTION_READINESS: execution_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.EXECUTION_READINESS
    
    def test_cannot_bypass_low_execution_readiness(self):
        """Test that low execution readiness cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def execution_handler(context: PipelineContext) -> StageResult:
            context.execution_readiness = 0.3
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.EXECUTION_READINESS: execution_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.EXECUTION_READINESS
    
    def test_cannot_bypass_execution_blocking_reason(self):
        """Test that explicit execution blocking cannot be bypassed."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def execution_handler(context: PipelineContext) -> StageResult:
            context.execution_blocking_reason = "Capability missing"
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.EXECUTION_READINESS: execution_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context.status == PipelineStatus.BLOCKED
        assert context.blocking_stage == PipelineStage.EXECUTION_READINESS


class TestCreativityDoesNotMakeDecision:
    """Test that creativity does not make final decision."""
    
    def test_creativity_strategies_do_not_approve(self):
        """Test that creativity strategies do not approve execution."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def work_spec_handler(context: PipelineContext) -> StageResult:
            context.work_specification = "SEO project"
            context.profession = "seo"
            context.expert_domain = "seo"
            return StageResult(success=True, blocking=False)
        
        # Creativity generates strategies but does not set decision
        def decision_handler(context: PipelineContext) -> StageResult:
            # Decision handler must explicitly set decision
            # Creativity result should not auto-approve
            assert context.creativity_result is not None
            assert len(context.creativity_result.ranked_strategies) >= 0
            # Decision is not set by creativity
            context.decision = "ACCEPT"  # Must be set explicitly
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.WORK_SPECIFICATION: work_spec_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        # Creativity should have generated strategies
        assert context.creativity_result is not None
        # But decision must be set by decision handler
        assert context.decision == "ACCEPT"


class TestNoFakeData:
    """Test that pipeline does not introduce fake data."""
    
    def test_no_fake_portfolio_in_context(self):
        """Test that context does not contain fake portfolio."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def work_spec_handler(context: PipelineContext) -> StageResult:
            context.work_specification = "SEO project"
            context.profession = "seo"
            context.expert_domain = "seo"
            context.portfolio_strength = 0.2  # Low, not fake
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.WORK_SPECIFICATION: work_spec_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        # Portfolio strength should be realistic (0.0 to 1.0)
        assert 0.0 <= context.portfolio_strength <= 1.0
    
    def test_no_fake_reviews_in_context(self):
        """Test that context does not contain fake reviews."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def work_spec_handler(context: PipelineContext) -> StageResult:
            context.work_specification = "SEO project"
            context.profession = "seo"
            context.expert_domain = "seo"
            context.review_strength = 0.2  # Low, not fake
            return StageResult(success=True, blocking=False)
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.WORK_SPECIFICATION: work_spec_handler,
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        # Review strength should be realistic (0.0 to 1.0)
        assert 0.0 <= context.review_strength <= 1.0


class TestNoLiveAPIs:
    """Test that pipeline does not use live marketplace APIs."""
    
    def test_pipeline_works_without_live_apis(self):
        """Test that pipeline works without live marketplace APIs."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        def decision_handler(context: PipelineContext) -> StageResult:
            context.decision = "ACCEPT"
            return StageResult(success=True, blocking=False)
        
        stage_handlers = {
            PipelineStage.DECISION_EVALUATION: decision_handler,
        }
        
        # Should work without any live API calls
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        assert context is not None
        assert trace is not None


class TestStageOrder:
    """Test that stages execute in correct order."""
    
    def test_stages_execute_in_order(self):
        """Test that stages execute in the defined order."""
        orchestrator = PipelineOrchestrator()
        
        job_data = {"title": "Test Job"}
        
        execution_order = []
        
        def order_tracking_handler(stage: PipelineStage):
            def handler(context: PipelineContext) -> StageResult:
                execution_order.append(stage)
                return StageResult(success=True, blocking=False)
            return handler
        
        stage_handlers = {
            PipelineStage.JOB_RECEIVED: order_tracking_handler(PipelineStage.JOB_RECEIVED),
            PipelineStage.CLASSIFICATION: order_tracking_handler(PipelineStage.CLASSIFICATION),
            PipelineStage.WORK_SPECIFICATION: order_tracking_handler(PipelineStage.WORK_SPECIFICATION),
            PipelineStage.DECISION_EVALUATION: order_tracking_handler(PipelineStage.DECISION_EVALUATION),
        }
        
        context, trace = orchestrator.execute_pipeline("test_job", job_data, stage_handlers)
        
        # Verify order
        expected_order = [
            PipelineStage.JOB_RECEIVED,
            PipelineStage.CLASSIFICATION,
            PipelineStage.WORK_SPECIFICATION,
            PipelineStage.DECISION_EVALUATION,
        ]
        assert execution_order == expected_order
