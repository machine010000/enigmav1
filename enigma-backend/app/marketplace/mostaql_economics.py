"""
Mostaql Economics Engine.

Implements economics calculations for Mostaql's offer-based application model.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .contracts import MarketplacePlatform
from .economics import (
    AccountBalance,
    ApplicationCost,
    ApplicationEconomics,
    ApplicationModel,
    ApplicationQuota,
    ApplicationUnit,
    EconomicsValue,
    EconomicAssessment,
    EconomicDecision,
    EconomicsEngine,
    MarketplaceCost,
    MarketplaceEconomicsContract,
    QuotaType,
    VerificationStatus,
    WalletRequirement,
)


class MostaqlEconomicsEngine(EconomicsEngine):
    """
    Economics engine for Mostaql.

    Mostaql uses Offers as the application unit:
    - Free members: Limited offers per month
    - Paid members: More offers per month
    - Daily and rolling-period limits
    - Application model: CREDIT_BASED (with UNKNOWN verification status)
    """

    OFFER_COST_USD = 0.15  # Cost per offer in USD (UNKNOWN - not verified)
    SOURCE = "mostaql_estimated_pricing"
    CONFIDENCE = 0.3  # Low confidence - pricing not verified

    def __init__(self, account_data: Optional[Dict[str, Any]] = None):
        """
        Initialize with account data.

        Args:
            account_data: Account information including offer balance
        """
        self._account_data = account_data or {}
        self._verified_at = datetime.utcnow().isoformat()
        self._expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()  # Short expiry for unknown data

    @property
    def platform(self) -> MarketplacePlatform:
        return MarketplacePlatform.MOSTAQL

    @property
    def application_model(self) -> ApplicationModel:
        return ApplicationModel.CREDIT_BASED

    async def get_economics_contract(self) -> MarketplaceEconomicsContract:
        """
        Get the complete economics contract for Mostaql.

        Returns:
            MarketplaceEconomicsContract with UNKNOWN verification status
        """
        cash_cost = EconomicsValue(
            value=0.0,
            status=VerificationStatus.UNKNOWN,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        credit_cost = EconomicsValue(
            value=self.OFFER_COST_USD,
            status=VerificationStatus.UNKNOWN,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        application_cost = MarketplaceCost(
            cash_cost=cash_cost,
            currency="USD",
            credit_cost=credit_cost,
            credit_name="Offers",
        )

        minimum_balance = EconomicsValue(
            value=self._account_data.get("minimum_wallet_balance", 0),
            status=VerificationStatus.UNKNOWN,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        return MarketplaceEconomicsContract(
            platform=self.platform,
            currency="USD",
            application_model=ApplicationModel.CREDIT_BASED,
            application_cost=application_cost,
            minimum_balance=minimum_balance,
            credit_name="Offers",
            credit_cost=credit_cost,
            daily_limits={
                "offers": self._account_data.get("daily_offer_limit", 20),
            },
            monthly_limits={
                "offers": self._account_data.get("monthly_offer_limit", 200),
            },
            weekly_limits={
                "offers": self._account_data.get("rolling_offer_limit", 50),
            },
            last_verified_at=self._verified_at,
            source=self.SOURCE,
            confidence=self.CONFIDENCE,
            expires_at=self._expires_at,
        )

    async def get_application_cost(
        self,
        job_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApplicationCost:
        """
        Calculate the cost to apply to a job.

        Mostaql typically costs 1 offer per application.

        Args:
            job_id: Platform-specific job ID
            metadata: Job metadata including 'required_offers'

        Returns:
            Application cost in Offers
        """
        metadata = metadata or {}
        required_offers = metadata.get("required_offers", 1)

        # Ensure minimum of 1 offer
        required_offers = max(1, required_offers)

        monetary_value = required_offers * self.OFFER_COST_USD

        return ApplicationCost(
            unit=ApplicationUnit.OFFERS,
            amount=float(required_offers),
            currency="USD",
            monetary_value=monetary_value,
            is_free=False,
            description=f"{required_offers} offer(s) required",
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_account_balance(self) -> AccountBalance:
        """
        Get current account offer balance.

        Returns:
            Account balance in Offers
        """
        offers_available = self._account_data.get("offers_available", 0)
        offers_total = self._account_data.get("offers_total", 0)

        monetary_value = offers_available * self.OFFER_COST_USD

        return AccountBalance(
            unit=ApplicationUnit.OFFERS,
            available=float(offers_available),
            total=float(offers_total),
            currency="USD",
            monetary_value=monetary_value,
            last_updated=datetime.utcnow().isoformat(),
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_quotas(self) -> List[ApplicationQuota]:
        """
        Get current application quotas.

        Mostaql has daily, monthly, and rolling-period quotas.

        Returns:
            List of quota information
        """
        quotas = []

        # Daily quota
        daily_used = self._account_data.get("daily_offers_used", 0)
        daily_limit = self._account_data.get("daily_offer_limit", 20)
        quotas.append(
            ApplicationQuota(
                quota_type=QuotaType.DAILY,
                used=daily_used,
                limit=daily_limit,
                reset_at=(datetime.utcnow() + timedelta(days=1)).isoformat(),
                period_start=datetime.utcnow().isoformat(),
                source=self.SOURCE,
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=self.CONFIDENCE,
            )
        )

        # Monthly quota
        monthly_used = self._account_data.get("monthly_offers_used", 0)
        monthly_limit = self._account_data.get("monthly_offer_limit", 200)
        quotas.append(
            ApplicationQuota(
                quota_type=QuotaType.MONTHLY,
                used=monthly_used,
                limit=monthly_limit,
                reset_at=(datetime.utcnow() + timedelta(days=30)).isoformat(),
                period_start=datetime.utcnow().isoformat(),
                source=self.SOURCE,
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=self.CONFIDENCE,
            )
        )

        # Rolling period quota (e.g., 7-day rolling)
        rolling_used = self._account_data.get("rolling_offers_used", 0)
        rolling_limit = self._account_data.get("rolling_offer_limit", 50)
        rolling_days = self._account_data.get("rolling_period_days", 7)
        quotas.append(
            ApplicationQuota(
                quota_type=QuotaType.ROLLING,
                used=rolling_used,
                limit=rolling_limit,
                reset_at=(datetime.utcnow() + timedelta(days=rolling_days)).isoformat(),
                period_start=datetime.utcnow().isoformat(),
                source=self.SOURCE,
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=self.CONFIDENCE,
            )
        )

        return quotas

    async def get_wallet_requirements(self) -> Optional[WalletRequirement]:
        """
        Get wallet/balance requirements.

        Mostaql may require minimum wallet balance for certain projects.

        Returns:
            Wallet requirements or None
        """
        min_balance = self._account_data.get("minimum_wallet_balance")
        if min_balance:
            min_balance_value = EconomicsValue(
                value=float(min_balance),
                status=VerificationStatus.UNKNOWN,
                source=self.SOURCE,
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=self.CONFIDENCE,
            )
            return WalletRequirement(
                minimum_balance=min_balance_value,
                currency="USD",
                description="Minimum wallet balance for project eligibility",
                source=self.SOURCE,
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=self.CONFIDENCE,
            )
        return None

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
        # Get cost and balance
        application_cost = await self.get_application_cost(job_id)
        account_balance = await self.get_account_balance()
        quotas = await self.get_quotas()
        wallet_requirements = await self.get_wallet_requirements()

        # Calculate remaining balance after application
        remaining_balance = None
        if not application_cost.is_free:
            remaining_balance = max(0, account_balance.available - application_cost.amount)

        # Determine decision
        decision = EconomicDecision.WAIT
        decision_reason = ""

        if not account_balance.available >= application_cost.amount:
            decision = EconomicDecision.INSUFFICIENT_BALANCE
            decision_reason = f"Insufficient Offers: need {application_cost.amount}, have {account_balance.available}"
        elif any(q.is_exhausted for q in quotas):
            decision = EconomicDecision.INSUFFICIENT_QUOTA
            decision_reason = "Offer quota exhausted"
        elif wallet_requirements and account_balance.monetary_value < wallet_requirements.minimum_balance:
            decision = EconomicDecision.INSUFFICIENT_BALANCE
            decision_reason = f"Insufficient wallet balance: need ${wallet_requirements.minimum_balance}"
        elif assessment and assessment.economic_value is not None:
            if assessment.economic_value > 0:
                decision = EconomicDecision.APPLY
                decision_reason = "Positive economic value"
            else:
                decision = EconomicDecision.DONT_APPLY
                decision_reason = "Negative economic value"
        else:
            decision = EconomicDecision.WAIT
            decision_reason = "Insufficient economic assessment data"

        return ApplicationEconomics(
            job_id=job_id,
            platform=self.platform,
            account_balance=account_balance,
            application_cost=application_cost,
            quotas=quotas,
            wallet_requirements=wallet_requirements,
            assessment=assessment,
            decision=decision,
            decision_reason=decision_reason,
            remaining_balance_after_apply=remaining_balance,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

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
            available_credits: User's available Offers
            estimated_success_probability: Estimated success probability (0.0 to 1.0)
            expected_revenue: Expected revenue from the job

        Returns:
            ApplicationEconomics with detailed decision
        """
        job_id = opportunity.get("job_id", "unknown")
        metadata = opportunity.get("metadata", {})

        # Get cost and balance
        application_cost = await self.get_application_cost(job_id, metadata)
        
        # Use provided credits or account data
        if available_credits is not None:
            self._account_data["offers_available"] = available_credits
        
        account_balance = await self.get_account_balance()
        quotas = await self.get_quotas()
        wallet_requirements = await self.get_wallet_requirements()

        # Build assessment if revenue and probability provided
        assessment = None
        if expected_revenue is not None and estimated_success_probability is not None:
            expected_revenue_value = EconomicsValue(
                value=expected_revenue,
                status=VerificationStatus.UNKNOWN,
                source="user_estimation",
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=0.5,
            )
            
            win_probability = EconomicsValue(
                value=estimated_success_probability,
                status=VerificationStatus.UNKNOWN,
                source="user_estimation",
                verified_at=self._verified_at,
                expires_at=self._expires_at,
                confidence=0.5,
            )
            
            assessment = EconomicAssessment(
                expected_revenue=expected_revenue_value,
                win_probability=win_probability,
                application_cost=application_cost,
            )

        # Calculate remaining balance after application
        remaining_balance = None
        if not application_cost.is_free:
            remaining_balance = max(0, account_balance.available - application_cost.amount)

        # Determine decision
        decision = EconomicDecision.WAIT
        decision_reason = ""

        # Check if economics data is stale
        contract = await self.get_economics_contract()
        if contract.is_stale():
            decision = EconomicDecision.NEED_INFORMATION
            decision_reason = "Platform economics data is stale. Please refresh."
        elif not account_balance.available >= application_cost.amount:
            decision = EconomicDecision.INSUFFICIENT_BALANCE
            decision_reason = f"Insufficient Offers: need {application_cost.amount}, have {account_balance.available}"
        elif any(q.is_exhausted for q in quotas):
            decision = EconomicDecision.INSUFFICIENT_QUOTA
            decision_reason = "Offer quota exhausted"
        elif wallet_requirements and wallet_requirements.minimum_balance.value and account_balance.monetary_value < wallet_requirements.minimum_balance.value:
            decision = EconomicDecision.REQUIRES_MONEY
            decision_reason = f"Insufficient wallet balance: need ${wallet_requirements.minimum_balance.value}"
        elif assessment and assessment.economic_value is not None:
            if assessment.economic_value > 0:
                decision = EconomicDecision.APPLY
                decision_reason = "Positive economic value"
            else:
                decision = EconomicDecision.DONT_APPLY
                decision_reason = "Negative economic value"
        else:
            decision = EconomicDecision.WAIT
            decision_reason = "Insufficient economic assessment data"

        return ApplicationEconomics(
            job_id=job_id,
            platform=self.platform,
            account_balance=account_balance,
            application_cost=application_cost,
            quotas=quotas,
            wallet_requirements=wallet_requirements,
            assessment=assessment,
            decision=decision,
            decision_reason=decision_reason,
            remaining_balance_after_apply=remaining_balance,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    def update_account_data(self, account_data: Dict[str, Any]) -> None:
        """
        Update account data for calculations.

        Args:
            account_data: New account data
        """
        self._account_data.update(account_data)
