"""
Architecture tests for Marketplace Adapter Foundation.

These tests verify the structural integrity and architectural compliance
of the marketplace adapter contracts and implementations.
"""
import pytest

from app.marketplace.contracts import (
    MarketplacePlatform,
    AccountStatus,
    CreditType,
    ApplicationStatus,
    PlatformCapability,
    PlatformCost,
    PlatformLimits,
    MarketplaceAccount,
    PlatformError,
    NormalizedJob,
    NormalizedApplication,
    MarketplaceAdapter,
    AdapterRegistry,
    adapter_registry,
)
from app.marketplace.mock_adapter import MockMarketplaceAdapter


class TestMarketplaceEnums:
    """Test marketplace enum definitions."""

    def test_marketplace_platform_enum(self):
        """Test that MarketplacePlatform enum has required values."""
        assert MarketplacePlatform.MOCK.value == "mock"
        assert MarketplacePlatform.UPWORK.value == "upwork"
        assert MarketplacePlatform.FIVERR.value == "fiverr"
        assert MarketplacePlatform.FREELANCER.value == "freelancer"

    def test_account_status_enum(self):
        """Test that AccountStatus enum has required values."""
        assert AccountStatus.ACTIVE.value == "active"
        assert AccountStatus.SUSPENDED.value == "suspended"
        assert AccountStatus.RESTRICTED.value == "restricted"

    def test_credit_type_enum(self):
        """Test that CreditType enum has required values."""
        assert CreditType.CONNECTS.value == "connects"
        assert CreditType.BIDS.value == "bids"
        assert CreditType.TOKENS.value == "tokens"

    def test_application_status_enum(self):
        """Test that ApplicationStatus enum has required values."""
        assert ApplicationStatus.DRAFT.value == "draft"
        assert ApplicationStatus.SUBMITTED.value == "submitted"
        assert ApplicationStatus.ACCEPTED.value == "accepted"
        assert ApplicationStatus.REJECTED.value == "rejected"

    def test_platform_capability_enum(self):
        """Test that PlatformCapability enum has required values."""
        assert PlatformCapability.JOB_DISCOVERY.value == "job_discovery"
        assert PlatformCapability.JOB_RETRIEVAL.value == "job_retrieval"
        assert PlatformCapability.APPLICATION_SUBMISSION.value == "application_submission"


class TestPlatformCostModel:
    """Test PlatformCost model."""

    def test_platform_cost_structure(self):
        """Test that PlatformCost has required fields."""
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=2.0,
            currency="USD",
        )
        assert cost.credit_type == CreditType.CONNECTS
        assert cost.amount == 2.0
        assert cost.currency == "USD"
        assert hasattr(cost, 'is_free')
        assert hasattr(cost, 'description')


class TestPlatformLimitsModel:
    """Test PlatformLimits model."""

    def test_platform_limits_structure(self):
        """Test that PlatformLimits has required fields."""
        limits = PlatformLimits(
            daily_application_limit=50,
            monthly_application_limit=200,
            credits_available=80.0,
            credits_total=100.0,
            credit_type=CreditType.CONNECTS,
        )
        assert limits.daily_application_limit == 50
        assert limits.credits_available == 80.0
        assert limits.credit_type == CreditType.CONNECTS


class TestMarketplaceAccountModel:
    """Test MarketplaceAccount model."""

    def test_marketplace_account_structure(self):
        """Test that MarketplaceAccount has required fields."""
        account = MarketplaceAccount(
            platform=MarketplacePlatform.MOCK,
            account_id="test_account",
            username="test_user",
            status=AccountStatus.ACTIVE,
            is_authenticated=True,
        )
        assert account.platform == MarketplacePlatform.MOCK
        assert account.account_id == "test_account"
        assert account.status == AccountStatus.ACTIVE
        assert hasattr(account, 'limits')
        assert hasattr(account, 'metadata')


class TestPlatformErrorModel:
    """Test PlatformError model."""

    def test_platform_error_structure(self):
        """Test that PlatformError has required fields."""
        error = PlatformError(
            platform=MarketplacePlatform.MOCK,
            error_code="ERR_001",
            error_message="Test error",
        )
        assert error.platform == MarketplacePlatform.MOCK
        assert error.error_code == "ERR_001"
        assert hasattr(error, 'is_retriable')
        assert hasattr(error, 'is_auth_error')
        assert hasattr(error, 'is_rate_limit')


class TestNormalizedJobModel:
    """Test NormalizedJob model."""

    def test_normalized_job_structure(self):
        """Test that NormalizedJob has required fields."""
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
        )
        assert job.job_id == "job_001"
        assert job.platform == MarketplacePlatform.MOCK
        assert job.platform_job_id == "mock_job_001"
        assert hasattr(job, 'budget_min')
        assert hasattr(job, 'budget_max')
        assert hasattr(job, 'skills_required')
        assert hasattr(job, 'platform_cost')


class TestNormalizedApplicationModel:
    """Test NormalizedApplication model."""

    def test_normalized_application_structure(self):
        """Test that NormalizedApplication has required fields."""
        application = NormalizedApplication(
            application_id="app_001",
            platform=MarketplacePlatform.MOCK,
            job_id="job_001",
            platform_job_id="mock_job_001",
        )
        assert application.application_id == "app_001"
        assert application.platform == MarketplacePlatform.MOCK
        assert application.status == ApplicationStatus.DRAFT
        assert hasattr(application, 'platform_application_id')
        assert hasattr(application, 'proposal_text')
        assert hasattr(application, 'bid_amount')


