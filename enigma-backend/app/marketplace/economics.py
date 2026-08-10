"""
Marketplace Application Economy Contracts.

Domain-agnostic layer for understanding the real cost and constraints
of applying for work on each marketplace.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from .contracts import (
    CreditType,
    MarketplacePlatform,
    PlatformCost,
    PlatformLimits,
)


class ApplicationUnit(str, Enum):
    """Unit of application cost on marketplaces."""
    CONNECTS = "connects"  # Upwork
    BIDS = "bids"  # Freelancer
    OFFERS = "offers"  # Mostaql
    NONE = "none"  # Fiverr (gig economy)
    TOKENS = "tokens"  # Generic
    KHAMSAT_CREDITS = "khamsat_credits"  # Khamsat


class ApplicationModel(str, Enum):
    """Application model types for marketplaces."""
    CREDIT_BASED = "credit_based"  # Uses credits/tokens to apply
    FEE_BASED = "fee_based"  # Uses monetary fees to apply
    FREE = "free"  # No cost to apply
    MIXED = "mixed"  # Combination of credits and fees
    NO_DIRECT_APPLICATION = "no_direct_application"  # Gig economy, no traditional application
    UNKNOWN = "unknown"  # Application model not known


class VerificationStatus(str, Enum):
    """Verification status for economics data."""
    VERIFIED = "verified"  # Data has been verified
    UNKNOWN = "unknown"  # Data is unknown/unverified
    NOT_APPLICABLE = "not_applicable"  # Data does not apply to this platform


class EconomicDecision(str, Enum):
    """Economic decision for application."""
    APPLY = "apply"
    DONT_APPLY = "dont_apply"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INSUFFICIENT_QUOTA = "insufficient_quota"
    REQUIRES_MONEY = "requires_money"
    REQUIRES_ACCOUNT_SETUP = "requires_account_setup"
    NOT_APPLICABLE = "not_applicable"
    WAIT = "wait"
    NEED_INFORMATION = "need_information"


class QuotaType(str, Enum):
    """Types of quotas."""
    DAILY = "daily"
    MONTHLY = "monthly"
    ROLLING = "rolling"
    LIFETIME = "lifetime"
    WEEKLY = "weekly"


@dataclass
class EconomicsValue:
    """A value with verification status and source tracking."""
    value: Optional[float]
    status: VerificationStatus = VerificationStatus.UNKNOWN
    source: Optional[str] = None
    verified_at: Optional[str] = None  # ISO datetime string
    expires_at: Optional[str] = None  # ISO datetime string
    confidence: Optional[float] = None  # 0.0 to 1.0

    def is_verified(self) -> bool:
        return self.status == VerificationStatus.VERIFIED

    def is_stale(self) -> bool:
        if not self.expires_at:
            return False
        from datetime import datetime
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > expires

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "status": self.status.value,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
            "is_verified": self.is_verified(),
            "is_stale": self.is_stale(),
        }


@dataclass
class MarketplaceCost:
    """Normalized cost representation for marketplace participation."""
    cash_cost: EconomicsValue
    currency: str = "USD"
    credit_cost: Optional[EconomicsValue] = None
    credit_name: Optional[str] = None
    opportunity_cost: Optional[EconomicsValue] = None
    total_cost: Optional[EconomicsValue] = None

    @property
    def is_free(self) -> bool:
        """Check if participation is free."""
        if self.cash_cost.value and self.cash_cost.value > 0:
            return False
        if self.credit_cost and self.credit_cost.value and self.credit_cost.value > 0:
            return False
        # Negative values are not free (refunds/credits)
        if self.cash_cost.value and self.cash_cost.value < 0:
            return False
        if self.credit_cost and self.credit_cost.value and self.credit_cost.value < 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cash_cost": self.cash_cost.to_dict(),
            "currency": self.currency,
            "credit_cost": self.credit_cost.to_dict() if self.credit_cost else None,
            "credit_name": self.credit_name,
            "opportunity_cost": self.opportunity_cost.to_dict() if self.opportunity_cost else None,
            "total_cost": self.total_cost.to_dict() if self.total_cost else None,
            "is_free": self.is_free,
        }


@dataclass
class ApplicationCost:
    """Cost of applying to a specific job (legacy, for backward compatibility)."""
    unit: ApplicationUnit
    amount: float
    currency: str = "USD"
    monetary_value: Optional[float] = None  # If unit has monetary conversion
    is_free: bool = False
    description: str = ""
    source: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit": self.unit.value,
            "amount": self.amount,
            "currency": self.currency,
            "monetary_value": self.monetary_value,
            "is_free": self.is_free,
            "description": self.description,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
        }


@dataclass
class AccountBalance:
    """Account balance for application units."""
    unit: ApplicationUnit
    available: float
    total: float
    currency: str = "USD"
    monetary_value: Optional[float] = None
    last_updated: Optional[str] = None
    source: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit": self.unit.value,
            "available": self.available,
            "total": self.total,
            "currency": self.currency,
            "monetary_value": self.monetary_value,
            "last_updated": self.last_updated,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
        }


@dataclass
class ApplicationQuota:
    """Application quota limits."""
    quota_type: QuotaType
    used: int
    limit: int
    reset_at: Optional[str] = None  # ISO datetime string
    period_start: Optional[str] = None
    source: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    confidence: Optional[float] = None

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def is_exhausted(self) -> bool:
        return self.remaining <= 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quota_type": self.quota_type.value,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "is_exhausted": self.is_exhausted,
            "reset_at": self.reset_at,
            "period_start": self.period_start,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
        }


@dataclass
class WalletRequirement:
    """Wallet/balance requirements for application."""
    minimum_balance: EconomicsValue
    currency: str = "USD"
    description: str = ""
    source: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "minimum_balance": self.minimum_balance.to_dict(),
            "currency": self.currency,
            "description": self.description,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
        }


@dataclass
class EconomicAssessment:
    """Economic assessment of a job application."""
    expected_revenue: Optional[EconomicsValue] = None
    win_probability: Optional[EconomicsValue] = None  # 0.0 to 1.0
    execution_readiness: Optional[EconomicsValue] = None  # 0.0 to 1.0
    evidence_strength: Optional[EconomicsValue] = None  # 0.0 to 1.0
    application_cost: Optional[ApplicationCost] = None
    execution_cost: Optional[EconomicsValue] = None
    risk_score: Optional[EconomicsValue] = None  # 0.0 to 1.0
    confidence_adjustment: Optional[EconomicsValue] = None  # 0.0 to 1.0

    @property
    def expected_value(self) -> Optional[float]:
        """Calculate expected value: Success Probability × Expected Revenue."""
        if not self.expected_revenue or not self.win_probability:
            return None
        if self.expected_revenue.value is None or self.win_probability.value is None:
            return None
        return self.expected_revenue.value * self.win_probability.value

    @property
    def risk_adjusted_value(self) -> Optional[float]:
        """Calculate risk-adjusted value: Expected Value × Confidence Adjustment."""
        ev = self.expected_value
        if ev is None:
            return None
        if not self.confidence_adjustment or self.confidence_adjustment.value is None:
            return ev
        return ev * self.confidence_adjustment.value

    @property
    def economic_value(self) -> Optional[float]:
        """Calculate economic value: risk-adjusted value - costs."""
        rav = self.risk_adjusted_value
        if rav is None:
            return None

        total_cost = 0.0
        if self.application_cost and self.application_cost.monetary_value:
            total_cost += self.application_cost.monetary_value
        if self.execution_cost and self.execution_cost.value:
            total_cost += self.execution_cost.value

        return rav - total_cost

    @property
    def roi_estimate(self) -> Optional[float]:
        """Calculate ROI: Risk Adjusted Value / Participation Cost."""
        rav = self.risk_adjusted_value
        if rav is None:
            return None

        total_cost = 0.0
        if self.application_cost and self.application_cost.monetary_value:
            total_cost += self.application_cost.monetary_value
        if self.execution_cost and self.execution_cost.value:
            total_cost += self.execution_cost.value

        if total_cost == 0:
            return None  # Explicit zero-cost classification

        return rav / total_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_revenue": self.expected_revenue.to_dict() if self.expected_revenue else None,
            "win_probability": self.win_probability.to_dict() if self.win_probability else None,
            "execution_readiness": self.execution_readiness.to_dict() if self.execution_readiness else None,
            "evidence_strength": self.evidence_strength.to_dict() if self.evidence_strength else None,
            "application_cost": self.application_cost.to_dict() if self.application_cost else None,
            "execution_cost": self.execution_cost.to_dict() if self.execution_cost else None,
            "risk_score": self.risk_score.to_dict() if self.risk_score else None,
            "confidence_adjustment": self.confidence_adjustment.to_dict() if self.confidence_adjustment else None,
            "expected_value": self.expected_value,
            "risk_adjusted_value": self.risk_adjusted_value,
            "economic_value": self.economic_value,
            "roi_estimate": self.roi_estimate,
        }


@dataclass
class MarketplaceEconomicsContract:
    """Generic contract for marketplace economics information."""
    platform: MarketplacePlatform
    currency: str
    application_model: ApplicationModel
    application_cost: Optional[MarketplaceCost] = None
    minimum_balance: Optional[EconomicsValue] = None
    credit_name: Optional[str] = None
    credit_cost: Optional[EconomicsValue] = None
    proposal_cost: Optional[EconomicsValue] = None
    boost_available: Optional[EconomicsValue] = None
    boost_cost: Optional[EconomicsValue] = None
    transaction_fee: Optional[EconomicsValue] = None
    platform_commission: Optional[EconomicsValue] = None
    withdrawal_fee: Optional[EconomicsValue] = None
    account_requirements: Optional[Dict[str, Any]] = None
    daily_limits: Optional[Dict[str, Any]] = None
    weekly_limits: Optional[Dict[str, Any]] = None
    monthly_limits: Optional[Dict[str, Any]] = None
    last_verified_at: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    expires_at: Optional[str] = None

    def is_stale(self) -> bool:
        """Check if economics data is stale."""
        if not self.expires_at:
            return False
        from datetime import datetime
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > expires

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "currency": self.currency,
            "application_model": self.application_model.value,
            "application_cost": self.application_cost.to_dict() if self.application_cost else None,
            "minimum_balance": self.minimum_balance.to_dict() if self.minimum_balance else None,
            "credit_name": self.credit_name,
            "credit_cost": self.credit_cost.to_dict() if self.credit_cost else None,
            "proposal_cost": self.proposal_cost.to_dict() if self.proposal_cost else None,
            "boost_available": self.boost_available.to_dict() if self.boost_available else None,
            "boost_cost": self.boost_cost.to_dict() if self.boost_cost else None,
            "transaction_fee": self.transaction_fee.to_dict() if self.transaction_fee else None,
            "platform_commission": self.platform_commission.to_dict() if self.platform_commission else None,
            "withdrawal_fee": self.withdrawal_fee.to_dict() if self.withdrawal_fee else None,
            "account_requirements": self.account_requirements,
            "daily_limits": self.daily_limits,
            "weekly_limits": self.weekly_limits,
            "monthly_limits": self.monthly_limits,
            "last_verified_at": self.last_verified_at,
            "source": self.source,
            "confidence": self.confidence,
            "expires_at": self.expires_at,
            "is_stale": self.is_stale(),
        }


@dataclass
class ApplicationEconomics:
    """Complete economic analysis for application decision."""
    job_id: str
    platform: MarketplacePlatform
    account_balance: AccountBalance
    application_cost: ApplicationCost
    quotas: List[ApplicationQuota] = field(default_factory=list)
    wallet_requirements: Optional[WalletRequirement] = None
    assessment: Optional[EconomicAssessment] = None
    decision: EconomicDecision = EconomicDecision.WAIT
    decision_reason: str = ""
    remaining_balance_after_apply: Optional[float] = None
    source: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    confidence: Optional[float] = None

    @property
    def can_afford(self) -> bool:
        """Check if account can afford the application cost."""
        if self.application_cost.is_free:
            return True
        return self.account_balance.available >= self.application_cost.amount

    @property
    def has_quota(self) -> bool:
        """Check if account has available quota."""
        if not self.quotas:
            return True
        return not any(q.is_exhausted for q in self.quotas)

    @property
    def meets_wallet_requirements(self) -> bool:
        """Check if account meets wallet requirements."""
        if not self.wallet_requirements:
            return True
        return self.account_balance.monetary_value >= self.wallet_requirements.minimum_balance.value if self.wallet_requirements.minimum_balance.value else True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "platform": self.platform.value,
            "account_balance": self.account_balance.to_dict(),
            "application_cost": self.application_cost.to_dict(),
            "quotas": [q.to_dict() for q in self.quotas],
            "wallet_requirements": self.wallet_requirements.to_dict() if self.wallet_requirements else None,
            "assessment": self.assessment.to_dict() if self.assessment else None,
            "decision": self.decision.value,
            "decision_reason": self.decision_reason,
            "remaining_balance_after_apply": self.remaining_balance_after_apply,
            "can_afford": self.can_afford,
            "has_quota": self.has_quota,
            "meets_wallet_requirements": self.meets_wallet_requirements,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
        }


@dataclass
class CreativeOpportunityContext:
    """
    Integration contract for Creativity Engine.

    Provides context for determining strategy when profile has low trust
    (e.g., zero reviews, no portfolio).
    """
    profile_strength: Optional[EconomicsValue] = None  # 0.0 to 1.0
    review_count: Optional[EconomicsValue] = None
    portfolio_strength: Optional[EconomicsValue] = None  # 0.0 to 1.0
    experience_level: Optional[str] = None  # "new", "intermediate", "expert"
    trust_deficit: Optional[EconomicsValue] = None  # 0.0 to 1.0, higher = more deficit
    market_competition: Optional[EconomicsValue] = None  # 0.0 to 1.0
    job_value: Optional[EconomicsValue] = None
    application_cost: Optional[ApplicationCost] = None
    expected_success_probability: Optional[EconomicsValue] = None
    pricing_flexibility: Optional[EconomicsValue] = None  # 0.0 to 1.0
    platform: Optional[MarketplacePlatform] = None
    source: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_strength": self.profile_strength.to_dict() if self.profile_strength else None,
            "review_count": self.review_count.to_dict() if self.review_count else None,
            "portfolio_strength": self.portfolio_strength.to_dict() if self.portfolio_strength else None,
            "experience_level": self.experience_level,
            "trust_deficit": self.trust_deficit.to_dict() if self.trust_deficit else None,
            "market_competition": self.market_competition.to_dict() if self.market_competition else None,
            "job_value": self.job_value.to_dict() if self.job_value else None,
            "application_cost": self.application_cost.to_dict() if self.application_cost else None,
            "expected_success_probability": self.expected_success_probability.to_dict() if self.expected_success_probability else None,
            "pricing_flexibility": self.pricing_flexibility.to_dict() if self.pricing_flexibility else None,
            "platform": self.platform.value if self.platform else None,
            "source": self.source,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
        }


class EconomicsEngine(ABC):
    """
    Abstract base class for marketplace economics engines.

    Each marketplace implements this to provide economic calculations
    specific to their platform model.
    """

    @property
    @abstractmethod
    def platform(self) -> MarketplacePlatform:
        """Get the platform this engine handles."""
        pass

    @property
    @abstractmethod
    def application_model(self) -> ApplicationModel:
        """Get the application model for this platform."""
        pass

    @abstractmethod
    async def get_economics_contract(self) -> MarketplaceEconomicsContract:
        """
        Get the complete economics contract for this platform.

        Returns:
            MarketplaceEconomicsContract with all platform economics
        """
        pass

    @abstractmethod
    async def get_application_cost(
        self,
        job_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApplicationCost:
        """
        Calculate the cost to apply to a job.

        Args:
            job_id: Platform-specific job ID
            metadata: Additional job metadata

        Returns:
            Application cost information
        """
        pass

    @abstractmethod
    async def get_account_balance(self) -> AccountBalance:
        """
        Get current account balance.

        Returns:
            Account balance information
        """
        pass

    @abstractmethod
    async def get_quotas(self) -> List[ApplicationQuota]:
        """
        Get current application quotas.

        Returns:
            List of quota information
        """
        pass

    @abstractmethod
    async def get_wallet_requirements(self) -> Optional[WalletRequirement]:
        """
        Get wallet/balance requirements.

        Returns:
            Wallet requirements or None if not applicable
        """
        pass

    @abstractmethod
    async def calculate_economics(
        self,
        job_id: str,
        assessment: Optional[EconomicAssessment] = None,
    ) -> ApplicationEconomics:
        """
        Calculate complete economics for application decision.

        Args:
            job_id: Platform-specific job ID
            assessment: Economic assessment of the job

        Returns:
            Complete application economics
        """
        pass

    @abstractmethod
    async def evaluate_application_economics(
        self,
        opportunity: Dict[str, Any],
        user_balance: Optional[float] = None,
        available_credits: Optional[float] = None,
        estimated_success_probability: Optional[float] = None,
        expected_revenue: Optional[float] = None,
    ) -> ApplicationEconomics:
        """
        Evaluate application economics with detailed decision.

        Args:
            opportunity: Job/opportunity data
            user_balance: User's monetary balance
            available_credits: User's available credits
            estimated_success_probability: Estimated success probability (0.0 to 1.0)
            expected_revenue: Expected revenue from the job

        Returns:
            ApplicationEconomics with detailed decision
        """
        pass
