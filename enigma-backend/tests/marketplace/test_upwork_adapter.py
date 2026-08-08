"""
Tests for Upwork Marketplace Adapter.

These tests verify that the UpworkAdapter properly implements
the MarketplaceAdapter contract and normalizes Upwork data correctly.
Tests use mocking to avoid requiring real Upwork credentials.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.marketplace.upwork_adapter import UpworkAdapter, UpworkCredentials
from app.marketplace.contracts import (
    MarketplacePlatform,
    PlatformCapability,
    AccountStatus,
    ApplicationStatus,
    CreditType,
)


class TestUpworkAdapterContract:
    """Test that UpworkAdapter implements MarketplaceAdapter contract."""

    def test_upwork_adapter_platform_property(self):
        """Test that UpworkAdapter returns correct platform."""
        adapter = UpworkAdapter()
        assert adapter.platform == MarketplacePlatform.UPWORK

    def test_upwork_adapter_capabilities_property(self):
        """Test that UpworkAdapter returns correct capabilities."""
        adapter = UpworkAdapter()
        capabilities = adapter.capabilities
        
        assert PlatformCapability.JOB_DISCOVERY in capabilities
        assert PlatformCapability.JOB_RETRIEVAL in capabilities
        assert PlatformCapability.APPLICATION_SUBMISSION in capabilities
        assert PlatformCapability.APPLICATION_STATUS_TRACKING in capabilities
        assert PlatformCapability.CREDIT_MANAGEMENT in capabilities
        assert PlatformCapability.ACCOUNT_STATUS_CHECK in capabilities

    def test_upwork_adapter_loads_credentials_from_env(self):
        """Test that adapter loads credentials from environment variables."""
        with patch.dict('os.environ', {
            'UPWORK_CLIENT_ID': 'test_id',
            'UPWORK_CLIENT_SECRET': 'test_secret',
            'UPWORK_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            adapter = UpworkAdapter()
            assert adapter._credentials.client_id == 'test_id'
            assert adapter._credentials.client_secret == 'test_secret'
            assert adapter._credentials.redirect_uri == 'http://localhost:8000/callback'

    def test_upwork_adapter_accepts_custom_credentials(self):
        """Test that adapter accepts custom credentials."""
        credentials = UpworkCredentials(
            client_id="custom_id",
            client_secret="custom_secret",
            redirect_uri="http://custom.uri",
        )
        adapter = UpworkAdapter(credentials=credentials)
        
        assert adapter._credentials.client_id == "custom_id"
        assert adapter._credentials.client_secret == "custom_secret"


class TestUpworkAuthentication:
    """Test Upwork authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_with_access_token(self):
        """Test authentication with direct access token."""
        adapter = UpworkAdapter()
        
        credentials = {"access_token": "test_token"}
        
        with patch.object(adapter, '_get_account_info', new_callable=AsyncMock) as mock_get_account:
            mock_account = MagicMock()
            mock_account.is_authenticated = True
            mock_get_account.return_value = mock_account
            
            account = await adapter.authenticate(credentials)
            
            assert adapter._credentials.access_token == "test_token"
            assert adapter._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_with_authorization_code(self):
        """Test authentication with authorization code."""
        adapter = UpworkAdapter()
        adapter._credentials = UpworkCredentials(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        
        credentials = {"authorization_code": "test_code"}
        
        with patch.object(adapter, '_exchange_code_for_token', new_callable=AsyncMock) as mock_exchange:
            with patch.object(adapter, '_get_account_info', new_callable=AsyncMock) as mock_get_account:
                mock_account = MagicMock()
                mock_account.is_authenticated = True
                mock_get_account.return_value = mock_account
                
                account = await adapter.authenticate(credentials)
                
                mock_exchange.assert_called_once_with("test_code")
                assert adapter._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_without_required_credentials_raises_error(self):
        """Test that authentication without required credentials raises error."""
        adapter = UpworkAdapter()
        
        with pytest.raises(ValueError):
            await adapter.authenticate({})


class TestUpworkJobNormalization:
    """Test Upwork job normalization to NormalizedJob."""

    def test_normalize_job_maps_upwork_fields(self):
        """Test that Upwork job fields are correctly normalized."""
        adapter = UpworkAdapter()
        
        upwork_job_data = {
            "id": "123456789",
            "title": "Python Developer Needed",
            "description": "Need a Python developer for a web project",
            "budget": {
                "min": 50,
                "max": 100,
                "currency": "USD",
                "type": "fixed",
            },
            "skills": [{"name": "python"}, {"name": "django"}],
            "jobType": "one-time",
            "duration": "1-3_months",
            "client": {
                "id": "client_123",
                "displayName": "Test Client",
                "reviews": {"rating": 4.5},
            },
            "createdDate": "2024-01-01T00:00:00Z",
            "connectsRequired": 2,
        }
        
        normalized_job = adapter._normalize_job(upwork_job_data)
        
        assert normalized_job.platform == MarketplacePlatform.UPWORK
        assert normalized_job.platform_job_id == "123456789"
        assert normalized_job.job_id == "upwork_123456789"
        assert normalized_job.title == "Python Developer Needed"
        assert normalized_job.description == "Need a Python developer for a web project"
        assert normalized_job.budget_min == 50
        assert normalized_job.budget_max == 100
        assert normalized_job.currency == "USD"
        assert normalized_job.budget_type == "fixed"
        assert "python" in normalized_job.skills_required
        assert "django" in normalized_job.skills_required
        assert normalized_job.job_type == "one-time"
        assert normalized_job.duration == "1-3_months"
        assert normalized_job.client_info["id"] == "client_123"
        assert normalized_job.client_info["name"] == "Test Client"
        assert normalized_job.client_info["rating"] == 4.5
        assert normalized_job.platform_cost.amount == 2.0
        assert normalized_job.platform_cost.credit_type == CreditType.CONNECTS

    def test_normalize_job_handles_missing_fields(self):
        """Test that normalization handles missing fields gracefully."""
        adapter = UpworkAdapter()
        
        upwork_job_data = {
            "id": "123",
            "title": "Test Job",
            "description": "Test",
        }
        
        normalized_job = adapter._normalize_job(upwork_job_data)
        
        assert normalized_job.platform == MarketplacePlatform.UPWORK
        assert normalized_job.platform_job_id == "123"
        assert normalized_job.title == "Test Job"
        assert normalized_job.budget_min is None
        assert normalized_job.budget_max is None
        assert len(normalized_job.skills_required) == 0


class TestUpworkStatusMapping:
    """Test Upwork status mapping to enum values."""

    def test_map_upwork_status(self):
        """Test that Upwork status is correctly mapped."""
        adapter = UpworkAdapter()
        
        assert adapter._map_upwork_status("active") == AccountStatus.ACTIVE
        assert adapter._map_upwork_status("suspended") == AccountStatus.SUSPENDED
        assert adapter._map_upwork_status("restricted") == AccountStatus.RESTRICTED
        assert adapter._map_upwork_status("verification_pending") == AccountStatus.VERIFICATION_PENDING
        assert adapter._map_upwork_status("unknown") == AccountStatus.UNKNOWN

    def test_map_upwork_application_status(self):
        """Test that Upwork application status is correctly mapped."""
        adapter = UpworkAdapter()
        
        assert adapter._map_upwork_application_status("submitted") == ApplicationStatus.SUBMITTED
        assert adapter._map_upwork_application_status("accepted") == ApplicationStatus.ACCEPTED
        assert adapter._map_upwork_application_status("rejected") == ApplicationStatus.REJECTED
        assert adapter._map_upwork_application_status("withdrawn") == ApplicationStatus.WITHDRAWN
        assert adapter._map_upwork_application_status("unknown") == ApplicationStatus.UNKNOWN


class TestUpworkErrorHandling:
    """Test Upwork error handling and normalization."""

    def test_handle_api_error_401(self):
        """Test that 401 errors are marked as auth errors."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.platform == MarketplacePlatform.UPWORK
        assert error.is_auth_error is True
        assert error.is_retriable is False

    def test_handle_api_error_429(self):
        """Test that 429 errors are marked as rate limit errors."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.platform == MarketplacePlatform.UPWORK
        assert error.is_rate_limit is True
        assert error.is_retriable is True

    def test_handle_api_error_500(self):
        """Test that 500 errors are marked as retriable."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.platform == MarketplacePlatform.UPWORK
        assert error.is_retriable is True
        assert error.is_auth_error is False

    def test_handle_api_error_invalid_json(self):
        """Test that invalid JSON responses are handled gracefully."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.platform == MarketplacePlatform.UPWORK
        assert error.error_message == "HTTP 500 error"


class TestUpworkDateParsing:
    """Test Upwork date parsing."""

    def test_parse_upwork_date_valid(self):
        """Test parsing valid Upwork date."""
        adapter = UpworkAdapter()
        
        date_str = "2024-01-01T00:00:00Z"
        parsed = adapter._parse_upwork_date(date_str)
        
        assert parsed is not None
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 1

    def test_parse_upwork_date_none(self):
        """Test parsing None date."""
        adapter = UpworkAdapter()
        
        parsed = adapter._parse_upwork_date(None)
        assert parsed is None

    def test_parse_upwork_date_invalid(self):
        """Test parsing invalid date."""
        adapter = UpworkAdapter()
        
        parsed = adapter._parse_upwork_date("invalid-date")
        assert parsed is None


class TestUpworkAdapterIsolation:
    """Test that Upwork adapter is isolated from Core."""

    def test_upwork_adapter_does_not_expose_upwork_specific_fields(self):
        """Test that normalized jobs don't expose Upwork-specific fields."""
        adapter = UpworkAdapter()
        
        upwork_job_data = {
            "id": "123",
            "title": "Test",
            "description": "Test",
            "budget": {},
            "client": {},
        }
        
        normalized = adapter._normalize_job(upwork_job_data)
        
        # Should not have Upwork-specific fields
        assert not hasattr(normalized, 'upwork_job_id')
        assert not hasattr(normalized, 'upwork_client_id')
        
        # Should have normalized fields
        assert hasattr(normalized, 'platform_job_id')
        assert hasattr(normalized, 'client_info')

    def test_upwork_adapter_implements_interface_only(self):
        """Test that adapter only exposes interface methods."""
        adapter = UpworkAdapter()
        
        # Should have interface methods
        assert hasattr(adapter, 'authenticate')
        assert hasattr(adapter, 'discover_jobs')
        assert hasattr(adapter, 'submit_application')
        
        # Should not expose internal implementation details
        assert not hasattr(adapter, '_api_client')
        assert not hasattr(adapter, '_upwork_api')
