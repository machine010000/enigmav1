"""
Tests for SEO Readiness Evolution module.

Tests readiness evolution based on executions and evidence.
"""

import pytest
from datetime import datetime, timedelta

from app.expert_domains.domains.seo_readiness_evolution import (
    ExecutionResult,
    ExecutionRecord,
    EvidenceImpact,
    KnowledgeImpact,
    SEOKnowledgeReadinessEvolution,
    SEOKnowledgeReadinessOrchestrator,
)
from app.expert_domains.contracts import ReadinessScore
from app.knowledge_governance.models import KnowledgeMaturity


class TestExecutionRecord:
    """Test execution record."""

    def test_execution_record_creation(self):
        """Test creating an execution record."""
        record = ExecutionRecord(
            execution_id="exec_001",
            task_id="technical_seo_audit_task",
            result=ExecutionResult.SUCCESS,
            duration_seconds=3600.0,
            quality_score=0.9,
        )
        
        assert record.execution_id == "exec_001"
        assert record.result == ExecutionResult.SUCCESS
        assert record.quality_score == 0.9


class TestSEOKnowledgeReadinessEvolution:
    """Test SEO knowledge readiness evolution."""

    def test_initial_readiness(self):
        """Test initial readiness score."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        readiness = evolution.get_current_readiness()
        
        assert readiness.domain_id == "seo"
        assert readiness.overall_readiness == 0.5  # Default initial readiness

    def test_custom_initial_readiness(self):
        """Test custom initial readiness."""
        initial = ReadinessScore(
            domain_id="seo",
            knowledge_readiness=0.8,
            execution_readiness=0.7,
            evidence_readiness=0.6,
            learning_readiness=0.9,
            overall_readiness=0.75,
        )
        
        evolution = SEOKnowledgeReadinessEvolution("seo", initial)
        
        readiness = evolution.get_current_readiness()
        
        assert readiness.overall_readiness == 0.75

    def test_record_successful_execution(self):
        """Test recording successful execution increases readiness."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.record_execution(
            execution_id="exec_001",
            task_id="task",
            result=ExecutionResult.SUCCESS,
            duration_seconds=3600.0,
            quality_score=0.9,
        )
        
        new_readiness = evolution.get_current_readiness()
        
        # Execution readiness should increase
        assert new_readiness.execution_readiness > initial_readiness.execution_readiness

    def test_record_failed_execution(self):
        """Test recording failed execution decreases readiness."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.record_execution(
            execution_id="exec_002",
            task_id="task",
            result=ExecutionResult.FAILURE,
            duration_seconds=3600.0,
            quality_score=0.5,
        )
        
        new_readiness = evolution.get_current_readiness()
        
        # Execution readiness should decrease
        assert new_readiness.execution_readiness < initial_readiness.execution_readiness

    def test_record_partial_success(self):
        """Test recording partial success has moderate impact."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.record_execution(
            execution_id="exec_003",
            task_id="task",
            result=ExecutionResult.PARTIAL_SUCCESS,
            duration_seconds=3600.0,
            quality_score=0.7,
        )
        
        new_readiness = evolution.get_current_readiness()
        
        # Partial success should have small positive impact
        assert new_readiness.execution_readiness >= initial_readiness.execution_readiness

    def test_apply_evidence_impact(self):
        """Test applying evidence impact increases readiness."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.apply_evidence_impact(
            evidence_id="evidence_001",
            concept_id="concept1",
            quality_score=0.9,
            maturity_impact=0.5,
        )
        
        new_readiness = evolution.get_current_readiness()
        
        # Evidence readiness should increase
        assert new_readiness.evidence_readiness > initial_readiness.evidence_readiness

    def test_apply_knowledge_impact_increase(self):
        """Test applying knowledge maturity increase."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.apply_knowledge_impact(
            knowledge_id="knowledge1",
            change_type="maturity_increase",
            previous_maturity=KnowledgeMaturity.DEFINITION,
            new_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        )
        
        new_readiness = evolution.get_current_readiness()
        
        # Knowledge readiness should increase
        assert new_readiness.knowledge_readiness >= initial_readiness.knowledge_readiness

    def test_apply_knowledge_impact_decrease(self):
        """Test applying knowledge maturity decrease."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.apply_knowledge_impact(
            knowledge_id="knowledge1",
            change_type="maturity_decrease",
            previous_maturity=KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS,
            new_maturity=KnowledgeMaturity.DEFINITION,
        )
        
        new_readiness = evolution.get_current_readiness()
        
        # Knowledge readiness should decrease
        assert new_readiness.knowledge_readiness <= initial_readiness.knowledge_readiness

    def test_readiness_decay(self):
        """Test readiness decay over time."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        initial_readiness = evolution.get_current_readiness()
        
        evolution.decay_readiness(days=1)
        
        new_readiness = evolution.get_current_readiness()
        
        # All readiness components should decrease
        assert new_readiness.knowledge_readiness < initial_readiness.knowledge_readiness
        assert new_readiness.execution_readiness < initial_readiness.execution_readiness
        assert new_readiness.evidence_readiness < initial_readiness.evidence_readiness
        assert new_readiness.learning_readiness < initial_readiness.learning_readiness

    def test_get_execution_history(self):
        """Test getting execution history."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        evolution.record_execution(
            execution_id="exec_001",
            task_id="task",
            result=ExecutionResult.SUCCESS,
            duration_seconds=3600.0,
            quality_score=0.9,
        )
        
        history = evolution.get_execution_history()
        
        assert len(history) == 1
        assert history[0].execution_id == "exec_001"

    def test_get_execution_history_limit(self):
        """Test execution history limit."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        for i in range(150):
            evolution.record_execution(
                execution_id=f"exec_{i}",
                task_id="task",
                result=ExecutionResult.SUCCESS,
                duration_seconds=3600.0,
                quality_score=0.9,
            )
        
        history = evolution.get_execution_history(limit=100)
        
        assert len(history) == 100

    def test_get_readiness_trend(self):
        """Test getting readiness trend."""
        evolution = SEOKnowledgeReadinessEvolution("seo")
        
        # Add some executions
        for i in range(5):
            evolution.record_execution(
                execution_id=f"exec_{i}",
                task_id="task",
                result=ExecutionResult.SUCCESS if i % 2 == 0 else ExecutionResult.FAILURE,
                duration_seconds=3600.0,
                quality_score=0.8,
            )
        
        trend = evolution.get_readiness_trend(days=30)
        
        assert "period_days" in trend
        assert "execution_count" in trend
        assert "success_rate" in trend
        assert "current_readiness" in trend


