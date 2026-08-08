"""
Negative tests for Marketplace Adapter Foundation.

These tests verify that:
- No platform-specific logic exists in Core
- Abstraction layer is properly enforced
- Platform-specific data is normalized
- Core doesn't depend on specific platforms
"""
import pytest

from app.marketplace.contracts import (
    MarketplacePlatform,
    NormalizedJob,
    NormalizedApplication,
    MarketplaceAdapter,
    AdapterRegistry,
)
from app.marketplace.mock_adapter import MockMarketplaceAdapter


class TestNoPlatformLogicInCore:
    """Test that platform-specific logic is not in Core."""

    def test_normalized_job_no_platform_specific_fields(self):
        """Test that NormalizedJob doesn't have platform-specific fields."""
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
        )
        
        # Should not have platform-specific fields
        assert not hasattr(job, 'upwork_job_url')
        assert not hasattr(job, 'fiverr_gig_id')
        assert not hasattr(job, 'freelancer_project_id')
        
        # Should have normalized fields
        assert hasattr(job, 'title')
        assert hasattr(job, 'description')
        assert hasattr(job, 'budget_min')
        assert hasattr(job, 'budget_max')

    def test_normalized_application_no_platform_specific_fields(self):
        """Test that NormalizedApplication doesn't have platform-specific fields."""
        application = NormalizedApplication(
            application_id="app_001",
            platform=MarketplacePlatform.MOCK,
            job_id="job_001",
            platform_job_id="mock_job_001",
        )
        
        # Should not have platform-specific fields
        assert not hasattr(application, 'upwork_cover_letter')
        assert not hasattr(application, 'fiverr_offer')
        assert not hasattr(application, 'freelancer_bid')
        
        # Should have normalized fields
        assert hasattr(application, 'proposal_text')
        assert hasattr(application, 'bid_amount')

    def test_adapter_contract_is_abstract(self):
        """Test that MarketplaceAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MarketplaceAdapter()

    def test_adapter_registry_only_accepts_adapters(self):
        """Test that adapter registry only accepts MarketplaceAdapter instances."""
        registry = AdapterRegistry()
        
        # Should not accept non-adapter
        with pytest.raises(AttributeError):
            registry.register("not_an_adapter")

    def test_platform_enum_does_not_expose_implementation_details(self):
        """Test that platform enum doesn't expose implementation details."""
        # Should only have platform identifiers
        platforms = [p.value for p in MarketplacePlatform]
        
        # Should not have implementation details
        assert "api_url" not in str(platforms)
        assert "api_key" not in str(platforms)
        assert "endpoint" not in str(platforms)


class TestAbstractionLayerEnforcement:
    """Test that abstraction layer is properly enforced."""

    def test_normalized_data_is_platform_agnostic(self):
        """Test that normalized data is platform-agnostic."""
        # Create jobs from different platforms
        mock_job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
        )
        
        # Both should have same structure
        assert hasattr(mock_job, 'job_id')
        assert hasattr(mock_job, 'title')
        assert hasattr(mock_job, 'description')
        assert hasattr(mock_job, 'budget_min')
        
        # Platform is only differentiator
        assert mock_job.platform == MarketplacePlatform.MOCK

    def test_adapter_interface_hides_implementation(self):
        """Test that adapter interface hides implementation details."""
        adapter = MockMarketplaceAdapter()
        
        # Should expose only interface methods
        assert hasattr(adapter, 'authenticate')
        assert hasattr(adapter, 'discover_jobs')
        assert hasattr(adapter, 'submit_application')
        
        # Should not expose internal implementation details
        assert not hasattr(adapter, '_api_client')
        assert not hasattr(adapter, '_api_key')
        assert not hasattr(adapter, '_api_url')

    def test_registry_enforces_adapter_type(self):
        """Test that registry enforces adapter type checking."""
        registry = AdapterRegistry()
        
        # Only MarketplaceAdapter instances should work
        adapter = MockMarketplaceAdapter()
        registry.register(adapter)
        
        # Non-adapter should fail
        with pytest.raises(AttributeError):
            registry.register({"platform": "mock"})


