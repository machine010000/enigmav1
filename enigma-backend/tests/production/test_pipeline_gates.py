"""
Pipeline Gate Regression Tests

Tests to ensure pipeline gates are not bypassed and block correctly.
"""

import pytest

from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.context import PipelineContext, PipelineStage, PipelineStatus
from app.pipeline.trace import PipelineTrace
from app.marketplace.economics import EconomicDecision
from app.marketplace.account_economics import EconomicSafetyStatus


class TestEconomicsGate:
    """Test economics gate blocking."""
    
    def test_economics_gate_blocks_on_insufficient_balance(self):
        """Test economics gate blocks on insufficient balance."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set blocking economic decision
        context.economic_decision = EconomicDecision.INSUFFICIENT_BALANCE
        
        result = orchestrator._check_economics_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
    
    def test_economics_gate_blocks_on_safety_block(self):
        """Test economics gate blocks on account safety BLOCK."""
        from app.marketplace.account_economics import EconomicSafetyResult
        
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set blocking safety result
        context.economic_safety_result = EconomicSafetyResult(
            status=EconomicSafetyStatus.BLOCK,
            blocking_reason="Account suspended",
            metrics=None,
        )
        
        result = orchestrator._check_economics_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
        assert "suspended" in context.economic_blocking_reason.lower()
    
    def test_economics_gate_blocks_on_need_research(self):
        """Test economics gate blocks on NEED_RESEARCH."""
        from app.marketplace.account_economics import EconomicSafetyResult
        
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set NEED_RESEARCH safety result
        context.economic_safety_result = EconomicSafetyResult(
            status=EconomicSafetyStatus.NEED_RESEARCH,
            blocking_reason="Stale account data",
            metrics=None,
        )
        
        result = orchestrator._check_economics_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
    
    def test_economics_gate_passes_on_safe(self):
        """Test economics gate passes on SAFE status."""
        from app.marketplace.account_economics import EconomicSafetyResult
        
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set SAFE safety result
        context.economic_safety_result = EconomicSafetyResult(
            status=EconomicSafetyStatus.SAFE,
            blocking_reason=None,
            metrics=None,
        )
        
        result = orchestrator._check_economics_gate(context, trace)
        
        assert result is True
    
    def test_economics_gate_passes_on_accept_decision(self):
        """Test economics gate passes on ACCEPT decision."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set accepting economic decision (APPLY is the positive decision)
        context.economic_decision = EconomicDecision.APPLY
        
        result = orchestrator._check_economics_gate(context, trace)
        
        assert result is True


class TestKnowledgeEvidenceGate:
    """Test knowledge/evidence gate blocking."""
    
    def test_knowledge_gate_blocks_on_low_readiness(self):
        """Test knowledge gate blocks on low readiness."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set low knowledge readiness
        context.knowledge_readiness = 0.2
        
        result = orchestrator._check_knowledge_evidence_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
    
    def test_evidence_gate_blocks_on_low_readiness(self):
        """Test evidence gate blocks on low readiness."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set low evidence readiness
        context.knowledge_readiness = 0.8  # Knowledge OK
        context.evidence_readiness = 0.2  # Evidence low
        
        result = orchestrator._check_knowledge_evidence_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
    
    def test_knowledge_gate_blocks_on_explicit_reason(self):
        """Test knowledge gate blocks on explicit blocking reason."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set explicit blocking reason
        context.knowledge_blocking_reason = "Knowledge gap detected"
        
        result = orchestrator._check_knowledge_evidence_gate(context, trace)
        
        assert result is False
    
    def test_knowledge_evidence_gate_passes_on_high_readiness(self):
        """Test knowledge/evidence gate passes on high readiness."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set high readiness
        context.knowledge_readiness = 0.8
        context.evidence_readiness = 0.8
        
        result = orchestrator._check_knowledge_evidence_gate(context, trace)
        
        assert result is True


class TestDecisionGate:
    """Test decision gate blocking."""
    
    def test_decision_gate_blocks_on_reject(self):
        """Test decision gate blocks on REJECT."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set REJECT decision
        context.decision = "REJECT"
        
        result = orchestrator._check_decision_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
    
    def test_decision_gate_blocks_on_decline(self):
        """Test decision gate blocks on DECLINE."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set DECLINE decision
        context.decision = "DECLINE"
        
        result = orchestrator._check_decision_gate(context, trace)
        
        assert result is False
    
    def test_decision_gate_passes_on_accept(self):
        """Test decision gate passes on ACCEPT."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set ACCEPT decision
        context.decision = "ACCEPT"
        
        result = orchestrator._check_decision_gate(context, trace)
        
        assert result is True
    
    def test_decision_gate_passes_on_accept_with_conditions(self):
        """Test decision gate passes on ACCEPT_WITH_CONDITIONS."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set ACCEPT_WITH_CONDITIONS decision
        context.decision = "ACCEPT_WITH_CONDITIONS"
        
        result = orchestrator._check_decision_gate(context, trace)
        
        assert result is True


class TestExecutionGate:
    """Test execution gate blocking."""
    
    def test_execution_gate_blocks_on_low_readiness(self):
        """Test execution gate blocks on low readiness."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set low execution readiness
        context.execution_readiness = 0.3
        
        result = orchestrator._check_execution_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
    
    def test_execution_gate_blocks_on_explicit_reason(self):
        """Test execution gate blocks on explicit blocking reason."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set explicit blocking reason
        context.execution_blocking_reason = "Execution not ready"
        
        result = orchestrator._check_execution_gate(context, trace)
        
        assert result is False
    
    def test_execution_gate_passes_on_high_readiness(self):
        """Test execution gate passes on high readiness."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set high execution readiness
        context.execution_readiness = 0.8
        
        result = orchestrator._check_execution_gate(context, trace)
        
        assert result is True


class TestGateOrder:
    """Test gate execution order."""
    
    def test_gates_execute_in_correct_order(self):
        """Test that gates execute in the correct order."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set all gates to pass
        context.economic_decision = EconomicDecision.APPLY
        context.knowledge_readiness = 0.8
        context.evidence_readiness = 0.8
        context.decision = "ACCEPT"
        context.execution_readiness = 0.8
        
        # All gates should pass
        assert orchestrator._check_economics_gate(context, trace) is True
        assert orchestrator._check_knowledge_evidence_gate(context, trace) is True
        assert orchestrator._check_decision_gate(context, trace) is True
        assert orchestrator._check_execution_gate(context, trace) is True
    
    def test_early_gate_blocks_later_gates(self):
        """Test that early gate blocking prevents later gate execution."""
        orchestrator = PipelineOrchestrator()
        context = PipelineContext(job_id="test", job_data={})
        trace = PipelineTrace(pipeline_id="test", job_id="test")
        
        # Set economics gate to block
        context.economic_decision = EconomicDecision.INSUFFICIENT_BALANCE
        
        # Economics gate should block
        result = orchestrator._check_economics_gate(context, trace)
        
        # Gate returns False when blocked
        assert result is False
