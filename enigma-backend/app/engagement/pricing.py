from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PricingModelType(str, Enum):
    """Types of pricing models."""
    HOURLY = "hourly"
    FIXED = "fixed"
    MILESTONE = "milestone"
    RETAINER = "retainer"
    CUSTOM = "custom"


class PricingStatus(str, Enum):
    """Status for pricing proposals."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEGOTIATED = "negotiated"


class Currency(str, Enum):
    """Currency types."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    OTHER = "other"


@dataclass(frozen=True)
class PricingModel:
    """A pricing model for work."""
    model_id: str
    model_type: PricingModelType
    name: str
    description: str
    currency: Currency = Currency.USD
    base_rate: Optional[float] = None  # For hourly
    total_amount: Optional[float] = None  # For fixed
    estimated_hours: Optional[float] = None
    payment_terms: str = ""
    billing_frequency: str = "one_time"  # one_time, weekly, monthly, milestone
    minimum_amount: Optional[float] = None
    maximum_amount: Optional[float] = None
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    retainer_hours: Optional[float] = None  # For retainer
    retainer_period: Optional[str] = None  # For retainer
    custom_terms: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PricingProposal:
    """A pricing proposal for a work request."""
    proposal_id: str
    work_specification_id: str
    pricing_model: PricingModel
    status: PricingStatus = PricingStatus.DRAFT
    proposed_by: Optional[str] = None
    proposed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    negotiation_history: List[Dict[str, Any]] = field(default_factory=list)
    revision_notes: List[str] = field(default_factory=list)
    validity_period: Optional[str] = None
    expiration_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PricingComponent:
    """A component of a pricing model."""
    component_id: str
    name: str
    description: str
    amount: float
    unit: str = ""  # hour, item, milestone, month
    quantity: float = 1.0
    is_optional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PricingAdjustment:
    """An adjustment to pricing."""
    adjustment_id: str
    adjustment_type: str  # discount, surcharge, bonus
    description: str
    amount: float
    percentage: Optional[float] = None
    reason: str = ""
    applied_at: Optional[datetime] = None
    applied_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PricingFramework:
    """Framework for pricing models."""

    def __init__(self):
        self._pricing_models: Dict[str, PricingModel] = {}
        self._pricing_proposals: Dict[str, PricingProposal] = {}

    def create_hourly_model(
        self,
        model_id: str,
        name: str,
        description: str,
        hourly_rate: float,
        estimated_hours: float,
        currency: Currency = Currency.USD,
    ) -> PricingModel:
        """Create an hourly pricing model."""
        return PricingModel(
            model_id=model_id,
            model_type=PricingModelType.HOURLY,
            name=name,
            description=description,
            currency=currency,
            base_rate=hourly_rate,
            estimated_hours=estimated_hours,
            total_amount=hourly_rate * estimated_hours,
        )

    def create_fixed_model(
        self,
        model_id: str,
        name: str,
        description: str,
        total_amount: float,
        currency: Currency = Currency.USD,
    ) -> PricingModel:
        """Create a fixed pricing model."""
        return PricingModel(
            model_id=model_id,
            model_type=PricingModelType.FIXED,
            name=name,
            description=description,
            currency=currency,
            total_amount=total_amount,
        )

    def create_milestone_model(
        self,
        model_id: str,
        name: str,
        description: str,
        milestones: List[Dict[str, Any]],
        currency: Currency = Currency.USD,
    ) -> PricingModel:
        """Create a milestone pricing model."""
        total_amount = sum(m.get("amount", 0) for m in milestones)
        return PricingModel(
            model_id=model_id,
            model_type=PricingModel.MILESTONE,
            name=name,
            description=description,
            currency=currency,
            total_amount=total_amount,
            milestones=milestones,
            billing_frequency="milestone",
        )

    def create_retainer_model(
        self,
        model_id: str,
        name: str,
        description: str,
        monthly_amount: float,
        retainer_hours: float,
        currency: Currency = Currency.USD,
    ) -> PricingModel:
        """Create a retainer pricing model."""
        return PricingModel(
            model_id=model_id,
            model_type=PricingModel.RETAINER,
            name=name,
            description=description,
            currency=currency,
            base_rate=monthly_amount,
            retainer_hours=retainer_hours,
            total_amount=monthly_amount,
            billing_frequency="monthly",
        )

    def register_model(self, model: PricingModel) -> bool:
        """Register a pricing model."""
        if model.model_id in self._pricing_models:
            return False
        self._pricing_models[model.model_id] = model
        return True

    def get_model(self, model_id: str) -> Optional[PricingModel]:
        """Get a pricing model by ID."""
        return self._pricing_models.get(model_id)

    def list_models(self) -> List[PricingModel]:
        """List all pricing models."""
        return list(self._pricing_models.values())

    def create_proposal(
        self,
        proposal_id: str,
        work_specification_id: str,
        pricing_model: PricingModel,
        proposed_by: str,
    ) -> PricingProposal:
        """Create a pricing proposal."""
        return PricingProposal(
            proposal_id=proposal_id,
            work_specification_id=work_specification_id,
            pricing_model=pricing_model,
            proposed_by=proposed_by,
            proposed_at=datetime.utcnow(),
        )

    def register_proposal(self, proposal: PricingProposal) -> bool:
        """Register a pricing proposal."""
        if proposal.proposal_id in self._pricing_proposals:
            return False
        self._pricing_proposals[proposal.proposal_id] = proposal
        return True

    def get_proposal(self, proposal_id: str) -> Optional[PricingProposal]:
        """Get a pricing proposal by ID."""
        return self._pricing_proposals.get(proposal_id)

    def get_proposals_for_work(self, work_specification_id: str) -> List[PricingProposal]:
        """Get pricing proposals for a work specification."""
        return [
            p for p in self._pricing_proposals.values()
            if p.work_specification_id == work_specification_id
        ]

    def calculate_total(self, model: PricingModel) -> float:
        """Calculate total amount for a pricing model."""
        if model.total_amount is not None:
            return model.total_amount
        if model.base_rate is not None and model.estimated_hours is not None:
            return model.base_rate * model.estimated_hours
        return 0.0
