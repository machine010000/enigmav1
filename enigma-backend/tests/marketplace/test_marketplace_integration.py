"""
Integration tests for Marketplace Adapter Foundation.

These tests verify the end-to-end pipeline:
Mock Marketplace → Discover Jobs → Normalize → Work Market Integration
"""
import pytest
import asyncio

from app.marketplace.contracts import (
    MarketplacePlatform,
    NormalizedJob,
    NormalizedApplication,
    ApplicationStatus,
    PlatformCapability,
)
from app.marketplace.mock_adapter import MockMarketplaceAdapter
from app.marketplace.contracts import AdapterRegistry


class TestMockMarketplaceIntegration:
    """Test Mock Marketplace integration pipeline."""

    @pytest.mark.asyncio
    async def test_mock_authenticate_and_discover_jobs(self):
        """Test authentication and job discovery pipeline."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate
        account = await adapter.authenticate({})
        
        assert account is not None
        assert account.platform == MarketplacePlatform.MOCK
        assert account.is_authenticated is True
        assert account.limits.credits_available > 0
        
        # Discover jobs
        jobs = await adapter.discover_jobs("python developer", limit=5)
        
        assert len(jobs) > 0
        assert all(isinstance(job, NormalizedJob) for job in jobs)
        assert all(job.platform == MarketplacePlatform.MOCK for job in jobs)

    @pytest.mark.asyncio
    async def test_mock_get_specific_job(self):
        """Test retrieving a specific job."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate and discover
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        assert len(jobs) > 0
        
        # Get specific job
        job = await adapter.get_job(jobs[0].platform_job_id)
        
        assert job is not None
        assert job.platform_job_id == jobs[0].platform_job_id
        assert job.title is not None
        assert job.description is not None

    @pytest.mark.asyncio
    async def test_mock_submit_application(self):
        """Test submitting an application."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate and discover
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        # Create application
        application = NormalizedApplication(
            application_id="test_app_001",
            platform=MarketplacePlatform.MOCK,
            job_id=jobs[0].job_id,
            platform_job_id=jobs[0].platform_job_id,
            proposal_text="I am interested in this job",
            bid_amount=100.0,
        )
        
        # Submit
        submitted = await adapter.submit_application(application)
        
        assert submitted.status == ApplicationStatus.SUBMITTED
        assert submitted.platform_application_id is not None
        assert submitted.submitted_at is not None

    @pytest.mark.asyncio
    async def test_mock_get_application_status(self):
        """Test getting application status."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate, discover, and submit
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        application = NormalizedApplication(
            application_id="test_app_002",
            platform=MarketplacePlatform.MOCK,
            job_id=jobs[0].job_id,
            platform_job_id=jobs[0].platform_job_id,
        )
        
        submitted = await adapter.submit_application(application)
        
        # Get status
        status = await adapter.get_application_status(submitted.platform_application_id)
        
        assert status == ApplicationStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_mock_get_platform_cost(self):
        """Test getting platform cost for a job."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate and discover
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        # Get cost
        cost = await adapter.get_platform_cost(jobs[0].platform_job_id)
        
        assert cost is not None
        assert cost.amount > 0
        assert cost.currency == "USD"

    @pytest.mark.asyncio
    async def test_mock_check_limits(self):
        """Test checking platform limits."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate
        await adapter.authenticate({})
        
        # Check limits
        limits = await adapter.check_limits()
        
        assert limits is not None
        assert limits.credits_available > 0
        assert limits.credits_total > 0
        assert limits.daily_application_limit is not None

    @pytest.mark.asyncio
    async def test_mock_get_account_status(self):
        """Test getting account status."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate
        await adapter.authenticate({})
        
        # Get status
        account = await adapter.get_account_status()
        
        assert account is not None
        assert account.is_authenticated is True
        assert account.last_synced_at is not None


class TestAdapterRegistryIntegration:
    """Test adapter registry integration."""

    def test_register_and_use_adapter(self):
        """Test registering and using an adapter through registry."""
        registry = AdapterRegistry()
        adapter = MockMarketplaceAdapter()
        
        # Register
        registry.register(adapter)
        
        # Get
        retrieved = registry.get(MarketplacePlatform.MOCK)
        
        assert retrieved is not None
        assert retrieved == adapter

    @pytest.mark.asyncio
    async def test_registry_adapter_discover_jobs(self):
        """Test discovering jobs through registry adapter."""
        registry = AdapterRegistry()
        adapter = MockMarketplaceAdapter()
        registry.register(adapter)
        
        # Get adapter and authenticate
        retrieved = registry.get(MarketplacePlatform.MOCK)
        await retrieved.authenticate({})
        
        # Discover jobs
        jobs = await retrieved.discover_jobs("python", limit=3)
        
        assert len(jobs) > 0
        assert all(job.platform == MarketplacePlatform.MOCK for job in jobs)


class TestNormalizationPipeline:
    """Test job normalization pipeline."""

    @pytest.mark.asyncio
    async def test_job_normalization_to_work_market_format(self):
        """Test that normalized jobs can be converted to work market format."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate and discover
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        job = jobs[0]
        
        # Verify normalized structure
        assert job.job_id is not None
        assert job.platform == MarketplacePlatform.MOCK
        assert job.platform_job_id is not None
        assert job.title is not None
        assert job.description is not None
        assert job.budget_min is not None or job.budget_max is not None
        assert job.skills_required is not None
        assert job.platform_cost is not None

    @pytest.mark.asyncio
    async def test_application_normalization_to_work_market_format(self):
        """Test that normalized applications can be converted to work market format."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate and discover
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        # Create and submit application
        application = NormalizedApplication(
            application_id="test_app_003",
            platform=MarketplacePlatform.MOCK,
            job_id=jobs[0].job_id,
            platform_job_id=jobs[0].platform_job_id,
            proposal_text="Test proposal",
            bid_amount=150.0,
        )
        
        submitted = await adapter.submit_application(application)
        
        # Verify normalized structure
        assert submitted.application_id is not None
        assert submitted.platform == MarketplacePlatform.MOCK
        assert submitted.platform_application_id is not None
        assert submitted.status == ApplicationStatus.SUBMITTED
        assert submitted.submitted_at is not None


class TestCapabilityChecking:
    """Test capability checking through registry."""

    def test_registry_capability_check(self):
        """Test checking capabilities through registry."""
        registry = AdapterRegistry()
        adapter = MockMarketplaceAdapter()
        registry.register(adapter)
        
        # Check various capabilities
        assert registry.has_capability(
            MarketplacePlatform.MOCK,
            PlatformCapability.JOB_DISCOVERY,
        ) is True
        
        assert registry.has_capability(
            MarketplacePlatform.MOCK,
            PlatformCapability.APPLICATION_SUBMISSION,
        ) is True
        
        # Check non-existent platform
        assert registry.has_capability(
            MarketplacePlatform.UPWORK,
            PlatformCapability.JOB_DISCOVERY,
        ) is False


class TestPlatformCostIntegration:
    """Test platform cost integration with decision making."""

    @pytest.mark.asyncio
    async def test_platform_cost_influences_decision(self):
        """Test that platform cost can be used for decision making."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate and discover
        await adapter.authenticate({})
        jobs = await adapter.discover_jobs("python", limit=1)
        
        # Get cost
        cost = await adapter.get_platform_cost(jobs[0].platform_job_id)
        
        # Get limits
        limits = await adapter.check_limits()
        
        # Decision logic example
        can_afford = cost.amount <= limits.credits_available
        
        assert can_afford is True
        assert limits.credits_available >= cost.amount