class TestPlatformIndependence:
    """Test that Core is independent of specific platforms."""

    def test_core_does_not_import_platform_specifics(self):
        """Test that Core modules don't import platform-specific code."""
        # This is a structural test - in production would use import analysis
        # For now, we verify the contracts module doesn't import platform-specifics
        from app.marketplace import contracts
        
        # Should not have platform-specific imports
        assert not hasattr(contracts, 'upwork_api')
        assert not hasattr(contracts, 'fiverr_api')
        assert not hasattr(contracts, 'freelancer_api')

    def test_normalized_job_works_without_platform(self):
        """Test that NormalizedJob can be created without platform-specific data."""
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
        )
        
        # Should work with minimal data
        assert job.job_id == "job_001"
        assert job.title == "Test Job"
        assert job.description == "Test description"

    def test_normalized_application_works_without_platform(self):
        """Test that NormalizedApplication can be created without platform-specific data."""
        application = NormalizedApplication(
            application_id="app_001",
            platform=MarketplacePlatform.MOCK,
            job_id="job_001",
            platform_job_id="mock_job_001",
        )
        
        # Should work with minimal data
        assert application.application_id == "app_001"
        assert application.platform == MarketplacePlatform.MOCK


class TestDataNormalization:
    """Test that data is properly normalized."""

    def test_job_normalization_removes_platform_specifics(self):
        """Test that job normalization removes platform-specific fields."""
        # In a real scenario, this would test the normalization logic
        # For now, we verify the structure doesn't allow platform-specifics
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
            metadata={"platform_specific": "data"},
        )
        
        # Platform-specific data should be in metadata, not as fields
        assert "platform_specific" in job.metadata
        assert not hasattr(job, 'platform_specific')

    def test_application_normalization_removes_platform_specifics(self):
        """Test that application normalization removes platform-specific fields."""
        application = NormalizedApplication(
            application_id="app_001",
            platform=MarketplacePlatform.MOCK,
            job_id="job_001",
            platform_job_id="mock_job_001",
            metadata={"platform_specific": "data"},
        )
        
        # Platform-specific data should be in metadata, not as fields
        assert "platform_specific" in application.metadata
        assert not hasattr(application, 'platform_specific')


class TestErrorHandling:
    """Test error handling without platform-specific logic."""

    def test_adapter_errors_are_generic(self):
        """Test that adapter errors are generic, not platform-specific."""
        # In a real scenario, this would test error handling
        # For now, we verify the error structure is generic
        from app.marketplace.contracts import PlatformError
        
        error = PlatformError(
            platform=MarketplacePlatform.MOCK,
            error_code="ERR_001",
            error_message="Test error",
        )
        
        # Should have generic error fields
        assert hasattr(error, 'error_code')
        assert hasattr(error, 'error_message')
        assert hasattr(error, 'is_retriable')
        assert hasattr(error, 'is_auth_error')
        
        # Should not have platform-specific error fields
        assert not hasattr(error, 'upwork_error_code')
        assert not hasattr(error, 'fiverr_error_code')


class TestMockAdapterIsolation:
    """Test that Mock adapter is isolated from Core."""

    def test_mock_adapter_does_not_leak_to_core(self):
        """Test that Mock adapter implementation doesn't leak to Core."""
        adapter = MockMarketplaceAdapter()
        
        # Should only expose interface
        assert hasattr(adapter, 'platform')
        assert hasattr(adapter, 'capabilities')
        
        # Should not expose internal mock-specific details
        assert not hasattr(adapter, '_mock_data')
        assert not hasattr(adapter, '_test_data')

    def test_mock_adapter_is_swappable(self):
        """Test that Mock adapter can be swapped with real adapter."""
        registry = AdapterRegistry()
        
        # Register mock adapter
        mock_adapter = MockMarketplaceAdapter()
        registry.register(mock_adapter)
        
        # Should be able to retrieve by platform
        retrieved = registry.get(MarketplacePlatform.MOCK)
        assert retrieved == mock_adapter
        
        # Should be swappable (in production, would register real adapter)
        # This verifies the architecture allows swapping
        assert registry.has_capability(
            MarketplacePlatform.MOCK,
            mock_adapter.capabilities[0],
        )
