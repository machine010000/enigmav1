from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkPriority(str, Enum):
    """Priority levels for work specifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkComplexity(str, Enum):
    """Complexity levels for work specifications."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class WorkStatus(str, Enum):
    """Status for work specifications."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


@dataclass(frozen=True)
class WorkSpecification:
    """Specification for client work requests."""
    work_id: str
    title: str
    description: str
    business_goal: str
    business_context: str
    industry: str
    target_audience: str
    expected_outcome: str
    constraints: List[str] = field(default_factory=list)
    priority: WorkPriority = WorkPriority.MEDIUM
    complexity: WorkComplexity = WorkComplexity.MODERATE
    estimated_scope: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    optional_capabilities: List[str] = field(default_factory=list)
    recommended_capabilities: List[str] = field(default_factory=list)
    required_tasks: List[str] = field(default_factory=list)
    optional_tasks: List[str] = field(default_factory=list)
    suggested_tasks: List[str] = field(default_factory=list)
    status: WorkStatus = WorkStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkCapabilityMapping:
    """Mapping between work specifications and capabilities."""
    mapping_id: str
    work_id: str
    capability_id: str
    mapping_type: str  # required, optional, recommended
    importance: str = "medium"  # low, medium, high, critical
    justification: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class WorkTaskMapping:
    """Mapping between work specifications and tasks."""
    mapping_id: str
    work_id: str
    task_id: str
    mapping_type: str  # required, optional, suggested
    order: Optional[int] = None
    estimated_duration: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
