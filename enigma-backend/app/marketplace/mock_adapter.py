"""Mock Marketplace Adapter for testing."""
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
    """Mock implementation of MarketplaceAdapter."""

    def __init__(self) -> None:
        self._authenticated = False
        self._account: Optional[MarketplaceAccount] = None
        self._jobs: Dict[str, NormalizedJob] = {}
        self._applications: Dict[str, NormalizedApplication] = {}
        self._job_counter = 0
        self._application_counter = 0

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

    async def get_account_status(self) -> MarketplaceAccount:
        if not self._account:
            raise RuntimeError("Not authenticated")
        self._account.last_synced_at = datetime.utcnow()
        return self._account

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

    async def submit_application(
        self,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
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

    async def get_platform_cost(self, platform_job_id: str) -> PlatformCost:
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

    async def check_limits(self) -> PlatformLimits:
        if not self._account:
            raise RuntimeError("Not authenticated")
        return self._account.limits
