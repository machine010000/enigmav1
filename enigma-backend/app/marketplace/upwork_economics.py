"""
Upwork Economics Engine.

Implements economics calculations for Upwork's Connect-based application model.
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


class UpworkEconomicsEngine(EconomicsEngine):
    """
    Economics engine for Upwork.

    Upwork uses Connects as the application unit:
    - Standard jobs: 1-6 Connects
    - Premium jobs: May require more Connects
    - Connects have monetary value ($0.15 per Connect)
    - Application model: CREDIT_BASED
    """

    CONNECT_COST_USD = 0.15  # Cost per Connect in USD (VERIFIED)
    SOURCE = "upwork_official_pricing"
    CONFIDENCE = 0.95  # High confidence in verified pricing

    def __init__(self, account_data: Optional[Dict[str, Any]] = None):
        """
        Initialize with account data.

        Args:
            account_data: Account information including Connects balance
        """
        self._account_data = account_data or {}
        self._verified_at = datetime.utcnow().isoformat()
        self._expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

    @property
    def platform(self) -> MarketplacePlatform:
        return MarketplacePlatform.UPWORK

    @property
    def application_model(self) -> ApplicationModel:
        return ApplicationModel.CREDIT_BASED

    async def get_economics_contract(self) -> MarketplaceEconomicsContract:
        """
        Get the complete economics contract for Upwork.

        Returns:
            MarketplaceEconomicsContract with verified Upwork economics
        """
        cash_cost = EconomicsValue(
            value=0.0,
            status=VerificationStatus.VERIFIED,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        credit_cost = EconomicsValue(
            value=self.CONNECT_COST_USD,
            status=VerificationStatus.VERIFIED,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        application_cost = MarketplaceCost(
            cash_cost=cash_cost,
            currency="USD",
            credit_cost=credit_cost,
            credit_name="Connects",
        )

        minimum_balance = EconomicsValue(
            value=0.0,
            status=VerificationStatus.NOT_APPLICABLE,
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
            credit_name="Connects",
            credit_cost=credit_cost,
            daily_limits={
                "applications": self._account_data.get("daily_application_limit", 50),
            },
            monthly_limits={
                "applications": self._account_data.get("monthly_application_limit", 200),
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

        Upwork Connect cost varies by job:
        - Standard jobs: 1-6 Connects
        - Premium jobs: May require more
        - The job metadata should include 'required_connects'

        Args:
            job_id: Platform-specific job ID
            metadata: Job metadata including 'required_connects'

        Returns:
            Application cost in Connects
        """
        metadata = metadata or {}
        required_connects = metadata.get("required_connects", 1)

        # Ensure minimum of 1 Connect
        required_connects = max(1, required_connects)

        monetary_value = required_connects * self.CONNECT_COST_USD

        return ApplicationCost(
            unit=ApplicationUnit.CONNECTS,
            amount=float(required_connects),
            currency="USD",
            monetary_value=monetary_value,
            is_free=False,
            description=f"{required_connects} Connects required",
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_account_balance(self) -> AccountBalance:
        """
        Get current account Connects balance.

        Returns:
            Account balance in Connects
        """
        connects_available = self._account_data.get("connects_available", 0)
        connects_total = self._account_data.get("connects_total", 0)

        monetary_value = connects_available * self.CONNECT_COST_USD

        return AccountBalance(
            unit=ApplicationUnit.CONNECTS,
            available=float(connects_available),
            total=float(connects_total),
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

        Upwork has daily and monthly application limits based on account tier.

        Returns:
            List of quota information
        """
        quotas = []

        # Daily quota
        daily_used = self._account_data.get("daily_applications_used", 0)
        daily_limit = self._account_data.get("daily_application_limit", 50)
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
        monthly_used = self._account_data.get("monthly_applications_used", 0)
        monthly_limit = self._account_data.get("monthly_application_limit", 300)
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

        return quotas

    async def get_wallet_requirements(self) -> Optional[WalletRequirement]:
        """
        Get wallet/balance requirements.

        Upwork doesn't have wallet requirements for applications,
        only Connects balance.

        Returns:
            None (not applicable)
        """
        return None

    async def calculate_economics(
        self,
        job_id: str,
        assessment: Optional[EconomicAssessment] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApplicationEconomics:
        """
        Calculate complete economics for application decision.

        Args:
            job_id: Platform-specific job ID
            assessment: Economic assessment of the job
            metadata: Job metadata including 'required_connects'

        Returns:
            Complete application economics
        """
        # Get cost and balance
        application_cost = await self.get_application_cost(job_id, metadata)
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

        if account_balance.available < application_cost.amount:
            decision = EconomicDecision.INSUFFICIENT_BALANCE
            decision_reason = f"Insufficient Connects: need {application_cost.amount}, have {account_balance.available}"
        elif any(q.is_exhausted for q in quotas):
            decision = EconomicDecision.INSUFFICIENT_QUOTA
            decision_reason = "Application quota exhausted"
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
            user_balance: User's monetary balance (not used for Upwork)
            available_credits: User's available Connects
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
            self._account_data["connects_available"] = available_credits
        
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
            decision_reason = f"Insufficient Connects: need {application_cost.amount}, have {account_balance.available}"
        elif any(q.is_exhausted for q in quotas):
            decision = EconomicDecision.INSUFFICIENT_QUOTA
            decision_reason = "Application quota exhausted"
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
