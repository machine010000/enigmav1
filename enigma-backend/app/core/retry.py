"""
Retry Policy and Timeout Handling

Production-grade retry policy with exponential backoff and timeout handling.
"""

import asyncio
import time
from typing import Callable, TypeVar, Optional, Any, Type
from functools import wraps
from datetime import datetime

from app.core.config import settings


T = TypeVar('T')


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, attempts: int, last_exception: Exception):
        self.message = message
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"{message} (attempts: {attempts}, last error: {last_exception})")


class TimeoutError(Exception):
    """Exception raised when operation times out."""
    
    def __init__(self, message: str, timeout_seconds: int):
        self.message = message
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{message} (timeout: {timeout_seconds}s)")


def with_timeout(
    timeout_seconds: Optional[int] = None,
    error_message: str = "Operation timed out",
):
    """
    Decorator to add timeout handling to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds (uses config default if None)
        error_message: Error message on timeout
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            actual_timeout = timeout_seconds or settings.API_TIMEOUT_SECONDS
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=actual_timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(error_message, actual_timeout)
        return wrapper
    return decorator


def with_retry(
    max_retries: Optional[int] = None,
    delay_seconds: Optional[int] = None,
    backoff_factor: float = 2.0,
    retry_on: Optional[tuple[Type[Exception], ...]] = None,
):
    """
    Decorator to add retry logic with exponential backoff to async functions.
    
    Args:
        max_retries: Maximum number of retry attempts (uses config default if None)
        delay_seconds: Initial delay between retries (uses config default if None)
        backoff_factor: Multiplier for exponential backoff
        retry_on: Tuple of exception types to retry on (all exceptions if None)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            actual_max_retries = max_retries or settings.MAX_RETRIES
            actual_delay = delay_seconds or settings.RETRY_DELAY_SECONDS
            last_exception = None
            
            for attempt in range(actual_max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on if retry_on else Exception as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == actual_max_retries:
                        raise RetryError(
                            f"All {actual_max_retries} retry attempts exhausted",
                            actual_max_retries,
                            e
                        )
                    
                    # Calculate delay with exponential backoff
                    delay = actual_delay * (backoff_factor ** attempt)
                    
                    # Log retry attempt
                    print(f"Retry attempt {attempt + 1}/{actual_max_retries} after {delay}s delay (error: {str(e)})")
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but for type safety
            raise RetryError(
                f"All {actual_max_retries} retry attempts exhausted",
                actual_max_retries,
                last_exception or Exception("Unknown error")
            )
        return wrapper
    return decorator


def with_timeout_and_retry(
    timeout_seconds: Optional[int] = None,
    max_retries: Optional[int] = None,
    delay_seconds: Optional[int] = None,
    backoff_factor: float = 2.0,
    retry_on: Optional[tuple[Type[Exception], ...]] = None,
):
    """
    Decorator to add both timeout and retry logic to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds (uses config default if None)
        max_retries: Maximum number of retry attempts (uses config default if None)
        delay_seconds: Initial delay between retries (uses config default if None)
        backoff_factor: Multiplier for exponential backoff
        retry_on: Tuple of exception types to retry on (all exceptions if None)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            actual_timeout = timeout_seconds or settings.API_TIMEOUT_SECONDS
            actual_max_retries = max_retries or settings.MAX_RETRIES
            actual_delay = delay_seconds or settings.RETRY_DELAY_SECONDS
            last_exception = None
            
            for attempt in range(actual_max_retries + 1):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=actual_timeout
                    )
                except asyncio.TimeoutError as e:
                    last_exception = e
                    
                    if attempt == actual_max_retries:
                        raise TimeoutError(
                            f"Operation timed out after {actual_max_retries} retry attempts",
                            actual_timeout
                        )
                    
                    delay = actual_delay * (backoff_factor ** attempt)
                    print(f"Retry attempt {attempt + 1}/{actual_max_retries} after timeout (delay: {delay}s)")
                    await asyncio.sleep(delay)
                    
                except retry_on if retry_on else Exception as e:
                    last_exception = e
                    
                    if attempt == actual_max_retries:
                        raise RetryError(
                            f"All {actual_max_retries} retry attempts exhausted",
                            actual_max_retries,
                            e
                        )
                    
                    delay = actual_delay * (backoff_factor ** attempt)
                    print(f"Retry attempt {attempt + 1}/{actual_max_retries} after error: {str(e)} (delay: {delay}s)")
                    await asyncio.sleep(delay)
            
            raise RetryError(
                f"All {actual_max_retries} retry attempts exhausted",
                actual_max_retries,
                last_exception or Exception("Unknown error")
            )
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for handling repeated failures.
    
    Opens circuit after consecutive failures, preventing calls to failing service.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to count as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            print(f"Circuit breaker opened after {self.failure_count} failures")
    
    def record_success(self) -> None:
        """Record a success and reset failure count."""
        self.failure_count = 0
        self.last_failure_time = None
        if self.state == "half-open":
            self.state = "closed"
            print("Circuit breaker closed after successful recovery")
    
    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "half-open"
                    print("Circuit breaker entering half-open state for recovery attempt")
                    return True
            return False
        
        # half-open state - allow one attempt
        return True
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if not self.can_attempt():
            raise RuntimeError("Circuit breaker is open - service unavailable")
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass
