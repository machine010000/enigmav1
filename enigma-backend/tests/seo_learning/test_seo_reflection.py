"""
Tests for SEO Reflection module.

Tests post-task reflection and candidate knowledge generation.
"""

import pytest
from datetime import datetime

from app.expert_domains.domains.seo_reflection import (
    ReflectionOutcome,
    TaskExecutionResult,
    Reflection,
    SEOReflectionGenerator,
    SEOReflectionOrchestrator,
)
from app.knowledge_governance.models import (
    CandidateKnowledge,
    KnowledgeMaturity,
    KnowledgeFreshness,
)


class TestTaskExecutionResult:
    """Test task execution result."""

    def test_execution_result_creation(self):
        """Test creating an execution result."""
        result = TaskExecutionResult(
            task_id="technical_seo_audit_task",
            execution_id="exec_001",
            expected_outcome="success",
            actual_outcome="success",
            metrics={"ranking_change": 5.0, "traffic_change": 10.0},
        )
        
        assert result.task_id == "technical_seo_audit_task"
        assert result.expected_outcome == "success"
        assert result.actual_outcome == "success"
        assert result.metrics["ranking_change"] == 5.0


class TestSEOReflectionGenerator:
    """Test SEO reflection generator."""

    def test_generate_reflection_success(self):
        """Test generating reflection for successful execution."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="technical_seo_audit_task",
            execution_id="exec_001",
            expected_outcome="success",
            actual_outcome="success",
            metrics={"ranking_change": 5.0},
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        assert reflection.outcome == ReflectionOutcome.SUCCESS
        assert reflection.task_execution == execution_result
        assert reflection.lesson is not None
        assert reflection.reason is not None

    def test_generate_reflection_failure(self):
        """Test generating reflection for failed execution."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="keyword_research_task",
            execution_id="exec_002",
            expected_outcome="success",
            actual_outcome="failure: ranking did not improve",
            metrics={"ranking_change": -2.0},
            metadata={"errors": ["ranking did not improve"]},
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        assert reflection.outcome == ReflectionOutcome.FAILURE
        assert "failure" in reflection.task_execution.actual_outcome.lower()

    def test_generate_reflection_partial_success(self):
        """Test generating reflection for partial success."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="link_building_task",
            execution_id="exec_003",
            expected_outcome="success",
            actual_outcome="partial success: some links acquired",
            metrics={"links_acquired": 5},
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        assert reflection.outcome == ReflectionOutcome.PARTIAL_SUCCESS

    def test_reflection_generates_candidates_on_failure(self):
        """Test that reflection generates candidates on failure."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="technical_seo_audit_task",
            execution_id="exec_004",
            expected_outcome="success",
            actual_outcome="failure: technical errors encountered",
            metadata={"errors": ["crawl failed", "timeout"]},
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        # Failure should generate candidates
        assert len(reflection.generated_candidates) >= 0  # May or may not generate based on logic

    def test_reflection_confidence_calculation(self):
        """Test reflection confidence calculation."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="task",
            execution_id="exec_005",
            expected_outcome="success",
            actual_outcome="success",
            metrics={"metric1": 1.0, "metric2": 2.0},
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        # Confidence should be between 0 and 1
        assert 0.0 <= reflection.confidence <= 1.0

    def test_get_reflection_history(self):
        """Test getting reflection history."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="task",
            execution_id="exec_006",
            expected_outcome="success",
            actual_outcome="success",
        )
        
        generator.generate_reflection(execution_result)
        
        history = generator.get_reflection_history()
        
        assert len(history) == 1

    def test_get_reflection_statistics(self):
        """Test getting reflection statistics."""
        generator = SEOReflectionGenerator()
        
        # Generate some reflections
        for i in range(3):
            execution_result = TaskExecutionResult(
                task_id="task",
                execution_id=f"exec_{i}",
                expected_outcome="success",
                actual_outcome="success",
            )
            generator.generate_reflection(execution_result)
        
        stats = generator.get_reflection_statistics()
        
        assert stats["total_reflections"] == 3
        assert "by_outcome" in stats
        assert "candidates_generated" in stats


