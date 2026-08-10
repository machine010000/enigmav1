"""
Khamsat Economics Engine.

Implements economics calculations for Khamsat's credit-based application model.
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


class KhamsatEconomicsEngine(EconomicsEngine):
    """
    Economics engine for Khamsat.

    Khamsat is an Arabic marketplace similar to Mostaql:
    - Uses credits/tokens for applications
    - Application model: CREDIT_BASED (with UNKNOWN verification status)
    - Pricing and limits are not verified
    """

    SOURCE = "khamsat_estimated_model"
    CONFIDENCE = 0.2  # Very low confidence - model not verified

    def __init__(self, account_data: Optional[Dict[str, Any]] = None):
        """
        Initialize with account data.

        Args:
            account_data: Account information including credit balance
        """
        self._account_data = account_data or {}
        self._verified_at = datetime.utcnow().isoformat()
        self._expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()  # Short expiry for unknown data

    @property
    def platform(self) -> MarketplacePlatform:
        return MarketplacePlatform.KHAMSAT

    @property
    def application_model(self) -> ApplicationModel:
        return ApplicationModel.CREDIT_BASED

    async def get_economics_contract(self) -> MarketplaceEconomicsContract:
        """
        Get the complete economics contract for Khamsat.

        Returns:
            MarketplaceEconomicsContract with UNKNOWN verification status
        """
        cash_cost = EconomicsValue(
            value=None,  # Unknown
            status=VerificationStatus.UNKNOWN,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        credit_cost = EconomicsValue(
            value=None,  # Unknown
            status=VerificationStatus.UNKNOWN,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        application_cost = MarketplaceCost(
            cash_cost=cash_cost,
            currency="SAR",
            credit_cost=credit_cost,
            credit_name="Credits",
        )

        minimum_balance = EconomicsValue(
            value=None,
            status=VerificationStatus.UNKNOWN,
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

        return MarketplaceEconomicsContract(
            platform=self.platform,
            currency="SAR",
            application_model=ApplicationModel.CREDIT_BASED,
            application_cost=application_cost,
            minimum_balance=minimum_balance,
            credit_name="Credits",
            credit_cost=credit_cost,
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

        Khamsat pricing is unknown - return UNKNOWN status.

        Args:
            job_id: Platform-specific job ID
            metadata: Job metadata (ignored)

        Returns:
            Application cost with UNKNOWN status
        """
        return ApplicationCost(
            unit=ApplicationUnit.KHAMSAT_CREDITS,
            amount=0.0,  # Unknown
            currency="SAR",
            monetary_value=None,  # Unknown
            is_free=False,
            description="Application cost unknown - pricing not verified",
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_account_balance(self) -> AccountBalance:
        """
        Get current account credit balance.

        Returns:
            Account balance (unknown)
        """
        credits_available = self._account_data.get("credits_available", 0)
        credits_total = self._account_data.get("credits_total", 0)

        return AccountBalance(
            unit=ApplicationUnit.KHAMSAT_CREDITS,
            available=float(credits_available),
            total=float(credits_total),
            currency="SAR",
            monetary_value=None,  # Unknown conversion rate
            last_updated=datetime.utcnow().isoformat(),
            source=self.SOURCE,
            verified_at=self._verified_at,
            expires_at=self._expires_at,
            confidence=self.CONFIDENCE,
        )

    async def get_quotas(self) -> List[ApplicationQuota]:
        """
        Get current application quotas.

        Khamsat quotas are unknown.

        Returns:
            Empty list (quotas unknown)
        """
        return []

    async def get_wallet_requirements(self) -> Optional[WalletRequirement]:
        """
        Get wallet/balance requirements.

        Khamsat wallet requirements are unknown.

        Returns:
            None (requirements unknown)
        """
        return None

    async def calculate_economics(
        self,
        job_id: str,
        assessment: Optional[EconomicAssessment] = None,
    ) -> ApplicationEconomics:
        """
        Calculate complete economics for application decision.

        Since Khamsat economics are unknown, return NEED_INFORMATION.

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

        # Since economics are unknown, return NEED_INFORMATION
        decision = EconomicDecision.NEED_INFORMATION
        decision_reason = "Khamsat pricing and economics are not verified. Please configure platform economics."

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
            remaining_balance_after_apply=None,
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

        Since Khamsat economics are unknown, return NEED_INFORMATION.

        Args:
            opportunity: Job/opportunity data
            user_balance: User's monetary balance
            available_credits: User's available Credits
            estimated_success_probability: Estimated success probability (0.0 to 1.0)
            expected_revenue: Expected revenue from the job

        Returns:
            ApplicationEconomics with NEED_INFORMATION decision
        """
        job_id = opportunity.get("job_id", "unknown")

        # Get cost and balance
        application_cost = await self.get_application_cost(job_id)
        
        # Use provided credits or account data
        if available_credits is not None:
            self._account_data["credits_available"] = available_credits
        
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

        # Since economics are unknown, return NEED_INFORMATION
        decision = EconomicDecision.NEED_INFORMATION
        decision_reason = "Khamsat pricing and economics are not verified. Please configure platform economics."

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
            remaining_balance_after_apply=None,
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
