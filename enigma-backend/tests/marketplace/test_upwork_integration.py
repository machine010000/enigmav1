"""
Integration tests for Upwork Adapter.

These tests verify the end-to-end integration of the Upwork adapter
with the marketplace contracts, using mocking to avoid requiring
real Upwork credentials or API calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.marketplace.upwork_adapter import UpworkAdapter, UpworkCredentials
from app.marketplace.contracts import (
    MarketplacePlatform,
    NormalizedJob,
    NormalizedApplication,
    ApplicationStatus,
    PlatformCapability,
    AdapterRegistry,
)


class TestUpworkAdapterIntegration:
    """Test Upwork adapter integration with marketplace contracts."""

    @pytest.mark.asyncio
    async def test_full_upwork_pipeline_mocked(self):
        """Test the complete Upwork pipeline with mocked API calls."""
        adapter = UpworkAdapter()
        adapter._credentials = UpworkCredentials(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
            access_token="test_token",
        )
        
        # Mock account info
        mock_account_data = {
            "data": {
                "me": {
                    "id": "user_123",
                    "profile": {"displayName": "Test User"},
                    "accountStatus": {"status": "active"},
                    "finance": {
                        "connects": {
                            "total": 100,
                            "available": 80,
                        }
                    },
                }
            }
        }
        
        with patch.object(adapter, '_make_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_account_data
            mock_request.return_value = mock_response
            
            # Step 1: Authenticate
            account = await adapter.authenticate({"access_token": "test_token"})
            assert account.is_authenticated is True
            assert account.platform == MarketplacePlatform.UPWORK

    @pytest.mark.asyncio
    async def test_upwork_adapter_in_registry(self):
        """Test that Upwork adapter can be registered and used through registry."""
        registry = AdapterRegistry()
        adapter = UpworkAdapter()
        
        # Register adapter
        registry.register(adapter)
        
        # Retrieve adapter
        retrieved = registry.get(MarketplacePlatform.UPWORK)
        assert retrieved is not None
        assert retrieved.platform == MarketplacePlatform.UPWORK
        
        # Check capabilities
        assert registry.has_capability(
            MarketplacePlatform.UPWORK,
            PlatformCapability.JOB_DISCOVERY,
        ) is True

    @pytest.mark.asyncio
    async def test_upwork_adapter_normalization_pipeline(self):
        """Test that Upwork data is properly normalized through the pipeline."""
        adapter = UpworkAdapter()
        
        upwork_job_data = {
            "id": "job_456",
            "title": "Web Developer",
            "description": "Need web developer",
            "budget": {"min": 30, "max": 60, "currency": "USD", "type": "hourly"},
            "skills": [{"name": "html"}, {"name": "css"}, {"name": "javascript"}],
            "jobType": "ongoing",
            "duration": "3-6_months",
            "client": {
                "id": "client_456",
                "displayName": "Web Client",
                "reviews": {"rating": 5.0},
            },
            "createdDate": "2024-02-01T00:00:00Z",
            "connectsRequired": 4,
        }
        
        normalized = adapter._normalize_job(upwork_job_data)
        
        # Verify normalization
        assert normalized.platform == MarketplacePlatform.UPWORK
        assert normalized.platform_job_id == "job_456"
        assert normalized.job_id == "upwork_job_456"
        assert normalized.title == "Web Developer"
        assert normalized.budget_min == 30
        assert normalized.budget_max == 60
        assert normalized.budget_type == "hourly"
        assert "html" in normalized.skills_required
        assert "css" in normalized.skills_required
        assert "javascript" in normalized.skills_required
        assert normalized.job_type == "ongoing"
        assert normalized.client_info["name"] == "Web Client"
        assert normalized.client_info["rating"] == 5.0
        assert normalized.platform_cost.amount == 4.0

    @pytest.mark.asyncio
    async def test_upwork_adapter_cost_decision_integration(self):
        """Test that platform cost influences decision making."""
        adapter = UpworkAdapter()
        
        # Simulate job cost check
        upwork_job_data = {
            "id": "job_789",
            "title": "Test Job",
            "description": "Test",
            "budget": {},
            "skills": [],
            "jobType": "one-time",
            "duration": "1-3_months",
            "client": {"id": "client_789", "displayName": "Client", "reviews": {}},
            "createdDate": "2024-01-01T00:00:00Z",
            "connectsRequired": 5,
        }
        
        normalized = adapter._normalize_job(upwork_job_data)
        cost = normalized.platform_cost
        
        # Simulate limits
        from app.marketplace.contracts import PlatformLimits, CreditType
        limits = PlatformLimits(
            credits_available=10.0,
            credits_total=100.0,
            credit_type=CreditType.CONNECTS,
        )
        
        # Decision: Can afford?
        assert cost.amount == 5.0
        can_afford = cost.amount <= limits.credits_available
        assert can_afford is True


class TestUpworkAdapterIsolationIntegration:
    """Test that Upwork adapter maintains isolation in integration scenarios."""

    @pytest.mark.asyncio
    async def test_upwork_adapter_does_not_leak_to_other_platforms(self):
        """Test that Upwork adapter doesn't affect other platforms."""
        from app.marketplace.mock_adapter import MockMarketplaceAdapter
        
        registry = AdapterRegistry()
        
        # Register both adapters
        upwork_adapter = UpworkAdapter()
        mock_adapter = MockMarketplaceAdapter()
        
        registry.register(upwork_adapter)
        registry.register(mock_adapter)
        
        # Both should be accessible
        upwork = registry.get(MarketplacePlatform.UPWORK)
        mock = registry.get(MarketplacePlatform.MOCK)
        
        assert upwork is not None
        assert mock is not None
        assert upwork.platform == MarketplacePlatform.UPWORK
        assert mock.platform == MarketplacePlatform.MOCK

    @pytest.mark.asyncio
    async def test_upwork_normalized_data_compatible_with_core(self):
        """Test that Upwork normalized data is compatible with Core."""
        adapter = UpworkAdapter()
        
        upwork_job_data = {
            "id": "job_999",
            "title": "Integration Test Job",
            "description": "Testing integration",
            "budget": {},
            "skills": [],
            "jobType": "one-time",
            "duration": "1-3_months",
            "client": {"id": "client_999", "displayName": "Client", "reviews": {}},
            "createdDate": "2024-01-01T00:00:00Z",
            "connectsRequired": 1,
        }
        
        normalized = adapter._normalize_job(upwork_job_data)
        
        # Should be compatible with NormalizedJob contract
        assert isinstance(normalized, NormalizedJob)
        assert normalized.job_id is not None
        assert normalized.platform == MarketplacePlatform.UPWORK
        assert normalized.platform_job_id is not None
        assert normalized.title is not None
        assert normalized.description is not None
