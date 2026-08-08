"""
Connects/Cost Protection for Marketplace Applications.

This module enforces cost checks before application submission,
preventing applications when insufficient credits/connects are available.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.marketplace.contracts import (
    PlatformCost,
    PlatformLimits,
    MarketplacePlatform,
    PlatformError,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CostCheckResult:
    """Result of a cost check."""
    can_submit: bool
    cost: PlatformCost
    available_credits: float
    reason: Optional[str] = None


class CostProtection:
    """
    Enforces cost protection before application submission.
    
    Checks that the user has sufficient credits/connects to submit
    an application before allowing submission.
    """
    
    def __init__(self) -> None:
        """Initialize cost protection."""
        self._platform_limits: Dict[MarketplacePlatform, PlatformLimits] = {}
    
    def update_limits(self, platform: MarketplacePlatform, limits: PlatformLimits) -> None:
        """
        Update platform limits for cost checking.
        
        Args:
            platform: The platform to update limits for
            limits: The current platform limits
        """
        self._platform_limits[platform] = limits
        logger.info(f"Updated limits for {platform}: {limits.credits_available} available")
    
    def check_submission_cost(
        self,
        platform: MarketplacePlatform,
        cost: PlatformCost,
    ) -> CostCheckResult:
        """
        Check if user can afford the application cost.
        
        Args:
            platform: The platform to submit to
            cost: The cost of the application
            
        Returns:
            CostCheckResult with decision and reason
        """
        # Get platform limits
        if platform not in self._platform_limits:
            logger.warning(f"No limits available for platform {platform}")
            return CostCheckResult(
                can_submit=False,
                cost=cost,
                available_credits=0.0,
                reason=f"No account information available for {platform}",
            )
        
        limits = self._platform_limits[platform]
        
        # Check if cost is free
        if cost.is_free:
            logger.info(f"Application is free for {platform}")
            return CostCheckResult(
                can_submit=True,
                cost=cost,
                available_credits=limits.credits_available,
                reason="Application is free",
            )
        
        # Check if user has sufficient credits
        if cost.amount > limits.credits_available:
            logger.warning(
                f"Insufficient credits for {platform}: "
                f"need {cost.amount}, have {limits.credits_available}"
            )
            return CostCheckResult(
                can_submit=False,
                cost=cost,
                available_credits=limits.credits_available,
                reason=(
                    f"Insufficient {cost.credit_type.value}: "
                    f"need {cost.amount}, have {limits.credits_available}"
                ),
            )
        
        # Check if account is restricted
        if limits.credits_available <= 0:
            logger.warning(f"Account has no available credits for {platform}")
            return CostCheckResult(
                can_submit=False,
                cost=cost,
                available_credits=limits.credits_available,
                reason="No available credits",
            )
        
        # Check daily limit
        if limits.daily_application_limit is not None and limits.daily_application_limit <= 0:
            logger.warning(f"Daily application limit reached for {platform}")
            return CostCheckResult(
                can_submit=False,
                cost=cost,
                available_credits=limits.credits_available,
                reason="Daily application limit reached",
            )
        
        # Check monthly limit
        if limits.monthly_application_limit is not None and limits.monthly_application_limit <= 0:
            logger.warning(f"Monthly application limit reached for {platform}")
            return CostCheckResult(
                can_submit=False,
                cost=cost,
                available_credits=limits.credits_available,
                reason="Monthly application limit reached",
            )
        
        # All checks passed
        logger.info(
            f"Cost check passed for {platform}: "
            f"cost {cost.amount}, available {limits.credits_available}"
        )
        
        return CostCheckResult(
            can_submit=True,
            cost=cost,
            available_credits=limits.credits_available,
            reason=None,
        )
    
    def deduct_cost(
        self,
        platform: MarketplacePlatform,
        cost: PlatformCost,
    ) -> None:
        """
        Deduct cost from available credits after successful submission.
        
        Args:
            platform: The platform submitted to
            cost: The cost that was deducted
        """
        if platform not in self._platform_limits:
            logger.warning(f"No limits available for platform {platform}")
            return
        
        limits = self._platform_limits[platform]
        
        if not cost.is_free:
            limits.credits_available -= cost.amount
            
            if limits.daily_application_limit is not None:
                limits.daily_application_limit -= 1
            
            if limits.monthly_application_limit is not None:
                limits.monthly_application_limit -= 1
            
            logger.info(
                f"Deducted {cost.amount} {cost.credit_type.value} from {platform}. "
                f"Remaining: {limits.credits_available}"
            )
    
    def get_available_credits(self, platform: MarketplacePlatform) -> Optional[float]:
        """
        Get available credits for a platform.
        
        Args:
            platform: The platform to check
            
        Returns:
            Available credits or None if not available
        """
        if platform not in self._platform_limits:
            return None
        
        return self._platform_limits[platform].credits_available


# Global cost protection instance
cost_protection = CostProtection()
