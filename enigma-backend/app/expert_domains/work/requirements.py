from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RequirementType(str, Enum):
    """Types of requirements."""
    FUNCTIONAL = "functional"
    BUSINESS = "business"
    TECHNICAL = "technical"
    QUALITY = "quality"
    COMPLIANCE = "compliance"


class RequirementPriority(str, Enum):
    """Priority levels for requirements."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Requirement:
    """A single requirement."""
    requirement_id: str
    requirement_type: RequirementType
    title: str
    description: str
    priority: RequirementPriority = RequirementPriority.MEDIUM
    acceptance_criteria: List[str] = field(default_factory=list)
    is_mandatory: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BudgetConstraint:
    """Budget constraint for work."""
    constraint_id: str
    minimum_budget: Optional[float] = None
    maximum_budget: Optional[float] = None
    currency: str = "USD"
    billing_type: str = "fixed"  # fixed, hourly, milestone
    payment_terms: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TimelineConstraint:
    """Timeline constraint for work."""
    constraint_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration: Optional[str] = None
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    timezone: str = "UTC"
    urgency: str = "normal"  # normal, urgent, flexible
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlatformConstraint:
    """Platform constraint for work."""
    constraint_id: str
    platform_name: str
    platform_version: Optional[str] = None
    required_features: List[str] = field(default_factory=list)
    restricted_features: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComplianceRequirement:
    """Compliance requirement for work."""
    requirement_id: str
    compliance_type: str  # GDPR, HIPAA, SOC2, etc.
    description: str
    required_actions: List[str] = field(default_factory=list)
    documentation_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClientRequirements:
    """Complete client requirements for work."""
    requirements_id: str
    work_id: str
    functional_requirements: List[Requirement] = field(default_factory=list)
    business_requirements: List[Requirement] = field(default_factory=list)
    technical_requirements: List[Requirement] = field(default_factory=list)
    quality_requirements: List[Requirement] = field(default_factory=list)
    budget_constraints: List[BudgetConstraint] = field(default_factory=list)
    timeline_constraints: List[TimelineConstraint] = field(default_factory=list)
    platform_constraints: List[PlatformConstraint] = field(default_factory=list)
    compliance_requirements: List[ComplianceRequirement] = field(default_factory=list)
    success_expectations: List[str] = field(default_factory=list)
    risk_notes: List[str] = field(default_factory=list)
    special_instructions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
