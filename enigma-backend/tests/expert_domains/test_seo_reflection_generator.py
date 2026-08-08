"""
Tests for SEO Reflection Generator module.

Tests SEO-specific reflection generation.
"""

import pytest

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
)
from app.expert_domains.domains.seo_reflection_generator import (
    SEOReflectionGenerator,
    SEOReflectionContext,
)


class TestSEOReflectionGenerator:
    """Test SEOReflectionGenerator."""

    def test_generate_seo_reflection(self):
        """Test generating SEO reflection."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "step_states": {"step_001": StepState.DONE},
            "outputs": {},
            "errors": {},
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert reflection.session_id == "session_001"
        assert reflection.reflection_type == "seo_execution"
        assert len(reflection.what_went_well) > 0

    def test_reflection_includes_missing_knowledge(self):
        """Test that reflection includes missing knowledge."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "step_states": {"step_001": StepState.DONE},
            "outputs": {},
            "errors": {},
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert "missing_knowledge" in reflection.metadata
        missing_knowledge = reflection.metadata["missing_knowledge"]
        assert isinstance(missing_knowledge, list)

    def test_reflection_includes_missing_evidence(self):
        """Test that reflection includes missing evidence."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "step_states": {"step_001": StepState.DONE},
            "outputs": {},
            "errors": {},
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert "missing_evidence" in reflection.metadata
        missing_evidence = reflection.metadata["missing_evidence"]
        assert isinstance(missing_evidence, list)

    def test_reflection_includes_suggested_learning(self):
        """Test that reflection includes suggested learning."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "step_states": {"step_001": StepState.DONE},
            "outputs": {},
            "errors": {},
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert "suggested_learning" in reflection.metadata
        suggested_learning = reflection.metadata["suggested_learning"]
        assert isinstance(suggested_learning, list)

    def test_reflection_with_failures(self):
        """Test reflection with execution failures."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "errors": {"step_001": "Execution failed"},
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert len(reflection.what_could_be_improved) > 0
        assert len(reflection.action_items) > 0

    def test_reflection_subject_includes_audit_type(self):
        """Test that reflection subject includes audit type."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "step_states": {"step_001": StepState.DONE},
            "outputs": {},
            "errors": {},
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert "technical_seo_audit" in reflection.subject

    def test_reflection_metadata_includes_url(self):
        """Test that reflection metadata includes URL."""
        generator = SEOReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Analysis",
            description="Technical SEO analysis",
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
            "step_states": {"step_001": StepState.DONE},
            "outputs": {},
            "errors": {},
            "url": "https://example.com",
            "audit_type": "technical_seo_audit",
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert reflection.metadata.get("url") == "https://example.com"


class TestSEOReflectionContext:
    """Test SEOReflectionContext."""

    def test_create_reflection_context(self):
        """Test creating SEO reflection context."""
        context = SEOReflectionContext(
            session_id="session_001",
            plan=None,  # Would be ExecutionPlan
            execution_results={},
            step_states={},
            url="https://example.com",
            audit_type="technical_seo_audit",
        )
        
        assert context.session_id == "session_001"
        assert context.url == "https://example.com"
        assert context.audit_type == "technical_seo_audit"

    def test_reflection_context_with_outputs(self):
        """Test reflection context with outputs."""
        context = SEOReflectionContext(
            session_id="session_001",
            plan=None,
            execution_results={},
            step_states={},
            outputs={"step_001": []},
        )
        
        assert "step_001" in context.outputs
