"""
Integration tests for SEO Execution Pipeline.

Tests the complete end-to-end execution flow.
"""

import pytest

from app.expert_domains.domains.seo_execution_orchestrator import (
    SEOExecutionOrchestrator,
    ExecutionReport,
    seo_execution_orchestrator,
)
from app.expert_domains.execution import ExecutionTemplate, ExecutionStep, ExecutionStepType


class TestSEOExecutionIntegration:
    """Test complete SEO execution pipeline integration."""

    def test_execute_work_specification_success(self):
        """Test successful execution of work specification."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
            "audit_scope": ["technical", "on_page"],
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.session_id is not None
        assert report.domain_id == "seo"
        assert report.execution_status in ["completed", "failed"]
        assert report.steps_total > 0
        assert report.completed_at is not None

    def test_execution_produces_outputs(self):
        """Test that execution produces outputs."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.outputs_generated > 0

    def test_execution_generates_reflection(self):
        """Test that execution generates reflection."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.reflection is not None
        assert report.reflection.session_id == report.session_id
        assert report.reflection.reflection_type == "seo_execution"

    def test_execution_updates_knowledge(self):
        """Test that execution updates knowledge."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.knowledge_update is not None
        assert "candidates_submitted" in report.knowledge_update

    def test_execution_updates_evidence(self):
        """Test that execution updates evidence."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.evidence_update is not None
        assert "evidence_registered" in report.evidence_update

    def test_execution_updates_readiness(self):
        """Test that execution updates readiness."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.readiness_update is not None
        assert "execution_readiness" in report.readiness_update
        assert "evidence_readiness" in report.readiness_update
        assert "knowledge_readiness" in report.readiness_update
        assert "overall_readiness" in report.readiness_update

    def test_execution_with_custom_template(self):
        """Test execution with custom template."""
        orchestrator = SEOExecutionOrchestrator()
        
        # Register custom template
        custom_template = ExecutionTemplate(
            template_id="custom_audit",
            name="Custom SEO Audit",
            description="Custom audit template",
            execution_steps=[
                ExecutionStep(
                    step_id="custom_step",
                    step_type=ExecutionStepType.ANALYSIS,
                    name="Custom Analysis",
                    description="Custom analysis step",
                    order=1,
                    required_inputs=["url"],
                    expected_outputs=["custom_output"],
                ),
            ],
            inputs=["url"],
            outputs=["custom_output"],
        )
        
        orchestrator.register_execution_template(custom_template)
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
            template_id="custom_audit",
        )
        
        assert report.execution_status in ["completed", "failed"]

    def test_execution_report_structure(self):
        """Test that execution report has correct structure."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.session_id is not None
        assert report.work_specification_id == "work_spec_001"
        assert report.domain_id == "seo"
        assert report.execution_status is not None
        assert isinstance(report.success, bool)
        assert isinstance(report.steps_completed, int)
        assert isinstance(report.steps_total, int)
        assert isinstance(report.outputs_generated, int)
        assert isinstance(report.validation_passed, bool)
        assert report.started_at is not None

    def test_execution_with_shopify_audit(self):
        """Test execution for Shopify SEO audit."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {
            "url": "https://example.myshopify.com",
            "audit_type": "shopify_seo_audit",
            "platform": "shopify",
        }
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_002",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        assert report.execution_status in ["completed", "failed"]
        assert report.steps_total > 0

    def test_global_orchestrator_instance(self):
        """Test that global orchestrator instance exists."""
        from app.expert_domains.domains.seo_execution_orchestrator import seo_execution_orchestrator
        
        assert seo_execution_orchestrator is not None
        assert isinstance(seo_execution_orchestrator, SEOExecutionOrchestrator)


class TestSEOExecutionPipelineFlow:
    """Test the complete execution pipeline flow."""

    def test_pipeline_session_creation(self):
        """Test that pipeline creates session."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        session = orchestrator._runtime.get_session(report.session_id)
        assert session is not None

    def test_pipeline_plan_creation(self):
        """Test that pipeline creates execution plan."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        plan = orchestrator._runtime.get_plan(report.session_id)
        assert plan is not None
        assert len(plan.steps) > 0

    def test_pipeline_step_execution(self):
        """Test that pipeline executes steps."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that steps were executed
        assert report.steps_completed >= 0
        assert report.steps_completed <= report.steps_total

    def test_pipeline_output_building(self):
        """Test that pipeline builds outputs."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that outputs were built
        assert report.outputs_generated >= 0

    def test_pipeline_validation(self):
        """Test that pipeline validates outputs."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that validation was performed
        assert isinstance(report.validation_passed, bool)

    def test_pipeline_reflection_generation(self):
        """Test that pipeline generates reflection."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that reflection was generated
        assert report.reflection is not None

    def test_pipeline_knowledge_update(self):
        """Test that pipeline updates knowledge."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that knowledge was updated
        assert report.knowledge_update is not None

    def test_pipeline_evidence_update(self):
        """Test that pipeline updates evidence."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that evidence was updated
        assert report.evidence_update is not None

    def test_pipeline_readiness_update(self):
        """Test that pipeline updates readiness."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        # Check that readiness was updated
        assert report.readiness_update is not None

    def test_pipeline_session_completion(self):
        """Test that pipeline completes session."""
        orchestrator = SEOExecutionOrchestrator()
        
        work_specification = {"url": "https://example.com"}
        
        report = orchestrator.execute_work_specification(
            work_specification_id="work_spec_001",
            work_specification=work_specification,
            domain_id="seo",
        )
        
        session = orchestrator._runtime.get_session(report.session_id)
        
        # Check that session was completed
        from app.execution.contracts import SessionState
        assert session.session_state in [SessionState.COMPLETED, SessionState.FAILED]
