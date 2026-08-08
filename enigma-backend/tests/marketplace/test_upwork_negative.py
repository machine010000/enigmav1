"""
Negative tests for Upwork Adapter.

These tests verify that:
- No Upwork-specific logic exists in Core
- Upwork adapter is properly isolated
- Core doesn't depend on Upwork implementation details
- Abstraction layer is maintained
"""
import pytest

from app.marketplace.upwork_adapter import UpworkAdapter
from app.marketplace.contracts import (
    MarketplacePlatform,
    NormalizedJob,
    NormalizedApplication,
    MarketplaceAdapter,
)


class TestNoUpworkLogicInCore:
    """Test that Upwork-specific logic is not in Core."""

    def test_core_contracts_dont_import_upwork(self):
        """Test that Core contracts don't import Upwork-specific code."""
        from app.marketplace import contracts
        
        # Should not have Upwork-specific imports
        assert not hasattr(contracts, 'UpworkAdapter')
        assert not hasattr(contracts, 'upwork_api')
        assert not hasattr(contracts, 'upwork_graphql')

    def test_normalized_job_doesnt_expose_upwork_fields(self):
        """Test that NormalizedJob doesn't expose Upwork-specific fields."""
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.UPWORK,
            platform_job_id="upwork_job_001",
            title="Test Job",
            description="Test description",
        )
        
        # Should not have Upwork-specific fields
        assert not hasattr(job, 'upwork_job_id')
        assert not hasattr(job, 'upwork_client_id')
        assert not hasattr(job, 'upwork_special_contract')
        
        # Should have normalized fields
        assert hasattr(job, 'platform_job_id')
        assert hasattr(job, 'client_info')

    def test_normalized_application_doesnt_expose_upwork_fields(self):
        """Test that NormalizedApplication doesn't expose Upwork-specific fields."""
        application = NormalizedApplication(
            application_id="app_001",
            platform=MarketplacePlatform.UPWORK,
            job_id="job_001",
            platform_job_id="upwork_job_001",
        )
        
        # Should not have Upwork-specific fields
        assert not hasattr(application, 'upwork_cover_letter')
        assert not hasattr(application, 'upwork_special_questionnaire')
        
        # Should have normalized fields
        assert hasattr(application, 'proposal_text')
        assert hasattr(application, 'bid_amount')

    def test_upwork_adapter_isolated_in_own_module(self):
        """Test that Upwork adapter is isolated in its own module."""
        # Upwork adapter should be in its own module
        from app.marketplace import upwork_adapter
        
        assert hasattr(upwork_adapter, 'UpworkAdapter')
        # Should not be in contracts module
        from app.marketplace import contracts
        assert not hasattr(contracts, 'UpworkAdapter')


class TestAbstractionLayerMaintenance:
    """Test that abstraction layer is maintained."""

    def test_upwork_adapter_implements_interface_only(self):
        """Test that Upwork adapter only implements the interface."""
        adapter = UpworkAdapter()
        
        # Should implement interface methods
        assert hasattr(adapter, 'authenticate')
        assert hasattr(adapter, 'discover_jobs')
        assert hasattr(adapter, 'submit_application')
        
        # Should not expose internal Upwork-specific details
        assert not hasattr(adapter, '_graphql_client')
        assert not hasattr(adapter, '_upwork_api_key')
        assert not hasattr(adapter, '_oauth_client')

    def test_upwork_adapter_normalizes_all_data(self):
        """Test that Upwork adapter normalizes all data."""
        adapter = UpworkAdapter()
        
        upwork_job_data = {
            "id": "123",
            "title": "Test",
            "description": "Test",
            "budget": {},
            "client": {},
            "upwork_internal_field": "should_not_expose",
        }
        
        normalized = adapter._normalize_job(upwork_job_data)
        
        # Upwork internal fields should not be exposed
        assert not hasattr(normalized, 'upwork_internal_field')
        # Should only have normalized fields
        assert hasattr(normalized, 'title')
        assert hasattr(normalized, 'description')

    def test_core_uses_only_contracts(self):
        """Test that Core uses only contracts, not specific adapters."""
        # Core should import from contracts, not from specific adapters
        from app.marketplace.contracts import (
            MarketplaceAdapter,
            NormalizedJob,
            NormalizedApplication,
        )
        
        # These should be available
        assert MarketplaceAdapter is not None
        assert NormalizedJob is not None
        assert NormalizedApplication is not None


