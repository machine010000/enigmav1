"""
Read-Only Integration Tests

TASK-051: Tests for read-only mode and safety checks.
"""

import pytest
import asyncio

from app.marketplace.mock_adapter import MockMarketplaceAdapter
from app.marketplace.contracts import (
    MarketplacePlatform,
    NormalizedApplication,
    ApplicationStatus,
)
from app.marketplace.auth import (
    CredentialProvider,
    TokenStore,
    EnvironmentCredentialProvider,
    InMemoryTokenStore,
)
from app.marketplace.capabilities import (
    PlatformCapabilities,
    CapabilityStatus,
    CapabilityRegistry,
)
from app.marketplace.errors import (
    APIError,
    APIErrorHandler,
    APIErrorType,
    RateLimitHandler,
    RateLimitInfo,
)


class TestReadOnlyMode:
    """Test read-only mode enforcement."""
    
    @pytest.mark.asyncio
    async def test_adapter_read_only_by_default(self):
        """Test adapter is read-only by default (TASK-051)."""
        adapter = MockMarketplaceAdapter()
        
        assert adapter.is_read_only is True
        assert adapter.auto_apply_enabled is False
    
    @pytest.mark.asyncio
    async def test_adapter_can_enable_read_only(self):
        """Test adapter can enable read-only mode."""
        adapter = MockMarketplaceAdapter(read_only=False)
        
        assert adapter.is_read_only is False
        
        adapter.enable_read_only()
        assert adapter.is_read_only is True
    
    @pytest.mark.asyncio
    async def test_adapter_can_disable_read_only(self):
        """Test adapter can disable read-only mode."""
        adapter = MockMarketplaceAdapter(read_only=True)
        
        assert adapter.is_read_only is True
        
        adapter.disable_read_only()
        assert adapter.is_read_only is False
    
    @pytest.mark.asyncio
    async def test_submit_application_blocked_in_read_only(self):
        """Test submit_application is blocked in read-only mode (TASK-051)."""
        adapter = MockMarketplaceAdapter(read_only=True, auto_apply_enabled=True)
        
        # Authenticate first
        await adapter.authenticate({})
        
        # Try to submit application
        application = NormalizedApplication(
            application_id="test_app",
            platform=MarketplacePlatform.MOCK,
            job_id="test_job",
            platform_job_id="test_job",
        )
        
        with pytest.raises(RuntimeError, match="read-only mode"):
            await adapter.submit_application(application)
    
    @pytest.mark.asyncio
    async def test_submit_application_blocked_when_auto_apply_disabled(self):
        """Test submit_application is blocked when auto_apply disabled (TASK-051)."""
        adapter = MockMarketplaceAdapter(read_only=False, auto_apply_enabled=False)
        
        # Authenticate first
        await adapter.authenticate({})
        
        # Try to submit application
        application = NormalizedApplication(
            application_id="test_app",
            platform=MarketplacePlatform.MOCK,
            job_id="test_job",
            platform_job_id="test_job",
        )
        
        with pytest.raises(RuntimeError, match="auto-apply is disabled"):
            await adapter.submit_application(application)
    
    @pytest.mark.asyncio
    async def test_submit_application_allowed_when_both_enabled(self):
        """Test submit_application is allowed when both read-only disabled and auto_apply enabled."""
        adapter = MockMarketplaceAdapter(read_only=False, auto_apply_enabled=True)
        
        # Authenticate first
        await adapter.authenticate({})
        
        # Submit application should work
        application = NormalizedApplication(
            application_id="test_app",
            platform=MarketplacePlatform.MOCK,
            job_id="test_job",
            platform_job_id="test_job",
        )
        
        result = await adapter.submit_application(application)
        
        assert result.status == ApplicationStatus.SUBMITTED
        assert result.platform_application_id is not None


