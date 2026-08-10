"""Mock Marketplace Adapter for testing.

TASK-051: Updated to implement new contract with read-only mode.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.marketplace.contracts import (
    MarketplaceAdapter,
    MarketplacePlatform,
    MarketplaceAccount,
    NormalizedJob,
    NormalizedApplication,
    PlatformCapability,
    PlatformCost,
    PlatformLimits,
    AccountStatus,
    ApplicationStatus,
    CreditType,
)


class MockMarketplaceAdapter(MarketplaceAdapter):
    """Mock implementation of MarketplaceAdapter.

    TASK-051: Read-only by default, no automatic application submission.
    """

    def __init__(self, read_only: bool = True, auto_apply_enabled: bool = False) -> None:
        """
        Initialize mock adapter.
        
        Args:
            read_only: Whether adapter is in read-only mode (TASK-051: default True)
            auto_apply_enabled: Whether auto-apply is enabled (TASK-051: default False)
        """
        self._authenticated = False
        self._account: Optional[MarketplaceAccount] = None
        self._jobs: Dict[str, NormalizedJob] = {}
        self._applications: Dict[str, NormalizedApplication] = {}
        self._job_counter = 0
        self._application_counter = 0
        self._read_only = read_only
        self._auto_apply_enabled = auto_apply_enabled

    @property
    def platform(self) -> MarketplacePlatform:
        return MarketplacePlatform.MOCK

    @property
    def capabilities(self) -> List[PlatformCapability]:
        return [
            PlatformCapability.JOB_DISCOVERY,
            PlatformCapability.JOB_RETRIEVAL,
            PlatformCapability.APPLICATION_SUBMISSION,
            PlatformCapability.APPLICATION_STATUS_TRACKING,
            PlatformCapability.CREDIT_MANAGEMENT,
            PlatformCapability.ACCOUNT_STATUS_CHECK,
        ]

    @property
    def is_read_only(self) -> bool:
        """Get read-only mode (TASK-051)."""
        return self._read_only

    @property
    def auto_apply_enabled(self) -> bool:
        """Get auto-apply enabled status (TASK-051)."""
        return self._auto_apply_enabled

    def enable_read_only(self) -> None:
        """Enable read-only mode."""
        self._read_only = True

    def disable_read_only(self) -> None:
        """Disable read-only mode."""
        self._read_only = False

    def enable_auto_apply(self) -> None:
        """Enable auto-apply."""
        self._auto_apply_enabled = True

    def disable_auto_apply(self) -> None:
        """Disable auto-apply."""
        self._auto_apply_enabled = False

    async def authenticate(self, credentials: Dict[str, Any]) -> MarketplaceAccount:
        self._authenticated = True
        self._account = MarketplaceAccount(
            platform=self.platform,
            account_id="mock_account_001",
            username="mock_user",
            status=AccountStatus.ACTIVE,
            is_authenticated=True,
            limits=PlatformLimits(
                daily_application_limit=50,
                monthly_application_limit=200,
                credits_available=80.0,
                credits_total=100.0,
                credit_type=CreditType.CONNECTS,
            ),
            last_synced_at=datetime.utcnow(),
        )
        return self._account

    async def refresh_authentication(self) -> MarketplaceAccount:
        """Refresh authentication (TASK-051)."""
        if not self._account:
            raise RuntimeError("Not authenticated")
        self._account.last_synced_at = datetime.utcnow()
        return self._account

    async def get_account_state(self) -> MarketplaceAccount:
        """Get account state (TASK-051)."""
        if not self._account:
            raise RuntimeError("Not authenticated")
        self._account.last_synced_at = datetime.utcnow()
        return self._account

    async def get_account_status(self) -> MarketplaceAccount:
        """Get account status (legacy method)."""
        return await self.get_account_state()

    async def discover_jobs(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[NormalizedJob]:
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        
        jobs = []
        for i in range(min(limit, 10)):
            self._job_counter += 1
            platform_job_id = f"mock_job_{self._job_counter}"
            job = NormalizedJob(
                job_id=f"job_{self._job_counter}",
                platform=self.platform,
                platform_job_id=platform_job_id,
                title=f"Mock Job: {query} - {i + 1}",
                description=f"Mock job for {query}",
                budget_min=50.0 + (i * 10),
                budget_max=500.0 + (i * 50),
                budget_type="fixed",
                currency="USD",
                skills_required=["python", "web development"],
                job_type="one-time",
                posted_date=datetime.utcnow() - timedelta(days=i),
                platform_cost=PlatformCost(
                    credit_type=CreditType.CONNECTS,
                    amount=2.0,
                    currency="USD",
                ),
            )
            self._jobs[platform_job_id] = job
            jobs.append(job)
        return jobs

    async def get_job(self, platform_job_id: str) -> NormalizedJob:
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        job = self._jobs.get(platform_job_id)
        if not job:
            raise ValueError(f"Job {platform_job_id} not found")
        return job

    async def get_application_requirements(self, platform_job_id: str) -> Dict[str, Any]:
        """Get application requirements (TASK-051)."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        job = self._jobs.get(platform_job_id)
        if not job:
            # Return default requirements if job not found (for testing)
            return {
                "skills_required": [],
                "attachments_required": [],
                "cover_letter_required": True,
                "portfolio_required": False,
            }
        return {
            "skills_required": job.skills_required,
            "attachments_required": [],
            "cover_letter_required": True,
            "portfolio_required": False,
        }

    async def get_application_cost(self, platform_job_id: str) -> PlatformCost:
        """Get application cost (TASK-051)."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        job = self._jobs.get(platform_job_id)
        if not job:
            raise ValueError(f"Job {platform_job_id} not found")
        return job.platform_cost or PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=2.0,
            currency="USD",
        )

    async def submit_application(
        self,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """
        Submit application with gating (TASK-051).
        
        Raises:
            RuntimeError: If read-only or auto_apply disabled
        """
        if self._read_only:
            raise RuntimeError(
                "Cannot submit application: mock adapter is in read-only mode"
            )
        
        if not self._auto_apply_enabled:
            raise RuntimeError(
                "Cannot submit application: auto-apply is disabled"
            )
        
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        
        self._application_counter += 1
        platform_application_id = f"mock_app_{self._application_counter}"
        application.platform_application_id = platform_application_id
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = datetime.utcnow()
        self._applications[platform_application_id] = application
        return application

    async def get_application_status(
        self,
        platform_application_id: str,
    ) -> ApplicationStatus:
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        application = self._applications.get(platform_application_id)
        if not application:
            raise ValueError(f"Application {platform_application_id} not found")
        return application.status

    async def check_limits(self) -> PlatformLimits:
        if not self._account:
            raise RuntimeError("Not authenticated")
        return self._account.limits