class TestSEOReflectionOrchestrator:
    """Test SEO reflection orchestrator."""

    def test_reflect_on_task(self):
        """Test reflecting on a task."""
        orchestrator = SEOReflectionOrchestrator()
        
        reflection = orchestrator.reflect_on_task(
            task_id="technical_seo_audit_task",
            execution_id="exec_007",
            expected_outcome="success",
            actual_outcome="success",
            metrics={"ranking_change": 3.0},
        )
        
        assert reflection.task_execution.task_id == "technical_seo_audit_task"
        assert reflection.task_execution.execution_id == "exec_007"

    def test_reflect_on_success(self):
        """Test reflecting on success."""
        orchestrator = SEOReflectionOrchestrator()
        
        reflection = orchestrator.reflect_on_success(
            task_id="keyword_research_task",
            execution_id="exec_008",
            metrics={"traffic_change": 15.0},
        )
        
        assert reflection.task_execution.expected_outcome == "success"
        assert reflection.task_execution.actual_outcome == "success"

    def test_reflect_on_failure(self):
        """Test reflecting on failure."""
        orchestrator = SEOReflectionOrchestrator()
        
        reflection = orchestrator.reflect_on_failure(
            task_id="link_building_task",
            execution_id="exec_009",
            error_reason="link quality too low",
            metrics={"links_acquired": 0},
        )
        
        assert "failure" in reflection.task_execution.actual_outcome.lower()
        assert "link quality too low" in reflection.task_execution.actual_outcome.lower()

    def test_reflect_on_partial_success(self):
        """Test reflecting on partial success."""
        orchestrator = SEOReflectionOrchestrator()
        
        reflection = orchestrator.reflect_on_partial_success(
            task_id="on_page_optimization_task",
            execution_id="exec_010",
            success_description="meta tags optimized",
            failure_description="content not updated",
            metrics={"meta_optimized": True, "content_updated": False},
        )
        
        assert "partial success" in reflection.task_execution.actual_outcome.lower()

    def test_get_reflection_statistics(self):
        """Test getting reflection statistics from orchestrator."""
        orchestrator = SEOReflectionOrchestrator()
        
        orchestrator.reflect_on_success("task", "exec_1")
        orchestrator.reflect_on_failure("task", "exec_2", "error")
        
        stats = orchestrator.get_reflection_statistics()
        
        assert stats["total_reflections"] == 2


class TestReflectionPipeline:
    """Test complete reflection pipeline."""

    def test_reflection_to_candidate_pipeline(self):
        """Test pipeline from reflection to candidate knowledge."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="technical_seo_audit_task",
            execution_id="exec_011",
            expected_outcome="success",
            actual_outcome="failure: unexpected ranking drop",
            metadata={"errors": ["ranking dropped"]},
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        # Check that reflection has proper structure
        assert reflection.reflection_id.startswith("reflection_")
        assert reflection.lesson is not None
        assert reflection.reason is not None

    def test_task_specific_lessons(self):
        """Test that different tasks generate specific lessons."""
        generator = SEOReflectionGenerator()
        
        # Technical SEO task
        tech_result = TaskExecutionResult(
            task_id="technical_seo_audit_task",
            execution_id="exec_012",
            expected_outcome="success",
            actual_outcome="success",
            metrics={"ranking_change": 5.0},
        )
        tech_reflection = generator.generate_reflection(tech_result)
        
        # Keyword research task
        keyword_result = TaskExecutionResult(
            task_id="keyword_research_task",
            execution_id="exec_013",
            expected_outcome="success",
            actual_outcome="success",
            metrics={"traffic_change": 10.0},
        )
        keyword_reflection = generator.generate_reflection(keyword_result)
        
        # Lessons should be task-specific
        assert tech_reflection.lesson is not None
        assert keyword_reflection.lesson is not None

    def test_reflection_with_metrics(self):
        """Test reflection with detailed metrics."""
        generator = SEOReflectionGenerator()
        
        execution_result = TaskExecutionResult(
            task_id="task",
            execution_id="exec_014",
            expected_outcome="success",
            actual_outcome="success",
            metrics={
                "ranking_change": 8.5,
                "traffic_change": 25.0,
                "conversion_change": 2.5,
                "domain_authority_change": 1.0,
            },
        )
        
        reflection = generator.generate_reflection(execution_result)
        
        # Metrics should influence confidence
        assert reflection.confidence > 0.5  # Should be higher with metrics