class TestCredentialProvider:
    """Test credential provider (TASK-051)."""
    
    @pytest.mark.asyncio
    async def test_environment_credential_provider(self):
        """Test environment credential provider."""
        provider = EnvironmentCredentialProvider()
        
        # No credentials set
        credential = await provider.get_credential("upwork")
        assert credential is None
        
        # Set environment variable
        import os
        os.environ["UPWORK_CLIENT_ID"] = "test_client_id"
        
        credential = await provider.get_credential("upwork")
        assert credential is not None
        assert credential.platform == "upwork"
        assert "client_id" in credential.data
        
        # Clean up
        del os.environ["UPWORK_CLIENT_ID"]
    
    @pytest.mark.asyncio
    async def test_environment_credential_provider_read_only(self):
        """Test environment credential provider is read-only."""
        provider = EnvironmentCredentialProvider()
        
        from app.marketplace.auth import Credential
        
        with pytest.raises(NotImplementedError):
            await provider.save_credential(Credential(platform="test", credential_type="test"))


class TestTokenStore:
    """Test token store (TASK-051)."""
    
    @pytest.mark.asyncio
    async def test_in_memory_token_store(self):
        """Test in-memory token store."""
        store = InMemoryTokenStore()
        
        from app.marketplace.auth import Token, TokenType
        
        token = Token(
            token_type=TokenType.ACCESS_TOKEN,
            value="test_token",
        )
        
        # Save token
        await store.save_token("upwork", token)
        
        # Get token
        retrieved = await store.get_token("upwork", TokenType.ACCESS_TOKEN)
        assert retrieved is not None
        assert retrieved.value == "test_token"
        
        # Delete token
        await store.delete_token("upwork", TokenType.ACCESS_TOKEN)
        
        # Token should be gone
        retrieved = await store.get_token("upwork", TokenType.ACCESS_TOKEN)
        assert retrieved is None


class TestPlatformCapabilities:
    """Test platform capability discovery (TASK-051)."""
    
    def test_capabilities_default_to_unknown(self):
        """Test capabilities default to UNKNOWN (TASK-051)."""
        capabilities = PlatformCapabilities("test_platform")
        
        # All capabilities should be UNKNOWN by default
        for capability in PlatformCapabilities.ALL_CAPABILITIES:
            status = capabilities.get_status(capability)
            assert status == CapabilityStatus.UNKNOWN
    
    def test_declare_capability(self):
        """Test declaring a capability."""
        capabilities = PlatformCapabilities("test_platform")
        
        capabilities.declare_capability(
            PlatformCapabilities.JOB_SEARCH,
            CapabilityStatus.SUPPORTED,
            version="1.0",
        )
        
        assert capabilities.supports(PlatformCapabilities.JOB_SEARCH)
        assert capabilities.get_status(PlatformCapabilities.JOB_SEARCH) == CapabilityStatus.SUPPORTED
    
    def test_unknown_not_false_or_free(self):
        """Test UNKNOWN is used, not false or free (TASK-051)."""
        capabilities = PlatformCapabilities("test_platform")
        
        # Default is UNKNOWN
        status = capabilities.get_status(PlatformCapabilities.JOB_SEARCH)
        assert status == CapabilityStatus.UNKNOWN
        assert status != CapabilityStatus.NOT_SUPPORTED
    
    def test_capability_registry(self):
        """Test capability registry."""
        registry = CapabilityRegistry()
        
        capabilities = PlatformCapabilities("test_platform")
        capabilities.declare_capability(
            PlatformCapabilities.JOB_SEARCH,
            CapabilityStatus.SUPPORTED,
        )
        
        registry.register(capabilities)
        
        # Check platform is registered
        assert registry.get("test_platform") is not None
        
        # Check capability support
        assert registry.supports("test_platform", PlatformCapabilities.JOB_SEARCH)
        
        # Check unknown platform returns UNKNOWN
        assert registry.get_status("unknown_platform", PlatformCapabilities.JOB_SEARCH) == CapabilityStatus.UNKNOWN


