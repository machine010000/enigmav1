"""
Test Pipeline Context
"""

import pytest

from app.pipeline.context import PipelineContext, PipelineStage, PipelineStatus
from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.economics import EconomicDecision


class TestPipelineContext:
    """Test pipeline context."""
    
    def test_context_initialization(self):
        """Test context initialization."""
        context = PipelineContext(job_id="test_job")
        
        assert context.job_id == "test_job"
        assert context.current_stage == PipelineStage.JOB_RECEIVED
        assert context.status == PipelineStatus.PENDING
        assert context.knowledge_readiness == 0.5
        assert context.evidence_readiness == 0.5
    
    def test_can_proceed_to_execution_accept(self):
        """Test can_proceed_to_execution with ACCEPT decision."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT"
        
        assert context.can_proceed_to_execution() is True
    
    def test_can_proceed_to_execution_accept_with_conditions(self):
        """Test can_proceed_to_execution with ACCEPT_WITH_CONDITIONS."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT_WITH_CONDITIONS"
        
        assert context.can_proceed_to_execution() is True
    
    def test_can_proceed_to_execution_reject(self):
        """Test can_proceed_to_execution with REJECT decision."""
        context = PipelineContext(job_id="test_job")
        context.decision = "REJECT"
        
        assert context.can_proceed_to_execution() is False
    
    def test_can_proceed_to_execution_need_research(self):
        """Test can_proceed_to_execution with NEED_RESEARCH decision."""
        context = PipelineContext(job_id="test_job")
        context.decision = "NEED_RESEARCH"
        
        assert context.can_proceed_to_execution() is False
    
    def test_can_proceed_to_execution_economics_blocked(self):
        """Test can_proceed_to_execution with economics blocking."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT"
        context.economic_blocking_reason = "Insufficient credits"
        
        assert context.can_proceed_to_execution() is False
    
    def test_can_proceed_to_execution_knowledge_blocked(self):
        """Test can_proceed_to_execution with knowledge blocking."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT"
        context.knowledge_blocking_reason = "Insufficient knowledge"
        
        assert context.can_proceed_to_execution() is False
    
    def test_can_proceed_to_execution_evidence_blocked(self):
        """Test can_proceed_to_execution with evidence blocking."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT"
        context.evidence_blocking_reason = "Insufficient evidence"
        
        assert context.can_proceed_to_execution() is False
    
    def test_can_proceed_to_execution_execution_blocked(self):
        """Test can_proceed_to_execution with execution blocking."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT"
        context.execution_blocking_reason = "High risk"
        
        assert context.can_proceed_to_execution() is False
    
    def test_is_blocked(self):
        """Test is_blocked method."""
        context = PipelineContext(job_id="test_job")
        context.status = PipelineStatus.BLOCKED
        
        assert context.is_blocked() is True
    
    def test_is_not_blocked(self):
        """Test is_blocked when not blocked."""
        context = PipelineContext(job_id="test_job")
        context.status = PipelineStatus.IN_PROGRESS
        
        assert context.is_blocked() is False
    
    def test_is_failed(self):
        """Test is_failed method."""
        context = PipelineContext(job_id="test_job")
        context.status = PipelineStatus.FAILED
        
        assert context.is_failed() is True
    
    def test_is_not_failed(self):
        """Test is_failed when not failed."""
        context = PipelineContext(job_id="test_job")
        context.status = PipelineStatus.IN_PROGRESS
        
        assert context.is_failed() is False
    
    def test_is_completed(self):
        """Test is_completed method."""
        context = PipelineContext(job_id="test_job")
        context.status = PipelineStatus.COMPLETED
        
        assert context.is_completed() is True
    
    def test_is_not_completed(self):
        """Test is_completed when not completed."""
        context = PipelineContext(job_id="test_job")
        context.status = PipelineStatus.IN_PROGRESS
        
        assert context.is_completed() is False
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        context = PipelineContext(job_id="test_job")
        context.decision = "ACCEPT"
        context.profession = "seo"
        
        result = context.to_dict()
        
        assert result["job_id"] == "test_job"
        assert result["decision"] == "ACCEPT"
        assert result["profession"] == "seo"
        assert result["status"] == "pending"
    
    def test_economic_decision_mapping(self):
        """Test economic decision mapping in context."""
        context = PipelineContext(job_id="test_job")
        context.economic_decision = EconomicDecision.INSUFFICIENT_BALANCE
        
        result = context.to_dict()
        
        assert result["economic_decision"] == "insufficient_balance"
    
    def test_platform_mapping(self):
        """Test platform mapping in context."""
        context = PipelineContext(job_id="test_job")
        context.platform = MarketplacePlatform.UPWORK
        
        result = context.to_dict()
        
        assert result["platform"] == "upwork"
