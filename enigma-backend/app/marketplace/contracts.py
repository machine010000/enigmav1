"""
Marketplace Adapter Foundation Contracts.

These contracts define the abstraction layer between Enigma and
marketplace platforms (Upwork, Fiverr, Freelancer, etc.).

The core Enigma system only interacts with normalized data through
these contracts, never directly with platform-specific APIs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class MarketplacePlatform(str, Enum):
    """Supported marketplace platforms."""
    MOCK = "mock"
    UPWORK = "upwork"
    FIVERR = "fiverr"
    FREELANCER = "freelancer"
    PEOPLE_PER_HOUR = "people_per_hour"
    GURU = "guru"


class AccountStatus(str, Enum):
    """Account status on marketplace."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RESTRICTED = "restricted"
    VERIFICATION_PENDING = "verification_pending"
    UNKNOWN = "unknown"


class CreditType(str, Enum):
    """Types of credits/credits on marketplaces."""
    CONNECTS = "connects"  # Upwork
    BIDS = "bids"  # Fiverr
    TOKENS = "tokens"  # Generic
    FREE_APPLICATIONS = "free_applications"
    PAID_APPLICATIONS = "paid_applications"


class ApplicationStatus(str, Enum):
    """Application status on marketplace."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    WITHDRAWN = "withdrawn"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class PlatformCapability(str, Enum):
    """Platform capabilities."""
    JOB_DISCOVERY = "job_discovery"
    JOB_RETRIEVAL = "job_retrieval"
    APPLICATION_SUBMISSION = "application_submission"
    APPLICATION_STATUS_TRACKING = "application_status_tracking"
    CREDIT_MANAGEMENT = "credit_management"
    ACCOUNT_STATUS_CHECK = "account_status_check"
    BUDGET_NEGOTIATION = "budget_negotiation"
    MESSAGING = "messaging"


@dataclass
class PlatformCost:
    """Cost of applying to a job on a platform."""
    credit_type: CreditType
    amount: float
    currency: str = "USD"
    is_free: bool = False
    description: str = ""


@dataclass
class PlatformLimits:
    """Platform limits for the account."""
    daily_application_limit: Optional[int] = None
    monthly_application_limit: Optional[int] = None
    credits_available: float = 0.0
    credits_total: float = 0.0
    credit_type: CreditType = CreditType.CONNECTS
    free_applications_remaining: Optional[int] = None
    paid_applications_allowed: bool = True


@dataclass
class MarketplaceAccount:
    """Account information on a marketplace."""
    platform: MarketplacePlatform
    account_id: str
    username: str
    status: AccountStatus
    is_authenticated: bool = False
    limits: PlatformLimits = field(default_factory=PlatformLimits)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_synced_at: Optional[datetime] = None


@dataclass
class PlatformError:
    """Platform-specific error."""
    platform: MarketplacePlatform
    error_code: str
    error_message: str
    is_retriable: bool = False
    is_auth_error: bool = False
    is_rate_limit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedJob:
    """Normalized job data from any marketplace."""
    job_id: str
    platform: MarketplacePlatform
    platform_job_id: str
    title: str
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_type: Optional[str] = None  # "hourly", "fixed", "negotiable"
    currency: str = "USD"
    client_info: Dict[str, Any] = field(default_factory=dict)
    skills_required: List[str] = field(default_factory=list)
    job_type: Optional[str] = None  # "one-time", "ongoing", "milestone"
    duration: Optional[str] = None  # "less_than_1_week", "1-3_months", etc.
    posted_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    platform_cost: Optional[PlatformCost] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedApplication:
    """Normalized application data for any marketplace."""
    application_id: str
    platform: MarketplacePlatform
    job_id: str
    platform_job_id: str
    platform_application_id: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.DRAFT
    submitted_at: Optional[datetime] = None
    proposal_text: str = ""
    cover_letter: str = ""
    attachments: List[str] = field(default_factory=list)
    bid_amount: Optional[float] = None
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarketplaceAdapter(ABC):
    """
    Abstract base class for marketplace adapters.
    
    Each marketplace (Upwork, Fiverr, Freelancer, etc.) implements
    this interface to provide normalized data to the Enigma core system.
    """

    @property
    @abstractmethod
    def platform(self) -> MarketplacePlatform:
        """Get the platform this adapter handles."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[PlatformCapability]:
        """Get the capabilities supported by this adapter."""
        pass

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> MarketplaceAccount:
        """
        Authenticate with the marketplace.
        
        Args:
            credentials: Platform-specific credentials
            
        Returns:
            MarketplaceAccount with authentication status
        """
        pass

    @abstractmethod
    async def get_account_status(self) -> MarketplaceAccount:
        """
        Get current account status.
        
        Returns:
            MarketplaceAccount with current status and limits
        """
        pass

    @abstractmethod
    async def discover_jobs(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[NormalizedJob]:
        """
        Discover jobs on the marketplace.
        
        Args:
            query: Search query
            filters: Platform-specific filters
            limit: Maximum number of jobs to return
            
        Returns:
            List of normalized jobs
        """
        pass

    @abstractmethod
    async def get_job(self, platform_job_id: str) -> NormalizedJob:
        """
        Get a specific job from the marketplace.
        
        Args:
            platform_job_id: Platform-specific job ID
            
        Returns:
            Normalized job data
        """
        pass

    @abstractmethod
    async def submit_application(
        self,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """
        Submit an application to the marketplace.
        
        Args:
            application: Normalized application data
            
        Returns:
            Normalized application with platform_application_id and status
        """
        pass

    @abstractmethod
    async def get_application_status(
        self,
        platform_application_id: str,
    ) -> ApplicationStatus:
        """
        Get the status of an application.
        
        Args:
            platform_application_id: Platform-specific application ID
            
        Returns:
            Application status
        """
        pass

    @abstractmethod
    async def get_platform_cost(self, platform_job_id: str) -> PlatformCost:
        """
        Get the cost to apply to a job.
        
        Args:
            platform_job_id: Platform-specific job ID
            
        Returns:
            Platform cost information
        """
        pass

    @abstractmethod
    async def check_limits(self) -> PlatformLimits:
        """
        Check current platform limits.
        
        Returns:
            Current platform limits
        """
        pass


class AdapterRegistry:
    """
    Registry for marketplace adapters.
    
    Manages the available adapters and provides lookup by platform.
    """

    def __init__(self) -> None:
        self._adapters: Dict[MarketplacePlatform, MarketplaceAdapter] = {}

    def register(self, adapter: MarketplaceAdapter) -> None:
        """Register a marketplace adapter."""
        self._adapters[adapter.platform] = adapter

    def get(self, platform: MarketplacePlatform) -> Optional[MarketplaceAdapter]:
        """Get an adapter by platform."""
        return self._adapters.get(platform)

    def list_platforms(self) -> List[MarketplacePlatform]:
        """List all registered platforms."""
        return list(self._adapters.keys())

    def has_capability(
        self,
        platform: MarketplacePlatform,
        capability: PlatformCapability,
    ) -> bool:
        """Check if a platform has a specific capability."""
        adapter = self.get(platform)
        if not adapter:
            return False
        return capability in adapter.capabilities


# Global adapter registry
adapter_registry = AdapterRegistry()
