from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AcceptancePriority(str, Enum):
    """Priority levels for acceptance criteria."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MeasurementType(str, Enum):
    """Types of measurements for acceptance criteria."""
    BOOLEAN = "boolean"
    THRESHOLD = "threshold"
    RANGE = "range"
    COUNT = "count"
    PERCENTAGE = "percentage"
    CUSTOM = "custom"


class ValidationMethod(str, Enum):
    """Validation methods for acceptance criteria."""
    AUTOMATED = "automated"
    MANUAL = "manual"
    HYBRID = "hybrid"
    PEER_REVIEW = "peer_review"
    CLIENT_REVIEW = "client_review"


@dataclass(frozen=True)
class AcceptanceCriterion:
    """A single acceptance criterion."""
    criterion_id: str
    requirement: str
    description: str
    measurement_type: MeasurementType
    threshold_value: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    validation_method: ValidationMethod = ValidationMethod.MANUAL
    priority: AcceptancePriority = AcceptancePriority.MEDIUM
    is_blocking: bool = False
    success_message: str = ""
    failure_message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcceptanceCriteriaSet:
    """A set of acceptance criteria for a deliverable or work item."""
    criteria_set_id: str
    name: str
    description: str
    target_type: str  # deliverable, work, task
    target_id: str
    criteria: List[AcceptanceCriterion] = field(default_factory=list)
    overall_pass_threshold: float = 1.0  # Percentage of criteria that must pass
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcceptanceResult:
    """Result of acceptance validation."""
    result_id: str
    criteria_set_id: str
    target_id: str
    passed: bool
    passed_criteria: List[str] = field(default_factory=list)
    failed_criteria: List[str] = field(default_factory=list)
    skipped_criteria: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)
    validated_by: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcceptanceChecklist:
    """A checklist for acceptance validation."""
    checklist_id: str
    name: str
    description: str
    checklist_items: List[Dict[str, Any]] = field(default_factory=list)
    requires_evidence: bool = True
    requires_signoff: bool = True
    signoff_roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
