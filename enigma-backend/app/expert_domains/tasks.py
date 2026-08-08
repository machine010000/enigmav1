from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.capabilities import CapabilityContract


class TaskCategory(str, Enum):
    """Categories for tasks."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    REPORTING = "reporting"
    DIAGNOSIS = "diagnosis"
    PREDICTION = "prediction"
    MAINTENANCE = "maintenance"


class TaskStatus(str, Enum):
    """Status for tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskContract:
    """Contract for an executable task within expert domains."""
    task_id: str
    name: str
    description: str
    goal: str
    category: TaskCategory
    required_capabilities: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    execution_standards: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    failure_conditions: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class TaskRequirement:
    """Represents a requirement for a task."""
    requirement_id: str
    task_id: str
    requirement_type: str  # capability, input, deliverable, standard
    requirement_value: str
    optional: bool = False


@dataclass(frozen=True)
class TaskExecution:
    """Represents a task execution instance."""
    execution_id: str
    task_id: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    deliverables: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskRegistry:
    """Registry for tasks."""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskContract] = {}

    def register(self, task: TaskContract) -> bool:
        """Register a task."""
        if task.task_id in self._tasks:
            return False
        self._tasks[task.task_id] = task
        return True

    def get(self, task_id: str) -> Optional[TaskContract]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def list_all(self) -> List[TaskContract]:
        """List all tasks."""
        return list(self._tasks.values())

    def list_by_category(self, category: TaskCategory) -> List[TaskContract]:
        """List tasks by category."""
        return [t for t in self._tasks.values() if t.category == category]

    def list_by_capability(self, capability_id: str) -> List[TaskContract]:
        """List tasks that require a specific capability."""
        return [
            t for t in self._tasks.values()
            if capability_id in t.required_capabilities
        ]

    def remove(self, task_id: str) -> bool:
        """Remove a task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def validate_capability_requirements(
        self,
        task_id: str,
        available_capabilities: List[str],
    ) -> Dict[str, bool]:
        """Validate if capability requirements are met for a task."""
        task = self.get(task_id)
        if not task:
            return {"valid": False, "task_found": False}

        required_capabilities = set(task.required_capabilities)
        available_capabilities_set = set(available_capabilities)

        validation = {
            "valid": True,
            "task_found": True,
            "capabilities_met": required_capabilities.issubset(available_capabilities_set),
            "missing_capabilities": list(required_capabilities - available_capabilities_set),
        }

        if not validation["capabilities_met"]:
            validation["valid"] = False

        return validation