class TestFullPipeline:
    """Test the full pipeline from discovery to application."""

    @pytest.mark.asyncio
    async def test_full_mock_pipeline(self):
        """Test the complete pipeline: Auth → Discover → Get Job → Submit Application."""
        adapter = MockMarketplaceAdapter()
        
        # Step 1: Authenticate
        account = await adapter.authenticate({})
        assert account.is_authenticated is True
        
        # Step 2: Discover jobs
        jobs = await adapter.discover_jobs("python developer", limit=1)
        assert len(jobs) > 0
        
        # Step 3: Get specific job details
        job = await adapter.get_job(jobs[0].platform_job_id)
        assert job is not None
        
        # Step 4: Check platform cost
        cost = await adapter.get_platform_cost(job.platform_job_id)
        assert cost is not None
        
        # Step 5: Check limits
        limits = await adapter.check_limits()
        assert limits.credits_available >= cost.amount
        
        # Step 6: Submit application
        application = NormalizedApplication(
            application_id="full_pipeline_app",
            platform=MarketplacePlatform.MOCK,
            job_id=job.job_id,
            platform_job_id=job.platform_job_id,
            proposal_text="Full pipeline test proposal",
            bid_amount=job.budget_min or 100.0,
        )
        
        submitted = await adapter.submit_application(application)
        assert submitted.status == ApplicationStatus.SUBMITTED
        
        # Step 7: Get application status
        status = await adapter.get_application_status(submitted.platform_application_id)
        assert status == ApplicationStatus.SUBMITTED
