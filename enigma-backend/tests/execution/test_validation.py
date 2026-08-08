"""
Tests for Execution Validation module.

Tests validation rules, quality gates, and validation results.
"""

import pytest

from app.execution.contracts import (
    ExecutionStep,
    StepState,
    StepType,
    ExecutionOutput,
    OutputType,
    ValidationResult,
    ValidationStatus,
    QualityGate,
)
from app.execution.validation import (
    BaseValidator,
    RuleBasedValidator,
    ValidationRule,
    CallbackValidator,
)


class TestValidationRule:
    """Test ValidationRule dataclass."""

    def test_create_validation_rule(self):
        """Test creating a validation rule."""
        def check_function(outputs, context):
            return len(outputs) > 0
        
        rule = ValidationRule(
            rule_id="rule_001",
            name="Output Check",
            description="Check that outputs exist",
            check_function=check_function,
            error_message="No outputs generated",
            severity="error",
            required=True,
        )
        
        assert rule.rule_id == "rule_001"
        assert rule.required is True


class TestBaseValidator:
    """Test BaseValidator."""

    def test_register_rule(self):
        """Test registering a validation rule."""
        validator = BaseValidator()
        
        def check_function(outputs, context):
            return True
        
        rule = ValidationRule(
            rule_id="rule_001",
            name="Test Rule",
            description="Test rule",
            check_function=check_function,
            error_message="Test error",
        )
        
        validator.register_rule("task", rule)
        
        assert "task" in validator._rules
        assert len(validator._rules["task"]) == 1

    def test_validate_step_with_expected_outputs(self):
        """Test validating step with expected outputs."""
        validator = BaseValidator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
            expected_outputs=["output_1", "output_2"],
        )
        
        outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="output_1",
                description="First output",
            ),
            ExecutionOutput(
                output_id="output_002",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="output_2",
                description="Second output",
            ),
        ]
        
        result = validator.validate_step(step, outputs, {"session_id": "session_001"})
        
        # Should pass or have warnings due to output completeness check
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]
        assert result.checks_passed > 0

    def test_validate_step_missing_expected_output(self):
        """Test validating step with missing expected output."""
        validator = BaseValidator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
            expected_outputs=["output_1", "output_2"],
        )
        
        outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="output_1",
                description="First output",
            ),
        ]
        
        result = validator.validate_step(step, outputs, {"session_id": "session_001"})
        
        assert result.status == ValidationStatus.FAILED
        assert len(result.validation_errors) > 0

    def test_validate_step_with_empty_outputs(self):
        """Test validating step with empty outputs."""
        validator = BaseValidator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = []
        
        result = validator.validate_step(step, outputs, {"session_id": "session_001"})
        
        assert result.status == ValidationStatus.FAILED

    def test_validate_step_with_custom_rule(self):
        """Test validating step with custom rule."""
        validator = BaseValidator()
        
        def custom_check(outputs, context):
            return all(o.content is not None for o in outputs)
        
        rule = ValidationRule(
            rule_id="rule_001",
            name="Content Check",
            description="Check that all outputs have content",
            check_function=custom_check,
            error_message="Output has no content",
            required=True,
        )
        
        validator.register_rule("task", rule)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="Output 1",
                description="First output",
                content={"data": "value"},
            )
        ]
        
        result = validator.validate_step(step, outputs, {"session_id": "session_001"})
        
        assert result.status == ValidationStatus.PASSED

    def test_validate_quality_gate(self):
        """Test validating a quality gate."""
        validator = BaseValidator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Deliverable 1",
            description="First deliverable",
        )
        
        gate = QualityGate(
            gate_id="gate_001",
            step_id="step_001",
            gate_name="Quality Check",
            description="Quality gate for deliverable",
            criteria=["criterion_1", "criterion_2"],
            threshold=None,  # No threshold for this test
            required=True,
        )
        
        outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="criterion_1",
                description="First criterion",
            ),
            ExecutionOutput(
                output_id="output_002",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="criterion_2",
                description="Second criterion",
            )
        ]
        
        result = validator.validate_quality_gate(step, outputs, gate, {"session_id": "session_001"})
        
        # With both criteria met and no threshold, should pass
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]

    def test_validate_quality_gate_with_threshold(self):
        """Test validating quality gate with threshold."""
        validator = BaseValidator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Deliverable 1",
            description="First deliverable",
        )
        
        gate = QualityGate(
            gate_id="gate_001",
            step_id="step_001",
            gate_name="Quality Check",
            description="Quality gate for deliverable",
            criteria=["criterion_1", "criterion_2"],
            threshold=0.8,
            required=True,
        )
        
        outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="criterion_1",
                description="First criterion",
            )
        ]
        
        result = validator.validate_quality_gate(step, outputs, gate, {"session_id": "session_001"})
        
        # Should fail threshold (50% pass rate < 80% threshold)
        assert result.status == ValidationStatus.FAILED


class TestRuleBasedValidator:
    """Test RuleBasedValidator."""

    def test_register_criterion_validator(self):
        """Test registering a criterion validator."""
        validator = RuleBasedValidator()
        
        def criterion_validator(criterion, outputs, context):
            return criterion in [o.name for o in outputs]
        
        validator.register_criterion_validator("custom", criterion_validator)
        
        assert "custom" in validator._criterion_validators

    def test_validate_with_custom_criterion(self):
        """Test validation with custom criterion validator."""
        validator = RuleBasedValidator()
        
        def custom_validator(criterion, outputs, context):
            return criterion.lower() in [o.name.lower() for o in outputs]
        
        validator.register_criterion_validator("custom", custom_validator)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="Custom Output",
                description="Custom output",
            )
        ]
        
        result = validator.validate_quality_gate(
            step,
            outputs,
            QualityGate(
                gate_id="gate_001",
                step_id="step_001",
                gate_name="Custom Gate",
                description="Custom quality gate",
                criteria=["custom output"],
                required=True,
            ),
            {"session_id": "session_001"},
        )
        
        assert result.status == ValidationStatus.PASSED


class TestCallbackValidator:
    """Test CallbackValidator."""

    def test_callback_validator(self):
        """Test callback validator."""
        def callback(step, outputs, context):
            return ValidationResult(
                validation_id="validation_001",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                status=ValidationStatus.PASSED,
                checks_passed=1,
                checks_total=1,
            )
        
        validator = CallbackValidator(callback)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        result = validator.validate_step(step, [], {"session_id": "session_001"})
        
        assert result.status == ValidationStatus.PASSED