class TestSEOKnowledgeReadinessOrchestrator:
    """Test SEO knowledge readiness orchestrator."""

    def test_record_successful_execution(self):
        """Test recording successful execution through orchestrator."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.record_successful_execution(
            execution_id="exec_001",
            task_id="task",
            duration_seconds=3600.0,
            quality_score=0.9,
        )
        
        assert readiness.domain_id == "seo"
        assert readiness.execution_readiness > 0.5  # Should increase from default

    def test_record_failed_execution(self):
        """Test recording failed execution through orchestrator."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.record_failed_execution(
            execution_id="exec_002",
            task_id="task",
            duration_seconds=3600.0,
            quality_score=0.5,
        )
        
        assert readiness.execution_readiness < 0.5  # Should decrease from default

    def test_record_partial_success(self):
        """Test recording partial success through orchestrator."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.record_partial_success(
            execution_id="exec_003",
            task_id="task",
            duration_seconds=3600.0,
            quality_score=0.7,
        )
        
        assert readiness.execution_readiness >= 0.5  # Should not decrease significantly

    def test_apply_high_quality_evidence(self):
        """Test applying high-quality evidence through orchestrator."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.apply_high_quality_evidence(
            evidence_id="evidence_001",
            concept_id="concept1",
            quality_score=0.9,
            maturity_impact=0.5,
        )
        
        assert readiness.evidence_readiness > 0.5  # Should increase from default

    def test_apply_knowledge_increase(self):
        """Test applying knowledge increase through orchestrator."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.apply_knowledge_increase(
            knowledge_id="knowledge1",
            previous_maturity=KnowledgeMaturity.DEFINITION,
            new_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        )
        
        assert readiness.knowledge_readiness >= 0.5  # Should increase from default

    def test_apply_knowledge_decrease(self):
        """Test applying knowledge decrease through orchestrator."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.apply_knowledge_decrease(
            knowledge_id="knowledge1",
            previous_maturity=KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS,
            new_maturity=KnowledgeMaturity.DEFINITION,
        )
        
        assert readiness.knowledge_readiness <= 0.5  # Should decrease from default

    def test_get_current_readiness(self):
        """Test getting current readiness."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        readiness = orchestrator.get_current_readiness()
        
        assert readiness.domain_id == "seo"

    def test_get_readiness_trend(self):
        """Test getting readiness trend."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        orchestrator.record_successful_execution("exec_1", "task", 3600.0, 0.9)
        
        trend = orchestrator.get_readiness_trend(days=30)
        
        assert "execution_count" in trend
        assert trend["execution_count"] >= 1

    def test_apply_daily_decay(self):
        """Test applying daily decay."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        initial_readiness = orchestrator.get_current_readiness()
        
        orchestrator.apply_daily_decay()
        
        new_readiness = orchestrator.get_current_readiness()
        
        # Readiness should decrease
        assert new_readiness.overall_readiness < initial_readiness.overall_readiness


class TestReadinessEvolutionPipeline:
    """Test complete readiness evolution pipeline."""

    def test_multiple_executions_impact(self):
        """Test impact of multiple executions."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        # Record multiple successful executions
        for i in range(5):
            orchestrator.record_successful_execution(
                execution_id=f"exec_{i}",
                task_id="task",
                duration_seconds=3600.0,
                quality_score=0.9,
            )
        
        readiness = orchestrator.get_current_readiness()
        
        # Execution readiness should be significantly higher
        assert readiness.execution_readiness > 0.7

    def test_mixed_success_failure_impact(self):
        """Test impact of mixed success and failure."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        # Record mixed results
        for i in range(10):
            if i % 3 == 0:
                orchestrator.record_failed_execution(
                    execution_id=f"exec_{i}",
                    task_id="task",
                    duration_seconds=3600.0,
                    quality_score=0.5,
                )
            else:
                orchestrator.record_successful_execution(
                    execution_id=f"exec_{i}",
                    task_id="task",
                    duration_seconds=3600.0,
                    quality_score=0.9,
                )
        
        readiness = orchestrator.get_current_readiness()
        
        # Overall readiness should be moderate
        assert 0.4 < readiness.overall_readiness < 0.8

    def test_evidence_and_execution_combined_impact(self):
        """Test combined impact of evidence and executions."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        # Add successful executions
        orchestrator.record_successful_execution("exec_1", "task", 3600.0, 0.9)
        orchestrator.record_successful_execution("exec_2", "task", 3600.0, 0.9)
        
        # Add high-quality evidence
        orchestrator.apply_high_quality_evidence(
            evidence_id="evidence_1",
            concept_id="concept1",
            quality_score=0.9,
            maturity_impact=0.5,
        )
        
        readiness = orchestrator.get_current_readiness()
        
        # Both execution and evidence readiness should be high
        assert readiness.execution_readiness > 0.5
        assert readiness.evidence_readiness > 0.5

    def test_readiness_trend_calculation(self):
        """Test readiness trend calculation."""
        orchestrator = SEOKnowledgeReadinessOrchestrator("seo")
        
        # Add executions over time
        for i in range(10):
            orchestrator.record_successful_execution(
                execution_id=f"exec_{i}",
                task_id="task",
                duration_seconds=3600.0,
                quality_score=0.8 + (i * 0.01),
            )
        
        trend = orchestrator.get_readiness_trend(days=30)
        
        # Verify trend statistics
        assert trend["execution_count"] == 10
        assert trend["success_rate"] == 1.0  # All successful
        assert trend["average_quality"] > 0.8
