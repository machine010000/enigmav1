"""
Structured Error Reporting

Production-grade error handling with no silent fallback.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import traceback
import sys

from app.core.config import settings


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ErrorCategory(Enum):
    """Error categories."""
    CONFIGURATION = "configuration"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"
    TIMEOUT = "timeout"


class EnigmaError(Exception):
    """
    Base exception for Enigma application errors.
    
    All application errors should inherit from this to ensure
    structured error reporting and no silent fallback.
    """
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize Enigma error.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            context: Additional context about the error
            original_exception: Original exception if wrapping another error
        """
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow().isoformat()
        self.traceback = traceback.format_exc() if original_exception else None
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "timestamp": self.timestamp,
            "traceback": self.traceback,
            "environment": settings.ENVIRONMENT,
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"[{self.severity.value.upper()}] {self.category.value}: {self.message}"


class ConfigurationError(EnigmaError):
    """Configuration error."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.CRITICAL,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class DatabaseError(EnigmaError):
    """Database error."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class ExternalAPIError(EnigmaError):
    """External API error."""
    
    def __init__(
        self,
        message: str,
        service: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        context = context or {}
        context["service"] = service
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class ValidationError(EnigmaError):
    """Validation error."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        context = context or {}
        if field:
            context["field"] = field
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class AuthenticationError(EnigmaError):
    """Authentication error."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class AuthorizationError(EnigmaError):
    """Authorization error."""
    
    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        context = context or {}
        if resource:
            context["resource"] = resource
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class BusinessLogicError(EnigmaError):
    """Business logic error."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class SystemError(EnigmaError):
    """System error."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.CRITICAL,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class NetworkError(EnigmaError):
    """Network error."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class TimeoutError(EnigmaError):
    """Timeout error."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        context = context or {}
        if operation:
            context["operation"] = operation
        if timeout_seconds:
            context["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=severity,
            context=context,
            original_exception=original_exception,
        )


class ErrorReporter:
    """Error reporter for structured error logging."""
    
    def __init__(self):
        """Initialize error reporter."""
        self._errors: List[Dict[str, Any]] = []
    
    def report_error(
        self,
        error: EnigmaError,
        log_to_console: bool = True,
    ) -> Dict[str, Any]:
        """
        Report an error.
        
        Args:
            error: Enigma error to report
            log_to_console: Whether to log to console
            
        Returns:
            Error dictionary
        """
        error_dict = error.to_dict()
        self._errors.append(error_dict)
        
        if log_to_console:
            self._log_error(error_dict)
        
        return error_dict
    
    def _log_error(self, error_dict: Dict[str, Any]) -> None:
        """Log error to console."""
        severity = error_dict["severity"].upper()
        category = error_dict["category"].upper()
        message = error_dict["message"]
        
        print(f"[{severity}] {category}: {message}")
        
        if error_dict.get("traceback"):
            print(f"Traceback: {error_dict['traceback']}")
        
        if error_dict.get("context"):
            print(f"Context: {error_dict['context']}")
    
    def get_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get filtered errors.
        
        Args:
            severity: Filter by severity
            category: Filter by category
            limit: Maximum number of errors to return
            
        Returns:
            Filtered error list
        """
        filtered = self._errors
        
        if severity:
            filtered = [e for e in filtered if e["severity"] == severity.value]
        
        if category:
            filtered = [e for e in filtered if e["category"] == category.value]
        
        if limit:
            filtered = filtered[-limit:]
        
        return filtered
    
    def clear_errors(self) -> None:
        """Clear all reported errors."""
        self._errors = []
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return any(e["severity"] == ErrorSeverity.CRITICAL.value for e in self._errors)


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    default_message: str = "An error occurred",
) -> EnigmaError:
    """
    Handle any exception and convert to EnigmaError.
    
    This ensures no silent fallback - all errors are properly wrapped and reported.
    
    Args:
        error: Exception to handle
        context: Additional context
        default_message: Default message if error is not EnigmaError
        
    Returns:
        EnigmaError
    """
    if isinstance(error, EnigmaError):
        return error
    
    # Determine category based on exception type
    if "database" in str(type(error)).lower() or "sql" in str(type(error)).lower():
        category = ErrorCategory.DATABASE
    elif "timeout" in str(error).lower():
        category = ErrorCategory.TIMEOUT
    elif "network" in str(error).lower() or "connection" in str(error).lower():
        category = ErrorCategory.NETWORK
    elif "auth" in str(error).lower():
        category = ErrorCategory.AUTHENTICATION
    elif "validation" in str(error).lower() or "value" in str(type(error)).lower():
        category = ErrorCategory.VALIDATION
    else:
        category = ErrorCategory.SYSTEM
    
    return EnigmaError(
        message=default_message,
        category=category,
        severity=ErrorSeverity.HIGH,
        context=context,
        original_exception=error,
    )


def no_silent_fallback(func):
    """
    Decorator to ensure no silent fallback in functions.
    
    Any exception will be wrapped in EnigmaError and raised.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, EnigmaError):
                raise
            
            # Wrap in EnigmaError to ensure no silent fallback
            raise handle_error(e, default_message=f"Error in {func.__name__}")
    
    return wrapper


# Global error reporter instance
error_reporter = ErrorReporter()
