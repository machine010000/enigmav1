"""
Base Marketplace Adapter

TASK-051: Base adapter with read-only mode, timeout/retry, and safety checks.
"""

from abc import ABC
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.marketplace.contracts import (
    MarketplaceAdapter,
    MarketplacePlatform,
    MarketplaceAccount,
    NormalizedJob,
    NormalizedApplication,
    PlatformCost,
    PlatformLimits,
    ApplicationStatus,
    PlatformCapability,
)
from app.marketplace.auth import CredentialProvider, TokenStore, ConnectionStatus
from app.marketplace.capabilities import PlatformCapabilities, CapabilityStatus
from app.marketplace.errors import APIError, APIErrorHandler, RateLimitHandler
from app.core.retry import with_timeout_and_retry, TimeoutError as EnigmaTimeoutError


class BaseMarketplaceAdapter(MarketplaceAdapter, ABC):
    """
    Base marketplace adapter with common functionality.
    
    TASK-051: Read-only by default, no automatic application submission.
    Integrates timeout/retry from TASK-050.
    """
    
    def __init__(
        self,
        platform: MarketplacePlatform,
        credential_provider: Optional[CredentialProvider] = None,
        token_store: Optional[TokenStore] = None,
        read_only: bool = True,
        auto_apply_enabled: bool = False,
    ):
        """
        Initialize base adapter.
        
        Args:
            platform: Platform identifier
            credential_provider: Credential provider (uses global if None)
            token_store: Token store (uses global if None)
            read_only: Whether adapter is in read-only mode (TASK-051: default True)
            auto_apply_enabled: Whether auto-apply is enabled (TASK-051: default False)
        """
        self._platform = platform
        self._read_only = read_only
        self._auto_apply_enabled = auto_apply_enabled
        
        # Use global instances if not provided
        from app.marketplace.auth import credential_provider as global_credential_provider
        from app.marketplace.auth import token_store as global_token_store
        from app.marketplace.auth import connection_status as global_connection_status
        from app.marketplace.errors import rate_limit_handler as global_rate_limit_handler
        
        self._credential_provider = credential_provider or global_credential_provider
        self._token_store = token_store or global_token_store
        self._connection_status = global_connection_status
        self._rate_limit_handler = global_rate_limit_handler
        
        # Initialize capabilities
        self._capabilities = PlatformCapabilities(platform.value)
        self._declare_capabilities()
    
    @property
    def platform(self) -> MarketplacePlatform:
        """Get platform."""
        return self._platform
    
    @property
    def is_read_only(self) -> bool:
        """Get read-only mode."""
        return self._read_only
    
    @property
    def auto_apply_enabled(self) -> bool:
        """Get auto-apply enabled status."""
        return self._auto_apply_enabled
    
    @property
    def capabilities(self) -> List[PlatformCapability]:
        """Get supported capabilities."""
        from app.marketplace.contracts import PlatformCapability
        
        # Map capability strings to PlatformCapability enum
        supported = self._capabilities.get_supported_capabilities()
        
        capability_map = {
            "job_search": PlatformCapability.JOB_DISCOVERY,
            "job_details": PlatformCapability.JOB_RETRIEVAL,
            "application_submission": PlatformCapability.APPLICATION_SUBMISSION,
            "application_status": PlatformCapability.APPLICATION_STATUS_TRACKING,
            "account_balance": PlatformCapability.CREDIT_MANAGEMENT,
            "account_status": PlatformCapability.ACCOUNT_STATUS_CHECK,
        }
        
        result = []
        for cap in supported:
            if cap in capability_map:
                result.append(capability_map[cap])
        
        return result
    
    def _declare_capabilities(self) -> None:
        """
        Declare platform capabilities.
        
        Subclasses should override this to declare their capabilities.
        Default: all capabilities UNKNOWN.
        """
        pass
    
    def enable_read_only(self) -> None:
        """Enable read-only mode."""
        self._read_only = True
    
    def disable_read_only(self) -> None:
        """Disable read-only mode (use with caution)."""
        self._read_only = False
    
    def enable_auto_apply(self) -> None:
        """Enable auto-apply (use with caution)."""
        self._auto_apply_enabled = True
    
    def disable_auto_apply(self) -> None:
        """Disable auto-apply."""
        self._auto_apply_enabled = False
    
    async def submit_application(
        self,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """
        Submit application with safety checks.
        
        TASK-051: Gated by read-only mode and auto_apply_enabled.
        
        Raises:
            RuntimeError: If read-only or auto_apply disabled
        """
        if self._read_only:
            raise RuntimeError(
                f"Cannot submit application: {self.platform.value} adapter is in read-only mode"
            )
        
        if not self._auto_apply_enabled:
            raise RuntimeError(
                f"Cannot submit application: auto-apply is disabled for {self.platform.value}"
            )
        
        # Subclasses implement actual submission
        return await self._do_submit_application(application)
    
    async def _do_submit_application(
        self,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """
        Actual application submission implementation.
        
        Subclasses must implement this.
        """
        raise NotImplementedError("Subclasses must implement _do_submit_application")
    
    async def _call_api_with_retry(
        self,
        api_call,
        *args,
        **kwargs
    ) -> Any:
        """
        Call API with timeout and retry from TASK-050.
        
        Args:
            api_call: Async function to call
            *args: Arguments for API call
            **kwargs: Keyword arguments for API call
            
        Returns:
            API response
            
        Raises:
            EnigmaTimeoutError: If timeout occurs
            APIError: If API error occurs
        """
        try:
            # Use timeout and retry from TASK-050
            decorated_call = with_timeout_and_retry(
                timeout_seconds=30,
                max_retries=3,
                delay_seconds=1,
            )(api_call)
            
            return await decorated_call(*args, **kwargs)
        
        except EnigmaTimeoutError as e:
            # Convert to API error
            raise APIError(
                error_type=APIErrorHandler._determine_error_type(None, str(e)),
                platform=self.platform.value,
                message=str(e),
                is_retriable=True,
            )
        
        except Exception as e:
            # Classify as API error
            api_error = APIErrorHandler.classify_error(
                platform=self.platform.value,
                status_code=None,
                error_message=str(e),
            )
            raise api_error
    
    def _check_rate_limit(self) -> tuple[bool, Optional[float]]:
        """
        Check rate limit before API call.
        
        Returns:
            Tuple of (can_request, wait_seconds)
        """
        return self._rate_limit_handler.can_request(self.platform.value)
    
    def _update_rate_limit(self, limit_info) -> None:
        """
        Update rate limit after API call.
        
        Args:
            limit_info: Rate limit info from API response
        """
        from app.marketplace.errors import RateLimitInfo
        
        if limit_info:
            self._rate_limit_handler.update_limit(
                self.platform.value,
                RateLimitInfo(
                    limit=limit_info.get("limit", 0),
                    remaining=limit_info.get("remaining", 0),
                    reset_at=datetime.fromisoformat(limit_info["reset_at"]) if limit_info.get("reset_at") else None,
                    window_seconds=limit_info.get("window_seconds"),
                )
            )
    
    def _report_api_error(self, error: APIError) -> None:
        """
        Report API error to Enigma Profile.
        
        TASK-051: API failures map to Enigma Issues.
        
        Args:
            error: API error to report
        """
        # Convert to Enigma Issue format
        issue_data = error.to_enigma_issue()
        
        # Report to Enigma Profile (if available)
        try:
            from app.enigma_profile import EnigmaProfileManager
            from app.marketplace.contracts import MarketplacePlatform
            
            manager = EnigmaProfileManager()
            manager.report_system_issue(
                issue_data["detected_reason"],
                MarketplacePlatform(self.platform),
                issue_type=issue_data["type"],
                severity=issue_data["severity"],
            )
        except Exception:
            # If Enigma Profile is not available, log the error
            print(f"API Error: {error.error_type.value} - {error.message}")
    
    async def _safe_api_call(
        self,
        api_call,
        *args,
        **kwargs
    ) -> Any:
        """
        Safe API call with error handling.
        
        TASK-051: Handles rate limiting, errors, and reporting.
        
        Args:
            api_call: Async function to call
            *args: Arguments for API call
            **kwargs: Keyword arguments for API call
            
        Returns:
            API response
        """
        # Check rate limit
        can_request, wait_seconds = self._check_rate_limit()
        if not can_request:
            raise APIError(
                error_type=APIErrorHandler._determine_error_type(429, "Rate limit exceeded"),
                platform=self.platform.value,
                message=f"Rate limit exceeded. Wait {wait_seconds} seconds.",
                is_rate_limit=True,
                is_retriable=True,
            )
        
        try:
            # Call API with retry
            response = await self._call_api_with_retry(api_call, *args, **kwargs)
            
            # Record request
            self._rate_limit_handler.record_request(self.platform.value)
            
            return response
        
        except APIError as e:
            # Report to Enigma Profile
            self._report_api_error(e)
            raise
        
        except Exception as e:
            # Wrap unknown errors
            api_error = APIErrorHandler.classify_error(
                platform=self.platform.value,
                status_code=None,
                error_message=str(e),
            )
            self._report_api_error(api_error)
            raise api_error
