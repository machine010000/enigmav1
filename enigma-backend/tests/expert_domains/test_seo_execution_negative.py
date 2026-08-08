"""
Negative tests for SEO Execution Pipeline.

Tests error handling and edge cases.
"""

import pytest

from app.expert_domains.domains.seo_execution_orchestrator import (
    SEOExecutionOrchestrator,
    ExecutionReport,
)
from app.expert_domains.execution import ExecutionTemplate, ExecutionStep, ExecutionStepType


class TestSEOExecutionNegative:
    """Test negative cases for SEO execution."""

    def test_execution_with_missing_url(self):
        """Test execution with missing URL in work specification."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            # Missing URL
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Should still complete but may have errors
        assert report.execution_status in ["completed", "failed"]
        # If it failed, should have errors
        if report.execution_status == "failed":
            assert len(report.errors) > 0

    def test_execution_with_invalid_domain(self):
        """Test execution with invalid domain ID."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="invalid_domain",  # Invalid domain
        )
        
        # Should still complete but may have issues
        assert report.execution_status in ["completed", "failed"]

    def test_execution_with_nonexistent_template(self):
        """Test execution with nonexistent template ID."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
            template_id="nonexistent_template",  # Nonexistent template
        )
        
        # Should fall back to default template
        assert report.execution_status in ["completed", "failed"]

    def test_execution_with_empty_work_specification(self):
        """Test execution with empty work specification."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {}  # Empty
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Should still complete with default template
        assert report.execution_status in ["completed", "failed"]

    def test_execution_with_invalid_url_format(self):
        """Test execution with invalid URL format."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "not-a-valid-url",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Should still complete (workers handle invalid URLs gracefully)
        assert report.execution_status in ["completed", "failed"]


class TestSEOWorkersNegative:
    """Test negative cases for SEO workers."""

    def test_worker_with_empty_inputs(self):
        """Test worker execution with empty inputs."""
        from app.expert_domains.domains.seo_workers import SEOTechnicalAuditWorker
        from app.execution.executor import ExecutionContext
        
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={},  # Empty inputs
        )
        
        result = worker.execute(context)
        
        # Should still succeed with defaults
        assert result.success is True
        assert len(result.outputs) > 0

    def test_worker_with_missing_required_field(self):
        """Test worker with missing required field in inputs."""
        from app.expert_domains.domains.seo_workers import SEOKeywordResearchWorker
        from app.execution.executor import ExecutionContext
        
        worker = SEOKeywordResearchWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={},  # Missing business_domain
        )
        
        result = worker.execute(context)
        
        # Should still succeed with defaults
        assert result.success is True


class TestSEOOutputsNegative:
    """Test negative cases for SEO output builders."""

    def test_output_builder_with_empty_result(self):
        """Test output builder with empty execution result."""
        from app.expert_domains.domains.seo_outputs import SEOAuditReportBuilder
        from app.execution.contracts import ExecutionStep, StepType
        
        builder = SEOAuditReportBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate Report",
            description="Generate report",
        )
        
        execution_result = {}  # Empty
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        # Should still produce report structure
        assert len(outputs) >= 1

    def test_output_builder_with_none_content(self):
        """Test output builder with None content."""
        from app.expert_domains.domains.seo_outputs import SEOEvidenceBuilder
        from app.execution.contracts import ExecutionStep, StepType
        
        builder = SEOEvidenceBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Collect Evidence",
            description="Collect evidence",
        )
        
        execution_result = {"evidence": None}
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        # Should handle None gracefully
        assert len(outputs) == 0


class TestSEOReflectionNegative:
    """Test negative cases for SEO reflection generator."""

    def test_reflection_with_empty_results(self):
        """Test reflection generation with empty execution results."""
        from app.expert_domains.domains.seo_reflection_generator import SEOReflectionGenerator
        from app.execution.contracts import ExecutionPlan, ExecutionStep, StepState, StepType
        
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Test Step",
            description="Test step",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        execution_results = {}  # Empty
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        # Should still generate reflection
        assert reflection.session_id == "session_001"
        assert reflection.reflection_type == "seo_execution"

    def test_reflection_with_all_failed_steps(self):
        """Test reflection with all steps failed."""
        from app.expert_domains.domains.seo_reflection_generator import SEOReflectionGenerator
        from app.execution.contracts import ExecutionPlan, ExecutionStep, StepState, StepType
        
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Test Step",
            description="Test step",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        execution_results = {
            "step_states": {"step_001": StepState.FAILED},
            "outputs": {},
            "errors": {"step_001": "Test error"},
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        # Should generate reflection with failure analysis
        assert len(reflection.what_could_be_improved) > 0
        assert len(reflection.action_items) > 0


class TestSEOKnowledgeIntegrationNegative:
    """Test negative cases for SEO knowledge integration."""

    def test_knowledge_integration_without_governance_service(self):
        """Test knowledge integration without governance service."""
        from app.expert_domains.domains.seo_knowledge_integration import SEOKnowledgeIntegration
        from app.execution.contracts import ExecutionOutput, OutputType
        
        integration = SEOKnowledgeIntegration()  # No governance service set
        
        outputs = [ExecutionOutput(
            output_id="output_001",
            step_id="step_001",
            session_id="session_001",
            output_type=OutputType.ARTIFACT,
            name="Test Output",
            description="Test output",
            content={"candidate_knowledge": []},
        )]
        
        result = integration.update_knowledge_from_outputs(
            outputs,
            "session_001",
            "seo",
        )
        
        # Should fail gracefully
        assert result.success is False
        assert len(result.errors) > 0

    def test_knowledge_integration_with_empty_outputs(self):
        """Test knowledge integration with empty outputs."""
        from app.expert_domains.domains.seo_knowledge_integration import SEOKnowledgeIntegration
        
        integration = SEOKnowledgeIntegration()
        
        result = integration.update_knowledge_from_outputs(
            [],  # Empty outputs
            "session_001",
            "seo",
        )
        
        # Should fail without governance service, but with no candidates
        assert result.success is False
        assert result.candidates_submitted == 0


class TestSEOEvidenceIntegrationNegative:
    """Test negative cases for SEO evidence integration."""

    def test_evidence_integration_with_empty_outputs(self):
        """Test evidence integration with empty outputs."""
        from app.expert_domains.domains.seo_knowledge_integration import SEOEvidenceIntegration
        
        integration = SEOEvidenceIntegration()
        
        result = integration.register_evidence(
            [],  # Empty outputs
            "session_001",
            "seo",
        )
        
        # Should succeed but with no evidence
        assert result["success"] is True
        assert result["evidence_registered"] == 0

    def test_evidence_integration_with_non_evidence_outputs(self):
        """Test evidence integration with non-evidence outputs."""
        from app.expert_domains.domains.seo_knowledge_integration import SEOEvidenceIntegration
        from app.execution.contracts import ExecutionOutput, OutputType
        
        integration = SEOEvidenceIntegration()
        
        outputs = [ExecutionOutput(
            output_id="output_001",
            step_id="step_001",
            session_id="session_001",
            output_type=OutputType.REPORT,  # Not evidence
            name="Test Report",
            description="Test report",
            content={},
        )]
        
        result = integration.register_evidence(
            outputs,
            "session_001",
            "seo",
        )
        
        # Should succeed but with no evidence registered
        assert result["success"] is True
        assert result["evidence_registered"] == 0


class TestSEOReadinessIntegrationNegative:
    """Test negative cases for SEO readiness integration."""

    def test_readiness_integration_with_failure(self):
        """Test readiness integration with execution failure."""
        from app.expert_domains.domains.seo_knowledge_integration import SEOReadinessIntegration
        
        integration = SEOReadinessIntegration()
        
        result = integration.update_readiness(
            session_id="session_001",
            domain_id="seo",
            execution_success=False,  # Failed execution
            quality_score=0.3,  # Low quality
            evidence_collected=0,
            knowledge_generated=0,
        )
        
        # Should still calculate readiness
        assert "execution_readiness" in result
        assert "overall_readiness" in result
        # Execution readiness should be lower for failed execution
        assert result["execution_readiness"] < 0.5

    def test_readiness_integration_with_zero_metrics(self):
        """Test readiness integration with zero metrics."""
        from app.expert_domains.domains.seo_knowledge_integration import SEOReadinessIntegration
        
        integration = SEOReadinessIntegration()
        
        result = integration.update_readiness(
            session_id="session_001",
            domain_id="seo",
            execution_success=True,
            quality_score=0.0,  # Zero quality
            evidence_collected=0,  # No evidence
            knowledge_generated=0,  # No knowledge
        )
        
        # Should still calculate readiness
        assert "execution_readiness" in result
        assert "evidence_readiness" in result
        assert "knowledge_readiness" in result
        assert "overall_readiness" in result
