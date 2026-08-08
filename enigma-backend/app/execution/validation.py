from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.execution.contracts import (
    ExecutionStep,
    ExecutionOutput,
    ValidationResult,
    ValidationStatus,
    QualityGate,
    ExecutionValidator,
)


@dataclass
class ValidationRule:
    """A single validation rule."""
    rule_id: str
    name: str
    description: str
    check_function: Callable[[List[ExecutionOutput], Dict[str, Any]], bool]
    error_message: str
    severity: str = "error"  # error, warning, info
    required: bool = True


class BaseValidator:
    """
    Base implementation of Execution Validator.
    
    This validator validates execution steps based on:
    - Expected outputs
    - Output completeness
    - Output quality
    - Custom validation rules
    """

    def __init__(self) -> None:
        self._rules: Dict[str, List[ValidationRule]] = {}  # step_type -> rules

    def register_rule(
        self,
        step_type: str,
        rule: ValidationRule,
    ) -> None:
        """Register a validation rule for a step type."""
        if step_type not in self._rules:
            self._rules[step_type] = []
        self._rules[step_type].append(rule)

    def validate_step(
        self,
        step: ExecutionStep,
        outputs: List[ExecutionOutput],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate an execution step.
        
        Args:
            step: The step to validate
            outputs: Outputs from the step execution
            context: Additional context
            
        Returns:
            ValidationResult with validation status and details
        """
        validation_id = f"validation_{step.step_id}"
        errors = []
        warnings = []
        checks_passed = 0
        checks_total = 0
        
        # Validate expected outputs
        output_validation = self._validate_expected_outputs(step, outputs)
        checks_total += output_validation["total"]
        checks_passed += output_validation["passed"]
        errors.extend(output_validation["errors"])
        warnings.extend(output_validation["warnings"])
        
        # Validate output completeness
        completeness_validation = self._validate_output_completeness(step, outputs)
        checks_total += completeness_validation["total"]
        checks_passed += completeness_validation["passed"]
        errors.extend(completeness_validation["errors"])
        warnings.extend(completeness_validation["warnings"])
        
        # Apply custom rules
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        custom_rules = self._rules.get(step_type_str, [])
        for rule in custom_rules:
            checks_total += 1
            try:
                if rule.check_function(outputs, context):
                    checks_passed += 1
                else:
                    if rule.required:
                        errors.append(rule.error_message)
                    else:
                        warnings.append(rule.error_message)
            except Exception as e:
                if rule.required:
                    errors.append(f"Rule '{rule.name}' failed with exception: {str(e)}")
                else:
                    warnings.append(f"Rule '{rule.name}' failed with exception: {str(e)}")
        
        # Determine overall status
        if errors:
            status = ValidationStatus.FAILED
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED
        
        return ValidationResult(
            validation_id=validation_id,
            step_id=step.step_id,
            session_id=context.get("session_id", ""),
            status=status,
            checks_passed=checks_passed,
            checks_total=checks_total,
            validation_errors=errors,
            validation_warnings=warnings,
            validated_at=datetime.utcnow(),
            metadata={
                "step_type": step_type_str,
                "output_count": len(outputs),
            },
        )

    def _validate_expected_outputs(
        self,
        step: ExecutionStep,
        outputs: List[ExecutionOutput],
    ) -> Dict[str, Any]:
        """Validate that expected outputs are present."""
        errors = []
        warnings = []
        passed = 0
        total = len(step.expected_outputs)
        
        if total == 0:
            return {"passed": 1, "total": 1, "errors": [], "warnings": []}
        
        output_names = {output.name for output in outputs}
        
        for expected_output in step.expected_outputs:
            if expected_output in output_names:
                passed += 1
            else:
                errors.append(f"Expected output '{expected_output}' not found")
        
        return {
            "passed": passed,
            "total": total,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_output_completeness(
        self,
        step: ExecutionStep,
        outputs: List[ExecutionOutput],
    ) -> Dict[str, Any]:
        """Validate output completeness."""
        errors = []
        warnings = []
        passed = 0
        total = 1  # Single check for completeness
        
        # Check if outputs have content
        empty_outputs = [o for o in outputs if o.content is None]
        
        if not outputs:
            errors.append("No outputs generated")
        elif empty_outputs:
            warnings.append(f"{len(empty_outputs)} outputs have no content")
        else:
            passed = 1
        
        return {
            "passed": passed,
            "total": total,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_quality_gate(
        self,
        step: ExecutionStep,
        outputs: List[ExecutionOutput],
        gate: QualityGate,
        context: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate a quality gate.
        
        Args:
            step: The step to validate
            outputs: Outputs from the step execution
            gate: The quality gate to validate
            context: Additional context
            
        Returns:
            ValidationResult for the quality gate
        """
        validation_id = f"quality_gate_{gate.gate_id}"
        errors = []
        warnings = []
        checks_passed = 0
        checks_total = len(gate.criteria)
        
        # Validate each criterion
        for criterion in gate.criteria:
            checks_total += 1
            if self._validate_criterion(criterion, outputs, context):
                checks_passed += 1
            else:
                if gate.required:
                    errors.append(f"Quality gate criterion failed: {criterion}")
                else:
                    warnings.append(f"Quality gate criterion failed: {criterion}")
        
        # Check threshold if specified
        if gate.threshold is not None:
            checks_total += 1
            pass_rate = checks_passed / checks_total if checks_total > 0 else 0
            if pass_rate >= gate.threshold:
                checks_passed += 1
            else:
                if gate.required:
                    errors.append(f"Quality gate threshold not met: {pass_rate:.2%} < {gate.threshold:.2%}")
                else:
                    warnings.append(f"Quality gate threshold not met: {pass_rate:.2%} < {gate.threshold:.2%}")
        
        # Determine status
        if errors:
            status = ValidationStatus.FAILED
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED
        
        return ValidationResult(
            validation_id=validation_id,
            step_id=step.step_id,
            session_id=context.get("session_id", ""),
            status=status,
            checks_passed=checks_passed,
            checks_total=checks_total,
            validation_errors=errors,
            validation_warnings=warnings,
            validated_at=datetime.utcnow(),
            metadata={
                "gate_id": gate.gate_id,
                "gate_name": gate.gate_name,
                "required": gate.required,
            },
        )

    def _validate_criterion(
        self,
        criterion: str,
        outputs: List[ExecutionOutput],
        context: Dict[str, Any],
    ) -> bool:
        """Validate a single criterion."""
        # Default implementation: check if criterion is in output names
        output_names = {output.name for output in outputs}
        return criterion in output_names


class RuleBasedValidator(BaseValidator):
    """
    Validator that uses custom validation rules.
    
    This validator allows domain-specific validation rules
    to be registered and applied during validation.
    """

    def __init__(self) -> None:
        super().__init__()
        self._criterion_validators: Dict[str, Callable[[str, List[ExecutionOutput], Dict[str, Any]], bool]] = {}

    def register_criterion_validator(
        self,
        criterion_name: str,
        validator: Callable[[str, List[ExecutionOutput], Dict[str, Any]], bool],
    ) -> None:
        """Register a custom criterion validator."""
        self._criterion_validators[criterion_name] = validator

    def _validate_criterion(
        self,
        criterion: str,
        outputs: List[ExecutionOutput],
        context: Dict[str, Any],
    ) -> bool:
        """Validate a criterion using registered validators."""
        # Try custom validator first
        for criterion_name, validator in self._criterion_validators.items():
            if criterion_name in criterion.lower():
                return validator(criterion, outputs, context)
        
        # Fall back to default
        return super()._validate_criterion(criterion, outputs, context)


class CallbackValidator:
    """
    Validator that uses a callback function for validation.
    
    This allows custom validation logic to be injected without
    creating a full validator class.
    """

    def __init__(
        self,
        validate_callback: Callable[
            [ExecutionStep, List[ExecutionOutput], Dict[str, Any]],
            ValidationResult,
        ],
    ) -> None:
        self._validate_callback = validate_callback

    def validate_step(
        self,
        step: ExecutionStep,
        outputs: List[ExecutionOutput],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate using callback."""
        return self._validate_callback(step, outputs, context)


# Default validator instance
default_validator = BaseValidator()
