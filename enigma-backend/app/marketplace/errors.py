"""
API Failure Intelligence

TASK-051: API failures map to Enigma Issues.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class APIErrorType(str, Enum):
    """API error types that map to Enigma Issues."""
    AUTH_EXPIRED = "AUTH_EXPIRED"
    RATE_LIMITED = "RATE_LIMITED"
    API_UNAVAILABLE = "API_UNAVAILABLE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    UNKNOWN_COST = "UNKNOWN_COST"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class APIError:
    """API error with context."""
    error_type: APIErrorType
    platform: str
    message: str
    status_code: Optional[int] = None
    is_retriable: bool = False
    is_auth_error: bool = False
    is_rate_limit: bool = False
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Auto-set is_auth_error based on error type (always set based on type)
        self.is_auth_error = self._is_auth_error_type()
        
        # Auto-set is_rate_limit based on error type (always set based on type)
        self.is_rate_limit = self.error_type == APIErrorType.RATE_LIMITED
    
    def to_enigma_issue(self) -> Dict[str, Any]:
        """
        Convert API error to Enigma Issue format.
        
        Returns:
            Dictionary compatible with Enigma Profile issue reporting
        """
        return {
            "source": "marketplace_api",
            "type": self.error_type.value,
            "severity": self._determine_severity(),
            "detected_reason": self.message,
            "platform": self.platform,
            "is_retriable": self.is_retriable,
            "is_auth_error": self.is_auth_error,
            "is_rate_limit": self.is_rate_limit,
            "status_code": self.status_code,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def _determine_severity(self) -> str:
        """Determine issue severity based on error type."""
        critical_errors = {
            APIErrorType.AUTH_EXPIRED,
            APIErrorType.ACCOUNT_SUSPENDED,
            APIErrorType.PERMISSION_DENIED,
        }
        
        high_errors = {
            APIErrorType.QUOTA_EXCEEDED,
            APIErrorType.UNKNOWN_COST,
            APIErrorType.API_UNAVAILABLE,
        }
        
        if self.error_type in critical_errors:
            return "CRITICAL"
        elif self.error_type in high_errors:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _is_auth_error_type(self) -> bool:
        """Check if error type is auth-related."""
        return self.error_type in {
            APIErrorType.AUTH_EXPIRED,
            APIErrorType.PERMISSION_DENIED,
        }


class APIErrorHandler:
    """
    Handler for API errors.
    
    TASK-051: Converts API failures to Enigma Issues.
    """
    
    @staticmethod
    def classify_error(
        platform: str,
        status_code: Optional[int],
        error_message: str,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> APIError:
        """
        Classify an API error.
        
        Args:
            platform: Platform identifier
            status_code: HTTP status code
            error_message: Error message
            response_body: Response body (if available)
            
        Returns:
            Classified API error
        """
        error_type = APIErrorHandler._determine_error_type(status_code, error_message, response_body)
        is_retriable = APIErrorHandler._is_retriable(error_type, status_code)
        is_auth_error = error_type in [APIErrorType.AUTH_EXPIRED, APIErrorType.PERMISSION_DENIED]
        is_rate_limit = error_type == APIErrorType.RATE_LIMITED
        
        return APIError(
            error_type=error_type,
            platform=platform,
            message=error_message,
            status_code=status_code,
            is_retriable=is_retriable,
            is_auth_error=is_auth_error,
            is_rate_limit=is_rate_limit,
            metadata={"response_body": response_body} if response_body else {},
        )
    
    @staticmethod
    def _determine_error_type(
        status_code: Optional[int],
        error_message: str,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> APIErrorType:
        """Determine error type from status code and message."""
        # Check status code first
        if status_code:
            if status_code == 401:
                return APIErrorType.AUTH_EXPIRED
            elif status_code == 403:
                return APIErrorType.PERMISSION_DENIED
            elif status_code == 429:
                return APIErrorType.RATE_LIMITED
            elif status_code >= 500:
                return APIErrorType.API_UNAVAILABLE
            elif status_code >= 400:
                return APIErrorType.INVALID_RESPONSE
        
        # Check error message
        error_message_lower = error_message.lower()
        
        if "auth" in error_message_lower or "token" in error_message_lower or "expired" in error_message_lower:
            return APIErrorType.AUTH_EXPIRED
        elif "rate limit" in error_message_lower or "too many requests" in error_message_lower:
            return APIErrorType.RATE_LIMITED
        elif "quota" in error_message_lower or "limit" in error_message_lower:
            return APIErrorType.QUOTA_EXCEEDED
        elif "suspended" in error_message_lower or "banned" in error_message_lower:
            return APIErrorType.ACCOUNT_SUSPENDED
        elif "permission" in error_message_lower or "forbidden" in error_message_lower:
            return APIErrorType.PERMISSION_DENIED
        elif "timeout" in error_message_lower or "timed out" in error_message_lower:
            return APIErrorType.TIMEOUT
        elif "network" in error_message_lower or "connection" in error_message_lower:
            return APIErrorType.NETWORK_ERROR
        
        # Check response body
        if response_body:
            error_code = response_body.get("error_code", "")
            if "auth" in error_code.lower() or "token" in error_code.lower():
                return APIErrorType.AUTH_EXPIRED
            elif "rate" in error_code.lower():
                return APIErrorType.RATE_LIMITED
        
        return APIErrorType.UNKNOWN_ERROR
    
    @staticmethod
    def _is_retriable(error_type: APIErrorType, status_code: Optional[int]) -> bool:
        """Determine if error is retriable."""
        retriable_types = {
            APIErrorType.RATE_LIMITED,
            APIErrorType.API_UNAVAILABLE,
            APIErrorType.TIMEOUT,
            APIErrorType.NETWORK_ERROR,
        }
        
        if error_type in retriable_types:
            return True
        
        # 5xx errors are retriable
        if status_code and status_code >= 500:
            return True
        
        return False


class RateLimitInfo:
    """Rate limit information."""
    
    def __init__(
        self,
        limit: int,
        remaining: int,
        reset_at: Optional[datetime] = None,
        window_seconds: Optional[int] = None,
    ):
        """
        Initialize rate limit info.
        
        Args:
            limit: Rate limit
            remaining: Remaining requests
            reset_at: When limit resets
            window_seconds: Time window in seconds
        """
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        self.window_seconds = window_seconds
    
    def is_exceeded(self) -> bool:
        """Check if rate limit is exceeded."""
        return self.remaining <= 0
    
    def wait_seconds(self) -> Optional[float]:
        """Get seconds to wait before next request."""
        if not self.reset_at:
            return None
        return (self.reset_at - datetime.utcnow()).total_seconds()


class RateLimitHandler:
    """
    Rate limit handler.
    
    TASK-051: Handles rate limiting from marketplace APIs.
    """
    
    def __init__(self):
        """Initialize rate limit handler."""
        self._limits: Dict[str, RateLimitInfo] = {}
    
    def update_limit(self, platform: str, limit_info: RateLimitInfo) -> None:
        """
        Update rate limit for a platform.
        
        Args:
            platform: Platform identifier
            limit_info: Rate limit information
        """
        self._limits[platform] = limit_info
    
    def get_limit(self, platform: str) -> Optional[RateLimitInfo]:
        """
        Get rate limit for a platform.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Rate limit info or None
        """
        return self._limits.get(platform)
    
    def can_request(self, platform: str) -> tuple[bool, Optional[float]]:
        """
        Check if request can be made.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Tuple of (can_request, wait_seconds)
        """
        limit_info = self.get_limit(platform)
        if not limit_info:
            return True, None
        
        if limit_info.is_exceeded():
            wait_seconds = limit_info.wait_seconds()
            if wait_seconds and wait_seconds > 0:
                return False, wait_seconds
        
        return True, None
    
    def record_request(self, platform: str) -> None:
        """
        Record a request (decrement remaining).
        
        Args:
            platform: Platform identifier
        """
        limit_info = self.get_limit(platform)
        if limit_info and limit_info.remaining > 0:
            limit_info.remaining -= 1
            self._limits[platform] = limit_info


# Global instances
api_error_handler = APIErrorHandler()
rate_limit_handler = RateLimitHandler()