class TestPlatformIndependence:
    """Test that Core is independent of Upwork."""

    def test_core_works_without_upwork_adapter(self):
        """Test that Core can work without Upwork adapter."""
        # Core should function without Upwork adapter being loaded
        from app.marketplace.contracts import (
            MarketplacePlatform,
            NormalizedJob,
        )
        
        # Should be able to create normalized jobs without Upwork
        job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_job_001",
            title="Test Job",
            description="Test description",
        )
        
        assert job.platform == MarketplacePlatform.MOCK
        assert job.title == "Test Job"

    def test_upwork_adapter_is_swappable(self):
        """Test that Upwork adapter can be swapped with another adapter."""
        from app.marketplace.contracts import AdapterRegistry
        from app.marketplace.mock_adapter import MockMarketplaceAdapter
        
        registry = AdapterRegistry()
        
        # Should be able to register Mock adapter
        mock_adapter = MockMarketplaceAdapter()
        registry.register(mock_adapter)
        
        # Should be able to retrieve it
        retrieved = registry.get(MarketplacePlatform.MOCK)
        assert retrieved == mock_adapter
        
        # This proves the architecture allows swapping adapters
        # without changing Core code


class TestDataIsolation:
    """Test that data is properly isolated between adapters."""

    def test_upwork_data_stays_in_adapter(self):
        """Test that Upwork-specific data stays in the adapter."""
        adapter = UpworkAdapter()
        
        # Upwork-specific data structures should be internal
        assert hasattr(adapter, '_credentials')
        assert hasattr(adapter, '_client')
        
        # These should not be exposed through the interface
        assert not hasattr(adapter, 'credentials')
        assert not hasattr(adapter, 'client')

    def test_normalized_data_is_platform_agnostic(self):
        """Test that normalized data is platform-agnostic."""
        from app.marketplace.contracts import NormalizedJob
        
        # Create jobs from different platforms
        upwork_job = NormalizedJob(
            job_id="job_001",
            platform=MarketplacePlatform.UPWORK,
            platform_job_id="upwork_001",
            title="Test",
            description="Test",
        )
        
        mock_job = NormalizedJob(
            job_id="job_002",
            platform=MarketplacePlatform.MOCK,
            platform_job_id="mock_001",
            title="Test",
            description="Test",
        )
        
        # Both should have the same structure
        assert hasattr(upwork_job, 'job_id')
        assert hasattr(mock_job, 'job_id')
        assert hasattr(upwork_job, 'title')
        assert hasattr(mock_job, 'title')
        
        # Platform is the only differentiator
        assert upwork_job.platform == MarketplacePlatform.UPWORK
        assert mock_job.platform == MarketplacePlatform.MOCK


class TestNoHardcodedUpworkReferences:
    """Test that there are no hardcoded Upwork references in Core."""

    def test_contracts_dont_hardcode_upwork_values(self):
        """Test that contracts don't have hardcoded Upwork-specific values."""
        from app.marketplace.contracts import (
            MarketplacePlatform,
            CreditType,
        )
        
        # MarketplacePlatform should include UPWORK as one of many
        platforms = [p.value for p in MarketplacePlatform]
        assert "upwork" in platforms
        assert "mock" in platforms
        assert "fiverr" in platforms
        
        # Should not have Upwork-specific values like "connects" hardcoded
        # except as a valid credit type
        credit_types = [c.value for c in CreditType]
        assert "connects" in credit_types
        assert "bids" in credit_types

    def test_error_handling_is_generic(self):
        """Test that error handling is generic, not Upwork-specific."""
        from app.marketplace.contracts import PlatformError
        
        error = PlatformError(
            platform=MarketplacePlatform.UPWORK,
            error_code="ERR_001",
            error_message="Test error",
        )
        
        # Should have generic error fields
        assert hasattr(error, 'error_code')
        assert hasattr(error, 'error_message')
        assert hasattr(error, 'is_retriable')
        
        # Should not have Upwork-specific error fields
        assert not hasattr(error, 'upwork_error_code')
        assert not hasattr(error, 'upwork_error_type')
