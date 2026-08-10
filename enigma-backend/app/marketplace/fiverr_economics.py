"""
Fiverr Economics Engine.

Implements economics calculations for Fiverr's gig/service economy model.
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


class FiverrEconomicsEngine(EconomicsEngine):
    """
    Economics engine for Fiverr.

    Fiverr uses a gig/service economy model:
    - No bid-based applications
    - Sellers create gigs/services
    - Clients initiate orders
    - Application Cost = NOT_APPLICABLE
    - Application Unit = NONE
    - Application model: NO_DIRECT_APPLICATION
    """

    SOURCE = "fiverr_official_model"
    CONFIDENCE = 0.9  # High confidence in model understanding

    def __init__(self, account_data: Optional[Dict[str, Any]] = None):
        """
        Initialize with account data.

        Args:
            account_data: Account information
        """
        self._account_data = account_data or {}
        self._verified_at = datetime.utcnow().isoformat()
        self._expires_at = (datetime.utcnow() + timedelta(days=90)).isoformat()  # Model changes rarely

    @property
    def platform(self) -> MarketplacePlatform:
        return MarketplacePlatform.FIVERR

    @property
    def application_model(self) -> ApplicationModel:
        return ApplicationModel.NO_DIRECT_APPLICATION

    async def get_economics_contract(self) -> MarketplaceEconomicsContract:
        """
        Get the complete economics contract for Fiverr.

        Returns:
            MarketplaceEconomicsContract with NO_DIRECT_APPLICATION model
        """
        cash_cost = EconomicsValue(
            value=0.0,
            status=VerificationStatus.NOT_APPLICABLE,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        application_cost = MarketplaceCost(
            cash_cost=cash_cost,
            currency="USD",
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
            application_model=ApplicationModel.NO_DIRECT_APPLICATION,
            application_cost=application_cost,
            minimum_balance=minimum_balance,
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

        Fiverr has no application cost (gig economy model).

        Args:
            job_id: Platform-specific job ID
            metadata: Job metadata (ignored)

        Returns:
            Free application cost
        """
        return ApplicationCost(
            unit=ApplicationUnit.NONE,
            amount=0.0,
            currency="USD",
            monetary_value=0.0,
            is_free=True,
            description="No application cost (gig economy - clients initiate orders)",
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_account_balance(self) -> AccountBalance:
        """
        Get current account balance.

        Fiverr doesn't have application units, but may have wallet balance.

        Returns:
            Account balance (wallet balance in USD)
        """
        wallet_balance = self._account_data.get("wallet_balance", 0.0)

        return AccountBalance(
            unit=ApplicationUnit.NONE,
            available=float(wallet_balance),
            total=float(wallet_balance),
            currency="USD",
            monetary_value=float(wallet_balance),
            last_updated=datetime.utcnow().isoformat(),
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_quotas(self) -> List[ApplicationQuota]:
        """
        Get current application quotas.

        Fiverr has no application quotas (gig economy model).

        Returns:
            Empty list (no quotas)
        """
        return []

    async def get_wallet_requirements(self) -> Optional[WalletRequirement]:
        """
        Get wallet/balance requirements.

        Fiverr may require minimum balance for certain features.

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
                description="Minimum wallet balance for seller features",
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

        Since Fiverr is a gig economy, the decision is based purely on
        economic assessment, not on application costs or quotas.

        Args:
            job_id: Platform-specific job ID
            assessment: Economic assessment of the job

        Returns:
            Complete application economics
        """
        # Get cost and balance (both free/none)
        application_cost = await self.get_application_cost(job_id)
        account_balance = await self.get_account_balance()
        quotas = await self.get_quotas()
        wallet_requirements = await self.get_wallet_requirements()

        # Determine decision based on economic assessment
        decision = EconomicDecision.WAIT
        decision_reason = ""

        if assessment and assessment.economic_value is not None:
            if assessment.economic_value > 0:
                decision = EconomicDecision.APPLY
                decision_reason = "Positive economic value (gig economy)"
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
            remaining_balance_after_apply=account_balance.available,
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

        Since Fiverr is a gig economy, the decision is based purely on
        economic assessment, not on application costs or quotas.

        Args:
            opportunity: Job/opportunity data
            user_balance: User's monetary balance
            available_credits: Not applicable for Fiverr
            estimated_success_probability: Estimated success probability (0.0 to 1.0)
            expected_revenue: Expected revenue from the job

        Returns:
            ApplicationEconomics with detailed decision
        """
        job_id = opportunity.get("job_id", "unknown")

        # Get cost and balance (both free/none)
        application_cost = await self.get_application_cost(job_id)
        
        # Use provided balance or account data
        if user_balance is not None:
            self._account_data["wallet_balance"] = user_balance
        
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

        # Determine decision based on economic assessment
        decision = EconomicDecision.WAIT
        decision_reason = ""

        # Check if economics data is stale
        contract = await self.get_economics_contract()
        if contract.is_stale():
            decision = EconomicDecision.NEED_INFORMATION
            decision_reason = "Platform economics data is stale. Please refresh."
        elif assessment and assessment.economic_value is not None:
            if assessment.economic_value > 0:
                decision = EconomicDecision.APPLY
                decision_reason = "Positive economic value (gig economy)"
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
            remaining_balance_after_apply=account_balance.available,
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
