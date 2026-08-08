from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionStepType(str, Enum):
    """Types of execution steps."""
    PREPARATION = "preparation"
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"
    CLEANUP = "cleanup"


@dataclass(frozen=True)
class ExecutionStep:
    """A single step in an execution template."""
    step_id: str
    step_type: ExecutionStepType
    name: str
    description: str
    order: int
    required_inputs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    optional: bool = False
    estimated_duration: Optional[str] = None
    quality_gates: List[str] = field(default_factory=list)
    validation_checkpoints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionTemplate:
    """Template for executing tasks within expert domains."""
    template_id: str
    name: str
    description: str
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    quality_gates: List[str] = field(default_factory=list)
    validation_checkpoints: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    supported_tasks: List[str] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    retry_policy: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class QualityGate:
    """A quality gate in execution."""
    gate_id: str
    name: str
    description: str
    gate_type: str  # threshold, boolean, comparison
    threshold_value: Optional[float] = None
    pass_condition: str = ""
    fail_action: str = "stop"  # stop, warn, continue
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationCheckpoint:
    """A validation checkpoint in execution."""
    checkpoint_id: str
    name: str
    description: str
    checkpoint_type: str  # input, output, intermediate
    validation_rules: List[str] = field(default_factory=list)
    required: bool = True
    on_failure: str = "stop"  # stop, warn, skip
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionTemplateRegistry:
    """Registry for execution templates."""

    def __init__(self) -> None:
        self._templates: Dict[str, ExecutionTemplate] = {}

    def register(self, template: ExecutionTemplate) -> bool:
        """Register an execution template."""
        if template.template_id in self._templates:
            return False
        self._templates[template.template_id] = template
        return True

    def get(self, template_id: str) -> Optional[ExecutionTemplate]:
        """Get an execution template by ID."""
        return self._templates.get(template_id)

    def list_all(self) -> List[ExecutionTemplate]:
        """List all execution templates."""
        return list(self._templates.values())

    def list_by_task(self, task_id: str) -> List[ExecutionTemplate]:
        """List templates that support a specific task."""
        return [
            t for t in self._templates.values()
            if task_id in t.supported_tasks
        ]

    def remove(self, template_id: str) -> bool:
        """Remove an execution template."""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def validate_step_order(self, template_id: str) -> Dict[str, bool]:
        """Validate that execution steps are properly ordered."""
        template = self.get(template_id)
        if not template:
            return {"valid": False, "template_found": False}

        orders = [step.order for step in template.execution_steps]
        sorted_orders = sorted(orders)

        validation = {
            "valid": True,
            "template_found": True,
            "steps_ordered": orders == sorted_orders,
            "no_duplicates": len(orders) == len(set(orders)),
        }

        if not validation["steps_ordered"]:
            validation["valid"] = False
        if not validation["no_duplicates"]:
            validation["valid"] = False

        return validation

    def get_required_capabilities(self, template_id: str) -> List[str]:
        """Get all required capabilities for a template."""
        template = self.get(template_id)
        if not template:
            return []

        capabilities = set(template.required_capabilities)
        for step in template.execution_steps:
            capabilities.update(step.required_capabilities)

        return list(capabilities)
