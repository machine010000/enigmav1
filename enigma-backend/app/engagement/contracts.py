from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionStatus(str, Enum):
    """Status for decision records."""
    PENDING = "pending"
    NEED_RESEARCH = "need_research"
    NEED_LEARNING = "need_learning"
    NEED_NEGOTIATION = "need_negotiation"
    NEED_CLARIFICATION = "need_clarification"
    NEED_PORTFOLIO = "need_portfolio"
    REJECT = "reject"
    ACCEPT = "accept"
    ACCEPT_WITH_CONDITIONS = "accept_with_conditions"


class DecisionPriority(str, Enum):
    """Priority levels for decisions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DecisionRecord:
    """A decision record for a work request."""
    decision_id: str
    work_specification_id: str
    timestamp: datetime
    decision_status: DecisionStatus
    decision_confidence: float  # 0.0 to 1.0
    decision_reasoning: List[str] = field(default_factory=list)
    missing_knowledge: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    missing_capabilities: List[str] = field(default_factory=list)
    required_research: List[str] = field(default_factory=list)
    estimated_risk: float = 0.0  # 0.0 to 1.0
    estimated_profitability: float = 0.0  # 0.0 to 1.0
    estimated_complexity: float = 0.0  # 0.0 to 1.0
    estimated_delivery_time: Optional[str] = None
    estimated_success_probability: float = 0.0  # 0.0 to 1.0
    rejection_reasons: List[str] = field(default_factory=list)
    acceptance_conditions: List[str] = field(default_factory=list)
    priority: DecisionPriority = DecisionPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionGate:
    """Gate that controls whether execution can proceed."""
    gate_id: str
    name: str
    description: str
    required_status: List[DecisionStatus] = field(default_factory=list)
    blocked_status: List[DecisionStatus] = field(default_factory=list)
    requires_conditions: bool = False
    requires_approval: bool = False
    approval_roles: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionRequirement:
    """A requirement for making a decision."""
    requirement_id: str
    requirement_type: str  # knowledge, evidence, capability, portfolio, clarity
    description: str
    is_blocking: bool = True
    validation_method: str = "manual"  # manual, automated, hybrid
    priority: str = "medium"  # low, medium, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionContract(ABC):
    """Contract for decision-making processes."""

    @abstractmethod
    def evaluate_work_request(
        self,
        work_specification_id: str,
        available_knowledge: List[str],
        available_evidence: List[str],
        available_capabilities: List[str],
    ) -> DecisionRecord:
        """Evaluate a work request and produce a decision."""
        pass

    @abstractmethod
    def can_proceed(self, decision_id: str) -> bool:
        """Check if execution can proceed based on a decision."""
        pass

    @abstractmethod
    def get_blocking_issues(self, decision_id: str) -> List[str]:
        """Get blocking issues for a decision."""
        pass

    @abstractmethod
    def get_required_actions(self, decision_id: str) -> List[str]:
        """Get required actions for a decision."""
        pass
