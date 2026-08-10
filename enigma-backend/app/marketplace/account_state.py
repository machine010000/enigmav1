"""
Marketplace Account State

Canonical account state representation for marketplace platforms.
Separates platform rules from actual account state.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

from app.marketplace.contracts import MarketplacePlatform


class AccountStatus(str, Enum):
    """Account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class DataSource(str, Enum):
    """Source of account data."""
    MANUAL_INPUT = "manual_input"
    API_INTEGRATION = "api_integration"
    MOCK_ADAPTER = "mock_adapter"
    UNKNOWN = "unknown"


class FreshnessStatus(str, Enum):
    """Freshness of account data."""
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass
class CreditBalance:
    """
    Credit balance for platforms using credits/tokens.
    """
    available: Optional[int] = None  # None means unknown
    pending: int = 0
    used: int = 0
    limit: Optional[int] = None  # None means no limit or unknown
    currency: Optional[str] = None  # e.g., "Connects", "Credits"
    
    def is_available_known(self) -> bool:
        """Check if available credits are known."""
        return self.available is not None
    
    def is_sufficient(self, required: int) -> Optional[bool]:
        """
        Check if credits are sufficient for required amount.
        
        Returns:
            True if sufficient, False if insufficient, None if unknown
        """
        if not self.is_available_known():
            return None
        return self.available >= required


@dataclass
class WalletBalance:
    """
    Wallet/balance for platforms using monetary balance.
    """
    available: Optional[float] = None  # None means unknown
    currency: str = "USD"
    
    def is_available_known(self) -> bool:
        """Check if available balance is known."""
        return self.available is not None
    
    def is_sufficient(self, required: float) -> Optional[bool]:
        """
        Check if balance is sufficient for required amount.
        
        Returns:
            True if sufficient, False if insufficient, None if unknown
        """
        if not self.is_available_known():
            return None
        return self.available >= required


@dataclass
class SubscriptionPlan:
    """
    Subscription/plan information if applicable.
    """
    plan_name: Optional[str] = None
    plan_type: Optional[str] = None  # e.g., "basic", "premium"
    expires_at: Optional[str] = None
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketplaceAccountState:
    """
    Canonical marketplace account state.
    
    Represents the actual state of an account on a marketplace platform,
    separate from platform rules and economics calculations.
    """
    platform: MarketplacePlatform
    account_id: Optional[str] = None
    account_status: AccountStatus = AccountStatus.UNKNOWN
    
    # Credits/Tokens
    credits: CreditBalance = field(default_factory=CreditBalance)
    
    # Wallet/Balance
    wallet: WalletBalance = field(default_factory=WalletBalance)
    
    # Subscription/Plan
    subscription: Optional[SubscriptionPlan] = None
    
    # Metadata
    last_verified_at: Optional[str] = None
    source: DataSource = DataSource.UNKNOWN
    confidence: float = 0.5  # 0.0 to 1.0
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    
    # Additional platform-specific data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_data_fresh(self, max_age_hours: int = 24) -> bool:
        """
        Check if account data is fresh.
        
        Args:
            max_age_hours: Maximum age in hours to consider data fresh
            
        Returns:
            True if data is fresh, False otherwise
        """
        if self.freshness == FreshnessStatus.EXPIRED:
            return False
        
        if self.last_verified_at is None:
            return self.freshness == FreshnessStatus.FRESH
        
        try:
            verified_time = datetime.fromisoformat(self.last_verified_at)
            age_hours = (datetime.utcnow() - verified_time).total_seconds() / 3600
            return age_hours < max_age_hours
        except (ValueError, TypeError):
            return False
    
    def has_known_credits(self) -> bool:
        """Check if credit balance is known."""
        return self.credits.is_available_known()
    
    def has_known_wallet(self) -> bool:
        """Check if wallet balance is known."""
        return self.wallet.is_available_known()
    
    def is_account_active(self) -> bool:
        """Check if account is active."""
        return self.account_status in [
            AccountStatus.ACTIVE,
            AccountStatus.VERIFIED,
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "platform": self.platform.value,
            "account_id": self.account_id,
            "account_status": self.account_status.value,
            "credits": {
                "available": self.credits.available,
                "pending": self.credits.pending,
                "used": self.credits.used,
                "limit": self.credits.limit,
                "currency": self.credits.currency,
            },
            "wallet": {
                "available": self.wallet.available,
                "currency": self.wallet.currency,
            },
            "subscription": {
                "plan_name": self.subscription.plan_name if self.subscription else None,
                "plan_type": self.subscription.plan_type if self.subscription else None,
                "expires_at": self.subscription.expires_at if self.subscription else None,
            } if self.subscription else None,
            "last_verified_at": self.last_verified_at,
            "source": self.source.value,
            "confidence": self.confidence,
            "freshness": self.freshness.value,
            "metadata": self.metadata,
        }
