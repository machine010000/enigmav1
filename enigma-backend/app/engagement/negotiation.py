from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NegotiationItemType(str, Enum):
    """Types of negotiation items."""
    QUESTION = "question"
    SCOPE_CHANGE = "scope_change"
    BUDGET_CHANGE = "budget_change"
    TIMELINE_CHANGE = "timeline_change"
    DELIVERABLE_CHANGE = "deliverable_change"
    RISK_WARNING = "risk_warning"
    TERM_CHANGE = "term_change"


class NegotiationStatus(str, Enum):
    """Status for negotiation items."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    RESOLVED = "resolved"


class NegotiationPriority(str, Enum):
    """Priority levels for negotiation items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class NegotiationItem:
    """A negotiation item."""
    item_id: str
    item_type: NegotiationItemType
    work_specification_id: str
    description: str
    current_value: str
    proposed_value: str
    status: NegotiationStatus = NegotiationStatus.PENDING
    priority: NegotiationPriority = NegotiationPriority.MEDIUM
    requested_by: Optional[str] = None
    responded_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: str = ""
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NegotiationRecord:
    """A record of a negotiation process."""
    record_id: str
    work_specification_id: str
    negotiation_items: List[NegotiationItem] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = "active"  # active, completed, abandoned
    total_items: int = 0
    resolved_items: int = 0
    rejected_items: int = 0
    pending_items: int = 0
    negotiation_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NegotiationTemplate:
    """A template for common negotiation scenarios."""
    template_id: str
    scenario_type: str  # scope, budget, timeline, deliverable, terms
    name: str
    description: str
    standard_questions: List[str] = field(default_factory=list)
    standard_responses: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NegotiationFramework:
    """Framework for negotiation management."""

    def __init__(self):
        self._negotiation_records: Dict[str, NegotiationRecord] = {}
        self._negotiation_templates: Dict[str, NegotiationTemplate] = {}

    def create_negotiation_item(
        self,
        item_id: str,
        item_type: NegotiationItemType,
        work_specification_id: str,
        description: str,
        current_value: str,
        proposed_value: str,
        priority: NegotiationPriority = NegotiationPriority.MEDIUM,
    ) -> NegotiationItem:
        """Create a negotiation item."""
        return NegotiationItem(
            item_id=item_id,
            item_type=item_type,
            work_specification_id=work_specification_id,
            description=description,
            current_value=current_value,
            proposed_value=proposed_value,
            priority=priority,
        )

    def start_negotiation(
        self,
        record_id: str,
        work_specification_id: str,
    ) -> NegotiationRecord:
        """Start a negotiation process."""
        return NegotiationRecord(
            record_id=record_id,
            work_specification_id=work_specification_id,
        )

    def add_item_to_record(
        self,
        record_id: str,
        item: NegotiationItem,
    ) -> bool:
        """Add a negotiation item to a record."""
        if record_id not in self._negotiation_records:
            return False
        record = self._negotiation_records[record_id]
        # In a real implementation, we'd update the record
        # For now, this is a placeholder
        return True

    def get_negotiation_record(self, record_id: str) -> Optional[NegotiationRecord]:
        """Get a negotiation record by ID."""
        return self._negotiation_records.get(record_id)

    def get_negotiation_for_work(self, work_specification_id: str) -> Optional[NegotiationRecord]:
        """Get negotiation for a work specification."""
        for record in self._negotiation_records.values():
            if record.work_specification_id == work_specification_id and record.status == "active":
                return record
        return None

    def register_template(self, template: NegotiationTemplate) -> bool:
        """Register a negotiation template."""
        if template.template_id in self._negotiation_templates:
            return False
        self._negotiation_templates[template.template_id] = template
        return True

    def get_template(self, template_id: str) -> Optional[NegotiationTemplate]:
        """Get a negotiation template by ID."""
        return self._negotiation_templates.get(template_id)

    def get_template_by_scenario(self, scenario_type: str) -> Optional[NegotiationTemplate]:
        """Get a negotiation template by scenario type."""
        for template in self._negotiation_templates.values():
            if template.scenario_type == scenario_type:
                return template
        return None

    def get_blocking_items(self, record_id: str) -> List[NegotiationItem]:
        """Get blocking negotiation items."""
        record = self.get_negotiation_record(record_id)
        if not record:
            return []
        return [
            item for item in record.negotiation_items
            if item.status in [NegotiationStatus.PENDING, NegotiationStatus.UNDER_REVIEW]
            and item.priority in [NegotiationPriority.HIGH, NegotiationPriority.CRITICAL]
        ]

    def get_required_actions(self, record_id: str) -> List[str]:
        """Get required actions for a negotiation."""
        record = self.get_negotiation_record(record_id)
        if not record:
            return []

        actions = []
        blocking_items = self.get_blocking_items(record_id)
        if blocking_items:
            actions.append(f"Address {len(blocking_items)} blocking negotiation items")

        if record.pending_items > 0:
            actions.append(f"Resolve {record.pending_items} pending items")

        return actions
