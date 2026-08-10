"""
Marketplace Economics Integration.

Integrates economics engines with the decision pipeline.
"""
from typing import Any, Dict, Optional

from app.marketplace.contracts import MarketplacePlatform, NormalizedJob
from app.marketplace.economics import (
    ApplicationEconomics,
    EconomicAssessment,
    EconomicDecision,
)
from app.marketplace.economics_registry import economics_registry
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EconomicsIntegration:
    """
    Integrates marketplace economics into the decision pipeline.

    This is called after proposal generation to determine if
    the application is economically viable before requesting
    human approval.
    """

    def __init__(self) -> None:
        """Initialize economics integration."""
        self._registry = economics_registry

    async def evaluate_application(
        self,
        job: NormalizedJob,
        assessment: Optional[EconomicAssessment] = None,
    ) -> ApplicationEconomics:
        """
        Evaluate the economics of applying to a job.

        Args:
            job: The normalized job data
            assessment: Economic assessment of the job (revenue, probability, etc.)

        Returns:
            Complete application economics with decision
        """
        # Get the appropriate economics engine
        engine = self._registry.get(job.platform)
        if not engine:
            logger.warning(f"No economics engine found for platform: {job.platform}")
            # Return a default economics object with WAIT decision
            return self._create_default_economics(job, assessment)

        # Calculate economics using the platform-specific engine
        job_metadata = job.metadata or {}
        if job.platform_cost:
            job_metadata["required_connects"] = job.platform_cost.amount
            job_metadata["required_bids"] = job.platform_cost.amount
            job_metadata["required_offers"] = job.platform_cost.amount

        economics = await engine.calculate_economics(
            job_id=job.platform_job_id,
            assessment=assessment,
        )

        logger.info(
            f"Economics evaluation for job {job.platform_job_id}: "
            f"decision={economics.decision.value}, "
            f"reason={economics.decision_reason}"
        )

        return economics

    def _create_default_economics(
        self,
        job: NormalizedJob,
        assessment: Optional[EconomicAssessment] = None,
    ) -> ApplicationEconomics:
        """Create a default economics object when no engine is available."""
        from app.marketplace.economics import (
            AccountBalance,
            ApplicationCost,
            ApplicationUnit,
        )

        return ApplicationEconomics(
            job_id=job.platform_job_id,
            platform=job.platform,
            account_balance=AccountBalance(
                unit=ApplicationUnit.NONE,
                available=0.0,
                total=0.0,
                currency="USD",
            ),
            application_cost=ApplicationCost(
                unit=ApplicationUnit.NONE,
                amount=0.0,
                currency="USD",
                is_free=True,
                description="No economics engine available",
            ),
            assessment=assessment,
            decision=EconomicDecision.WAIT,
            decision_reason="No economics engine available for this platform",
        )

    def can_proceed_to_approval(self, economics: ApplicationEconomics) -> bool:
        """
        Determine if application can proceed to human approval.

        Args:
            economics: The application economics

        Returns:
            True if can proceed to approval, False otherwise
        """
        # Only proceed if decision is APPLY
        if economics.decision != EconomicDecision.APPLY:
            logger.info(
                f"Cannot proceed to approval: decision={economics.decision.value}, "
                f"reason={economics.decision_reason}"
            )
            return False

        # Verify economic factors
        if economics.assessment and economics.assessment.economic_value is not None:
            if economics.assessment.economic_value <= 0:
                logger.info(
                    f"Cannot proceed to approval: negative economic value "
                    f"({economics.assessment.economic_value})"
                )
                return False

        return True

    def get_economic_summary(self, economics: ApplicationEconomics) -> Dict[str, Any]:
        """
        Get a summary of the economics for display.

        Args:
            economics: The application economics

        Returns:
            Summary dictionary for frontend display
        """
        summary = {
            "platform": economics.platform.value,
            "decision": economics.decision.value,
            "decision_reason": economics.decision_reason,
            "can_afford": economics.can_afford,
            "has_quota": economics.has_quota,
            "meets_wallet_requirements": economics.meets_wallet_requirements,
        }

        # Add cost information
        if economics.application_cost:
            summary["application_cost"] = {
                "unit": economics.application_cost.unit.value,
                "amount": economics.application_cost.amount,
                "currency": economics.application_cost.currency,
                "monetary_value": economics.application_cost.monetary_value,
                "is_free": economics.application_cost.is_free,
            }

        # Add balance information
        if economics.account_balance:
            summary["account_balance"] = {
                "unit": economics.account_balance.unit.value,
                "available": economics.account_balance.available,
                "total": economics.account_balance.total,
                "currency": economics.account_balance.currency,
            }

        # Add remaining balance
        if economics.remaining_balance_after_apply is not None:
            summary["remaining_balance_after_apply"] = economics.remaining_balance_after_apply

        # Add assessment information
        if economics.assessment:
            summary["assessment"] = {
                "expected_revenue": economics.assessment.expected_revenue,
                "win_probability": economics.assessment.win_probability,
                "execution_readiness": economics.assessment.execution_readiness,
                "evidence_strength": economics.assessment.evidence_strength,
                "economic_value": economics.assessment.economic_value,
            }

        return summary


# Global economics integration instance
economics_integration = EconomicsIntegration()