class TestAPIErrorHandling:
    """Test API error handling (TASK-051)."""
    
    def test_classify_error_401(self):
        """Test 401 error classification."""
        error = APIErrorHandler.classify_error(
            platform="upwork",
            status_code=401,
            error_message="Unauthorized",
        )
        
        assert error.error_type == APIErrorType.AUTH_EXPIRED
        assert error.is_auth_error is True
    
    def test_classify_error_429(self):
        """Test 429 error classification."""
        error = APIErrorHandler.classify_error(
            platform="upwork",
            status_code=429,
            error_message="Rate limit exceeded",
        )
        
        assert error.error_type == APIErrorType.RATE_LIMITED
        assert error.is_rate_limit is True
        assert error.is_retriable is True
    
    def test_classify_error_500(self):
        """Test 500 error classification."""
        error = APIErrorHandler.classify_error(
            platform="upwork",
            status_code=500,
            error_message="Internal server error",
        )
        
        assert error.error_type == APIErrorType.API_UNAVAILABLE
        assert error.is_retriable is True
    
    def test_to_enigma_issue(self):
        """Test conversion to Enigma Issue format."""
        error = APIError(
            error_type=APIErrorType.AUTH_EXPIRED,
            platform="upwork",
            message="Authentication expired",
        )
        
        issue = error.to_enigma_issue()
        
        assert issue["source"] == "marketplace_api"
        assert issue["type"] == "AUTH_EXPIRED"
        assert issue["severity"] == "CRITICAL"
        assert issue["platform"] == "upwork"
        assert issue["is_auth_error"] is True


class TestRateLimitHandling:
    """Test rate limit handling (TASK-051)."""
    
    def test_rate_limit_info(self):
        """Test rate limit info."""
        from datetime import datetime, timedelta
        
        limit_info = RateLimitInfo(
            limit=100,
            remaining=50,
            reset_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        assert limit_info.is_exceeded() is False
        assert limit_info.wait_seconds() is not None
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        limit_info = RateLimitInfo(
            limit=100,
            remaining=0,
        )
        
        assert limit_info.is_exceeded() is True
    
    def test_rate_limit_handler(self):
        """Test rate limit handler."""
        handler = RateLimitHandler()
        
        from datetime import datetime, timedelta
        
        limit_info = RateLimitInfo(
            limit=100,
            remaining=50,
            reset_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        handler.update_limit("upwork", limit_info)
        
        # Check can request
        can_request, wait_seconds = handler.can_request("upwork")
        assert can_request is True
        assert wait_seconds is None
        
        # Record request
        handler.record_request("upwork")
        
        # Get updated limit
        updated = handler.get_limit("upwork")
        assert updated.remaining == 49


class TestMockAdapterNewContract:
    """Test mock adapter implements new contract (TASK-051)."""
    
    @pytest.mark.asyncio
    async def test_mock_adapter_has_new_properties(self):
        """Test mock adapter has new properties."""
        adapter = MockMarketplaceAdapter()
        
        assert hasattr(adapter, 'is_read_only')
        assert hasattr(adapter, 'auto_apply_enabled')
    
    @pytest.mark.asyncio
    async def test_mock_adapter_has_new_methods(self):
        """Test mock adapter has new methods."""
        adapter = MockMarketplaceAdapter()
        
        assert hasattr(adapter, 'refresh_authentication')
        assert hasattr(adapter, 'get_account_state')
        assert hasattr(adapter, 'get_application_requirements')
        assert hasattr(adapter, 'get_application_cost')
    
    @pytest.mark.asyncio
    async def test_mock_adapter_refresh_authentication(self):
        """Test refresh_authentication method."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate first
        account = await adapter.authenticate({})
        
        # Refresh authentication
        refreshed = await adapter.refresh_authentication()
        
        assert refreshed is not None
        assert refreshed.account_id == account.account_id
    
    @pytest.mark.asyncio
    async def test_mock_adapter_get_account_state(self):
        """Test get_account_state method."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate first
        await adapter.authenticate({})
        
        # Get account state
        state = await adapter.get_account_state()
        
        assert state is not None
        assert state.is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_mock_adapter_get_application_requirements(self):
        """Test get_application_requirements method."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate first
        await adapter.authenticate({})
        
        # Get requirements
        requirements = await adapter.get_application_requirements("test_job")
        
        assert requirements is not None
        assert "skills_required" in requirements
