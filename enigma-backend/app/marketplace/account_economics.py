"""
Account-Aware Economics

Integrates account state with economics calculations.
Combines platform rules with actual account state for intelligent economics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.account_state import (
    MarketplaceAccountState,
    AccountStatus,
    DataSource,
    FreshnessStatus,
)
from app.marketplace.platform_rules import (
    PlatformRules,
    get_platform_rules,
    ApplicationCostType,
)
from app.marketplace.economics import (
    EconomicDecision,
    EconomicsValue,
    VerificationStatus,
)


class EconomicSafetyStatus(str, Enum):
    """Economic safety gate status."""
    SAFE = "safe"
    NEED_RESEARCH = "need_research"
    BLOCK = "block"
    UNKNOWN = "unknown"


@dataclass
class ApplicationCost:
    """
    Application cost with account state awareness.
    """
    cost_type: ApplicationCostType
    amount: Optional[float] = None  # None means unknown
    currency: Optional[str] = None
    is_known: bool = False
    
    def is_free(self) -> bool:
        """Check if application is free."""
        return self.cost_type == ApplicationCostType.FREE
    
    def is_unknown(self) -> bool:
        """Check if cost is unknown."""
        return not self.is_known or self.cost_type == ApplicationCostType.UNKNOWN


@dataclass
class EconomicMetrics:
    """
    Economic metrics for job evaluation.
    """
    application_cost: ApplicationCost
    available_balance: Optional[float] = None
    available_credits: Optional[int] = None
    expected_value: Optional[float] = None
    win_probability: Optional[float] = None
    roi: Optional[float] = None
    
    def is_balance_sufficient(self) -> Optional[bool]:
        """Check if balance is sufficient for application cost."""
        if self.application_cost.is_free() or self.application_cost.is_unknown():
            return None
        
        if self.application_cost.cost_type == ApplicationCostType.CREDITS:
            if self.available_credits is None:
                return None
            return self.available_credits >= self.application_cost.amount
        
        if self.application_cost.cost_type == ApplicationCostType.MONETARY:
            if self.available_balance is None:
                return None
            return self.available_balance >= self.application_cost.amount
        
        return None
    
    def has_positive_expected_value(self) -> Optional[bool]:
        """Check if expected value is positive."""
        if self.expected_value is None:
            return None
        return self.expected_value > 0


@dataclass
class EconomicSafetyResult:
    """
    Result of economic safety gate evaluation.
    """
    status: EconomicSafetyStatus
    blocking_reason: Optional[str] = None
    metrics: Optional[EconomicMetrics] = None
    recommendations: list = field(default_factory=list)


class AccountEconomicsEngine:
    """
    Account-aware economics engine.
    
    Combines platform rules with actual account state to provide
    intelligent economics evaluation without automatic apply.
    """
    
    def __init__(self):
        """Initialize the account economics engine."""
        self._account_states: Dict[MarketplacePlatform, MarketplaceAccountState] = {}
    
    def register_account_state(self, account_state: MarketplaceAccountState) -> None:
        """
        Register account state for a platform.
        
        Args:
            account_state: Account state to register
        """
        self._account_states[account_state.platform] = account_state
    
    def get_account_state(self, platform: MarketplacePlatform) -> Optional[MarketplaceAccountState]:
        """
        Get account state for a platform.
        
        Args:
            platform: Marketplace platform
            
        Returns:
            Account state or None if not registered
        """
        return self._account_states.get(platform)
    
    def evaluate_application_economics(
        self,
        platform: MarketplacePlatform,
        job_data: Dict[str, Any],
        account_state: Optional[MarketplaceAccountState] = None,
    ) -> EconomicSafetyResult:
        """
        Evaluate application economics with account state awareness.
        
        Args:
            platform: Marketplace platform
            job_data: Job data
            account_state: Account state (optional, uses registered if not provided)
            
        Returns:
            Economic safety result
        """
        # Use registered account state if not provided
        if account_state is None:
            account_state = self.get_account_state(platform)
        
        # Get platform rules
        rules = get_platform_rules(platform)
        
        # Calculate metrics
        metrics = self._calculate_metrics(platform, job_data, account_state, rules)
        
        # Evaluate safety gate
        return self._evaluate_safety_gate(metrics, account_state, rules)
    
    def _calculate_metrics(
        self,
        platform: MarketplacePlatform,
        job_data: Dict[str, Any],
        account_state: Optional[MarketplaceAccountState],
        rules: PlatformRules,
    ) -> EconomicMetrics:
        """
        Calculate economic metrics.
        
        Args:
            platform: Marketplace platform
            job_data: Job data
            account_state: Account state
            rules: Platform rules
            
        Returns:
            Economic metrics
        """
        # Get application cost from platform rules
        platform_cost = rules.get_application_cost_for_job(job_data)
        
        # Determine if cost is known based on account state
        is_cost_known = platform_cost.is_cost_known()
        
        # Get available balance/credits from account state
        available_balance = None
        available_credits = None
        
        if account_state:
            if account_state.has_known_wallet():
                available_balance = account_state.wallet.available
            if account_state.has_known_credits():
                available_credits = account_state.credits.available
        
        # Extract expected value from job data if available
        expected_value = job_data.get("expected_value")
        win_probability = job_data.get("win_probability")
        
        # Calculate ROI if both expected value and cost are known
        roi = None
        if expected_value is not None and platform_cost.cost_amount is not None:
            if platform_cost.cost_type == ApplicationCostType.MONETARY:
                roi = (expected_value - platform_cost.cost_amount) / platform_cost.cost_amount if platform_cost.cost_amount > 0 else None
            elif platform_cost.cost_type == ApplicationCostType.CREDITS:
                # For credits, ROI calculation may differ based on credit value
                # This is a simplified calculation
                roi = expected_value  # Placeholder for credit-to-value conversion
        
        return EconomicMetrics(
            application_cost=ApplicationCost(
                cost_type=platform_cost.cost_type,
                amount=platform_cost.cost_amount,
                currency=platform_cost.currency,
                is_known=is_cost_known,
            ),
            available_balance=available_balance,
            available_credits=available_credits,
            expected_value=expected_value,
            win_probability=win_probability,
            roi=roi,
        )
    
    def _evaluate_safety_gate(
        self,
        metrics: EconomicMetrics,
        account_state: Optional[MarketplaceAccountState],
        rules: PlatformRules,
    ) -> EconomicSafetyResult:
        """
        Evaluate economic safety gate.
        
        Args:
            metrics: Economic metrics
            account_state: Account state
            rules: Platform rules
            
        Returns:
            Economic safety result
        """
        recommendations = []
        blocking_reason = None
        
        # Check if account state is known and fresh
        if account_state:
            if not account_state.is_data_fresh(rules.max_data_age_hours):
                blocking_reason = "Account data is stale"
                return EconomicSafetyResult(
                    status=EconomicSafetyStatus.NEED_RESEARCH,
                    blocking_reason=blocking_reason,
                    metrics=metrics,
                    recommendations=["Update account data"],
                )
            
            if not account_state.is_account_active():
                blocking_reason = f"Account status: {account_state.account_status.value}"
                return EconomicSafetyResult(
                    status=EconomicSafetyStatus.BLOCK,
                    blocking_reason=blocking_reason,
                    metrics=metrics,
                )
        else:
            # No account state registered
            blocking_reason = "Account state unknown"
            return EconomicSafetyResult(
                status=EconomicSafetyStatus.NEED_RESEARCH,
                blocking_reason=blocking_reason,
                metrics=metrics,
                recommendations=["Register account state"],
            )
        
        # Check if application cost is known
        if metrics.application_cost.is_unknown():
            blocking_reason = "Application cost unknown"
            return EconomicSafetyResult(
                status=EconomicSafetyStatus.NEED_RESEARCH,
                blocking_reason=blocking_reason,
                metrics=metrics,
                recommendations=["Determine application cost"],
            )
        
        # Check if balance/credits are sufficient
        balance_sufficient = metrics.is_balance_sufficient()
        
        if balance_sufficient is False:
            blocking_reason = "Insufficient balance/credits for application"
            return EconomicSafetyResult(
                status=EconomicSafetyStatus.BLOCK,
                blocking_reason=blocking_reason,
                metrics=metrics,
            )
        
        if balance_sufficient is None:
            blocking_reason = "Balance/credits unknown"
            return EconomicSafetyResult(
                status=EconomicSafetyStatus.NEED_RESEARCH,
                blocking_reason=blocking_reason,
                metrics=metrics,
                recommendations=["Check account balance/credits"],
            )
        
        # Check expected value
        if metrics.expected_value is not None and metrics.expected_value < 0:
            blocking_reason = "Negative expected value"
            return EconomicSafetyResult(
                status=EconomicSafetyStatus.BLOCK,
                blocking_reason=blocking_reason,
                metrics=metrics,
            )
        
        # All checks passed
        return EconomicSafetyResult(
            status=EconomicSafetyStatus.SAFE,
            metrics=metrics,
        )
    
    def get_account_summary(self, platform: MarketplacePlatform) -> Optional[Dict[str, Any]]:
        """
        Get account summary for a platform.
        
        Args:
            platform: Marketplace platform
            
        Returns:
            Account summary or None if not registered
        """
        account_state = self.get_account_state(platform)
        if account_state is None:
            return None
        
        rules = get_platform_rules(platform)
        
        return {
            "platform": platform.value,
            "account_status": account_state.account_status.value,
            "credits_available": account_state.credits.available,
            "credits_currency": account_state.credits.currency,
            "wallet_available": account_state.wallet.available,
            "wallet_currency": account_state.wallet.currency,
            "subscription": account_state.subscription.plan_name if account_state.subscription else None,
            "last_verified": account_state.last_verified_at,
            "freshness": account_state.freshness.value,
            "confidence": account_state.confidence,
            "source": account_state.source.value,
            "is_fresh": account_state.is_data_fresh(rules.max_data_age_hours),
        }