class TestMarketplaceAdapterContract:
    """Test MarketplaceAdapter abstract contract."""

    def test_adapter_is_abstract(self):
        """Test that MarketplaceAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MarketplaceAdapter()

    def test_adapter_has_required_methods(self):
        """Test that MarketplaceAdapter has required abstract methods."""
        required_methods = [
            'platform',
            'capabilities',
            'authenticate',
            'get_account_status',
            'discover_jobs',
            'get_job',
            'submit_application',
            'get_application_status',
            'get_platform_cost',
            'check_limits',
        ]
        
        for method in required_methods:
            assert hasattr(MarketplaceAdapter, method)


class TestAdapterRegistry:
    """Test AdapterRegistry functionality."""

    def test_adapter_registry_instantiable(self):
        """Test that AdapterRegistry can be instantiated."""
        registry = AdapterRegistry()
        assert registry is not None
        assert isinstance(registry, AdapterRegistry)

    def test_adapter_registry_register(self):
        """Test registering an adapter."""
        registry = AdapterRegistry()
        adapter = MockMarketplaceAdapter()
        
        registry.register(adapter)
        
        assert registry.get(MarketplacePlatform.MOCK) == adapter

    def test_adapter_registry_list_platforms(self):
        """Test listing registered platforms."""
        registry = AdapterRegistry()
        adapter = MockMarketplaceAdapter()
        
        registry.register(adapter)
        
        platforms = registry.list_platforms()
        assert MarketplacePlatform.MOCK in platforms

    def test_adapter_registry_has_capability(self):
        """Test checking platform capability."""
        registry = AdapterRegistry()
        adapter = MockMarketplaceAdapter()
        
        registry.register(adapter)
        
        assert registry.has_capability(
            MarketplacePlatform.MOCK,
            PlatformCapability.JOB_DISCOVERY,
        ) is True

    def test_global_adapter_registry_exists(self):
        """Test that global adapter_registry instance exists."""
        assert adapter_registry is not None
        assert isinstance(adapter_registry, AdapterRegistry)


class TestMockMarketplaceAdapter:
    """Test MockMarketplaceAdapter implementation."""

    def test_mock_adapter_implements_contract(self):
        """Test that MockMarketplaceAdapter implements MarketplaceAdapter."""
        adapter = MockMarketplaceAdapter()
        assert isinstance(adapter, MarketplaceAdapter)

    def test_mock_adapter_platform_property(self):
        """Test that MockMarketplaceAdapter returns correct platform."""
        adapter = MockMarketplaceAdapter()
        assert adapter.platform == MarketplacePlatform.MOCK

    def test_mock_adapter_capabilities_property(self):
        """Test that MockMarketplaceAdapter returns capabilities."""
        adapter = MockMarketplaceAdapter()
        capabilities = adapter.capabilities
        assert len(capabilities) > 0
        assert PlatformCapability.JOB_DISCOVERY in capabilities

    def test_mock_adapter_authenticate(self):
        """Test that MockMarketplaceAdapter can authenticate."""
        import asyncio
        
        adapter = MockMarketplaceAdapter()
        
        async def test():
            account = await adapter.authenticate({})
            assert account is not None
            assert account.platform == MarketplacePlatform.MOCK
            assert account.is_authenticated is True
        
        asyncio.run(test())

    def test_mock_adapter_discover_jobs(self):
        """Test that MockMarketplaceAdapter can discover jobs."""
        import asyncio
        
        adapter = MockMarketplaceAdapter()
        
        async def test():
            await adapter.authenticate({})
            jobs = await adapter.discover_jobs("python", limit=5)
            assert len(jobs) > 0
            assert all(isinstance(job, NormalizedJob) for job in jobs)
        
        asyncio.run(test())


class TestAbstractionLayer:
    """Test that abstraction layer prevents platform-specific logic in core."""

    def test_normalized_job_is_platform_agnostic(self):
        """Test that NormalizedJob doesn't expose platform-specific fields."""
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
        )
        
        # Should have normalized fields, not platform-specific ones
        assert hasattr(job, 'title')
        assert hasattr(job, 'description')
        assert hasattr(job, 'budget_min')
        # Should not have platform-specific fields like "upwork_job_url"
        assert not hasattr(job, 'upwork_job_url')

    def test_normalized_application_is_platform_agnostic(self):
        """Test that NormalizedApplication doesn't expose platform-specific fields."""
        application = NormalizedApplication(
            application_id="app_001",
            platform=MarketplacePlatform.MOCK,
            job_id="job_001",
            platform_job_id="mock_job_001",
        )
        
        # Should have normalized fields
        assert hasattr(application, 'proposal_text')
        assert hasattr(application, 'bid_amount')
        # Should not have platform-specific fields
        assert not hasattr(application, 'upwork_cover_letter')

    def test_adapter_registry_enforces_abstraction(self):
        """Test that adapter registry only accepts MarketplaceAdapter instances."""
        registry = AdapterRegistry()
        
        # Should work with valid adapter
        adapter = MockMarketplaceAdapter()
        registry.register(adapter)
        
        # Should not work with non-adapter
        with pytest.raises(AttributeError):
            registry.register("not_an_adapter")
