"""
Platform Rules

Platform-specific rules separate from account state.
Defines the rules and constraints for each marketplace platform.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.marketplace.contracts import MarketplacePlatform


class ApplicationCostType(str, Enum):
    """Type of application cost."""
    CREDITS = "credits"
    MONETARY = "monetary"
    FREE = "free"
    UNKNOWN = "unknown"


@dataclass
class PlatformApplicationCost:
    """
    Platform-specific application cost rules.
    """
    cost_type: ApplicationCostType
    cost_amount: Optional[float] = None  # None means unknown
    currency: Optional[str] = None  # e.g., "Connects", "USD"
    
    def is_cost_known(self) -> bool:
        """Check if cost is known."""
        return self.cost_type != ApplicationCostType.UNKNOWN and self.cost_amount is not None
    
    def is_free(self) -> bool:
        """Check if application is free."""
        return self.cost_type == ApplicationCostType.FREE


@dataclass
class PlatformRules:
    """
    Platform-specific rules and constraints.
    
    Separated from actual account state to allow for rule updates
    without affecting account data.
    """
    platform: MarketplacePlatform
    
    # Application Cost Rules
    application_cost: PlatformApplicationCost = field(
        default_factory=lambda: PlatformApplicationCost(cost_type=ApplicationCostType.UNKNOWN)
    )
    
    # Credit Rules
    requires_credits: bool = False
    credit_currency: Optional[str] = None  # e.g., "Connects"
    
    # Wallet Rules
    requires_wallet: bool = False
    wallet_currency: str = "USD"
    
    # Subscription Rules
    requires_subscription: bool = False
    allowed_plans: list = field(default_factory=list)
    
    # Freshness Rules
    max_data_age_hours: int = 24  # Maximum age for data to be considered fresh
    
    # Additional platform-specific rules
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_application_cost_for_job(self, job_data: Dict[str, Any]) -> PlatformApplicationCost:
        """
        Get application cost for a specific job.
        
        Args:
            job_data: Job data
            
        Returns:
            Application cost for this job
        """
        # Default to platform's base cost
        return self.application_cost
    
    def is_data_stale(self, last_verified_at: Optional[str]) -> bool:
        """
        Check if data is stale based on platform rules.
        
        Args:
            last_verified_at: Last verification timestamp
            
        Returns:
            True if data is stale
        """
        if last_verified_at is None:
            return True
        
        try:
            verified_time = datetime.fromisoformat(last_verified_at)
            age_hours = (datetime.utcnow() - verified_time).total_seconds() / 3600
            return age_hours >= self.max_data_age_hours
        except (ValueError, TypeError):
            return True


# Platform-specific rule configurations
UPWORK_RULES = PlatformRules(
    platform=MarketplacePlatform.UPWORK,
    application_cost=PlatformApplicationCost(
        cost_type=ApplicationCostType.CREDITS,
        cost_amount=2,  # Default 2 Connects
        currency="Connects",
    ),
    requires_credits=True,
    credit_currency="Connects",
    max_data_age_hours=24,
)

FREELANCER_RULES = PlatformRules(
    platform=MarketplacePlatform.FREELANCER,
    application_cost=PlatformApplicationCost(
        cost_type=ApplicationCostType.MONETARY,
        cost_amount=0.50,  # Default bid fee
        currency="USD",
    ),
    requires_wallet=True,
    wallet_currency="USD",
    max_data_age_hours=24,
)

FIVERR_RULES = PlatformRules(
    platform=MarketplacePlatform.FIVERR,
    application_cost=PlatformApplicationCost(
        cost_type=ApplicationCostType.FREE,
    ),
    max_data_age_hours=48,
)

MOSTAQL_RULES = PlatformRules(
    platform=MarketplacePlatform.MOSTAQL,
    application_cost=PlatformApplicationCost(
        cost_type=ApplicationCostType.FREE,
    ),
    max_data_age_hours=48,
)

KHAMSAT_RULES = PlatformRules(
    platform=MarketplacePlatform.KHAMSAT,
    application_cost=PlatformApplicationCost(
        cost_type=ApplicationCostType.FREE,
    ),
    max_data_age_hours=48,
)


def get_platform_rules(platform: MarketplacePlatform) -> PlatformRules:
    """
    Get platform rules for a specific platform.
    
    Args:
        platform: Marketplace platform
        
    Returns:
        Platform rules
    """
    rules_map = {
        MarketplacePlatform.UPWORK: UPWORK_RULES,
        MarketplacePlatform.FREELANCER: FREELANCER_RULES,
        MarketplacePlatform.FIVERR: FIVERR_RULES,
        MarketplacePlatform.MOSTAQL: MOSTAQL_RULES,
        MarketplacePlatform.KHAMSAT: KHAMSAT_RULES,
    }
    
    return rules_map.get(platform, PlatformRules(platform=platform))
