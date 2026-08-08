from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReviewType(str, Enum):
    """Types of reviews."""
    QUALITY = "quality"
    TECHNICAL = "technical"
    BUSINESS = "business"
    COMPLIANCE = "compliance"
    PEER = "peer"
    CLIENT = "client"
    AUTOMATED = "automated"


class ReviewStatus(str, Enum):
    """Status for reviews."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReviewDecision(str, Enum):
    """Decision types for reviews."""
    APPROVED = "approved"
    APPROVED_WITH_CHANGES = "approved_with_changes"
    REJECTED = "rejected"
    RESUBMIT = "resubmit"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class ReviewChecklistItem:
    """A single item in a review checklist."""
    item_id: str
    title: str
    description: str
    is_required: bool = True
    weight: float = 1.0  # Importance weight
    validation_method: str = "manual"  # manual, automated
    expected_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewChecklist:
    """A checklist for conducting reviews."""
    checklist_id: str
    name: str
    description: str
    review_type: ReviewType
    checklist_items: List[ReviewChecklistItem] = field(default_factory=list)
    requires_evidence: bool = True
    requires_signoff: bool = True
    signoff_roles: List[str] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewValidationRule:
    """A validation rule for reviews."""
    rule_id: str
    name: str
    description: str
    rule_type: str  # mandatory, conditional, advisory
    condition: str = ""
    action_on_failure: str = "block"  # block, warn, skip
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Review:
    """A review instance."""
    review_id: str
    target_type: str  # deliverable, work, task
    target_id: str
    review_type: ReviewType
    reviewer: str
    checklist_id: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING
    decision: Optional[ReviewDecision] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    checklist_results: List[Dict[str, Any]] = field(default_factory=list)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    review_notes: List[str] = field(default_factory=list)
    approval_conditions: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewApproval:
    """An approval for a review."""
    approval_id: str
    review_id: str
    approver: str
    approval_status: str  # approved, rejected, pending
    comments: str = ""
    approved_at: Optional[datetime] = None
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewPolicy:
    """Policy governing reviews."""
    policy_id: str
    name: str
    description: str
    target_type: str  # deliverable, work, task
    required_review_types: List[ReviewType] = field(default_factory=list)
    minimum_reviewers: int = 1
    required_approvals: int = 1
    escalation_rules: List[str] = field(default_factory=list)
    retry_policy: str = "allow"  # allow, restricted, none
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
