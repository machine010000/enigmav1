import pytest

from app.expert_domains.execution import (
    ExecutionStep,
    ExecutionStepType,
    ExecutionTemplate,
    QualityGate,
    ValidationCheckpoint,
    ExecutionTemplateRegistry,
)


class TestExecutionStep:
    """Tests for ExecutionStep."""

    def test_execution_step_creation(self):
        """Test creating an execution step."""
        step = ExecutionStep(
            step_id="step1",
            step_type=ExecutionStepType.ANALYSIS,
            name="Analyze Website",
            description="Analyze website structure",
            order=1,
        )
        assert step.step_id == "step1"
        assert step.step_type == ExecutionStepType.ANALYSIS
        assert step.order == 1

    def test_execution_step_with_requirements(self):
        """Test execution step with requirements."""
        step = ExecutionStep(
            step_id="step1",
            step_type=ExecutionStepType.ANALYSIS,
            name="Analyze Website",
            description="Analyze website structure",
            order=1,
            required_inputs=["website_url"],
            expected_outputs=["analysis_report"],
            required_capabilities=["website_analysis"],
        )
        assert len(step.required_inputs) == 1
        assert len(step.expected_outputs) == 1
        assert len(step.required_capabilities) == 1


class TestExecutionTemplate:
    """Tests for ExecutionTemplate."""

    def test_execution_template_creation(self):
        """Test creating an execution template."""
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
        )
        assert template.template_id == "seo_audit_template"
        assert template.name == "SEO Audit Template"

    def test_execution_template_with_steps(self):
        """Test execution template with steps."""
        step1 = ExecutionStep(
            step_id="step1",
            step_type=ExecutionStepType.ANALYSIS,
            name="Analyze Website",
            description="Analyze website structure",
            order=1,
        )
        step2 = ExecutionStep(
            step_id="step2",
            step_type=ExecutionStepType.EXECUTION,
            name="Generate Report",
            description="Generate audit report",
            order=2,
        )
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
            execution_steps=[step1, step2],
        )
        assert len(template.execution_steps) == 2


class TestQualityGate:
    """Tests for QualityGate."""

    def test_quality_gate_creation(self):
        """Test creating a quality gate."""
        gate = QualityGate(
            gate_id="gate1",
            name="Quality Check",
            description="Quality gate for execution",
            gate_type="threshold",
            threshold_value=0.8,
        )
        assert gate.gate_id == "gate1"
        assert gate.threshold_value == 0.8


class TestValidationCheckpoint:
    """Tests for ValidationCheckpoint."""

    def test_validation_checkpoint_creation(self):
        """Test creating a validation checkpoint."""
        checkpoint = ValidationCheckpoint(
            checkpoint_id="cp1",
            name="Input Validation",
            description="Validate input data",
            checkpoint_type="input",
            validation_rules=["not_empty", "valid_url"],
        )
        assert checkpoint.checkpoint_id == "cp1"
        assert len(checkpoint.validation_rules) == 2


class TestExecutionTemplateRegistry:
    """Tests for ExecutionTemplateRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ExecutionTemplateRegistry()
        assert registry.list_all() == []

    def test_register_template(self):
        """Test registering a template."""
        registry = ExecutionTemplateRegistry()
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
        )
        result = registry.register(template)
        assert result is True
        assert "seo_audit_template" in [t.template_id for t in registry.list_all()]

    def test_register_duplicate_template(self):
        """Test that registering a duplicate template fails."""
        registry = ExecutionTemplateRegistry()
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
        )
        registry.register(template)
        result = registry.register(template)
        assert result is False

    def test_get_template(self):
        """Test retrieving a template."""
        registry = ExecutionTemplateRegistry()
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
        )
        registry.register(template)
        retrieved = registry.get("seo_audit_template")
        assert retrieved is not None
        assert retrieved.template_id == "seo_audit_template"

    def test_list_by_task(self):
        """Test listing templates by task."""
        registry = ExecutionTemplateRegistry()
        template1 = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
            supported_tasks=["seo_audit"],
        )
        template2 = ExecutionTemplate(
            template_id="content_template",
            name="Content Template",
            description="Template for content execution",
            supported_tasks=["content_creation"],
        )
        registry.register(template1)
        registry.register(template2)
        seo_templates = registry.list_by_task("seo_audit")
        assert len(seo_templates) == 1
        assert seo_templates[0].template_id == "seo_audit_template"

    def test_validate_step_order_success(self):
        """Test step order validation with proper ordering."""
        registry = ExecutionTemplateRegistry()
        step1 = ExecutionStep(
            step_id="step1",
            step_type=ExecutionStepType.ANALYSIS,
            name="Analyze Website",
            description="Analyze website structure",
            order=1,
        )
        step2 = ExecutionStep(
            step_id="step2",
            step_type=ExecutionStepType.EXECUTION,
            name="Generate Report",
            description="Generate audit report",
            order=2,
        )
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
            execution_steps=[step1, step2],
        )
        registry.register(template)
        validation = registry.validate_step_order("seo_audit_template")
        assert validation["valid"] is True
        assert validation["steps_ordered"] is True
        assert validation["no_duplicates"] is True

    def test_validate_step_order_failure(self):
        """Test step order validation with improper ordering."""
        registry = ExecutionTemplateRegistry()
        step1 = ExecutionStep(
            step_id="step1",
            step_type=ExecutionStepType.ANALYSIS,
            name="Analyze Website",
            description="Analyze website structure",
            order=2,
        )
        step2 = ExecutionStep(
            step_id="step2",
            step_type=ExecutionStepType.EXECUTION,
            name="Generate Report",
            description="Generate audit report",
            order=1,
        )
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
            execution_steps=[step1, step2],
        )
        registry.register(template)
        validation = registry.validate_step_order("seo_audit_template")
        assert validation["valid"] is False
        assert validation["steps_ordered"] is False

    def test_get_required_capabilities(self):
        """Test getting required capabilities for a template."""
        registry = ExecutionTemplateRegistry()
        step1 = ExecutionStep(
            step_id="step1",
            step_type=ExecutionStepType.ANALYSIS,
            name="Analyze Website",
            description="Analyze website structure",
            order=1,
            required_capabilities=["website_analysis"],
        )
        step2 = ExecutionStep(
            step_id="step2",
            step_type=ExecutionStepType.EXECUTION,
            name="Generate Report",
            description="Generate audit report",
            order=2,
            required_capabilities=["report_generation"],
        )
        template = ExecutionTemplate(
            template_id="seo_audit_template",
            name="SEO Audit Template",
            description="Template for SEO audit execution",
            execution_steps=[step1, step2],
            required_capabilities=["seo_audit"],
        )
        registry.register(template)
        capabilities = registry.get_required_capabilities("seo_audit_template")
        assert "website_analysis" in capabilities
        assert "report_generation" in capabilities
        assert "seo_audit" in capabilities
