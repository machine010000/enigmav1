"""
Failure/Retry Tests

Tests for timeout handling, retry policy, and circuit breaker.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.core.retry import (
    with_timeout,
    with_retry,
    with_timeout_and_retry,
    RetryError,
    TimeoutError as EnigmaTimeoutError,
    CircuitBreaker,
)


class TestTimeoutDecorator:
    """Test timeout decorator."""
    
    @pytest.mark.asyncio
    async def test_timeout_success(self):
        """Test timeout decorator with successful call."""
        @with_timeout(timeout_seconds=5)
        async def fast_function():
            return "success"
        
        result = await fast_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_raises_on_timeout(self):
        """Test timeout decorator raises on timeout."""
        @with_timeout(timeout_seconds=1)
        async def slow_function():
            await asyncio.sleep(2)
            return "success"
        
        with pytest.raises(EnigmaTimeoutError):
            await slow_function()
    
    @pytest.mark.asyncio
    async def test_timeout_uses_config_default(self):
        """Test timeout decorator uses config default."""
        from app.core.config import settings
        
        @with_timeout()
        async def function():
            return "success"
        
        # Should use settings.API_TIMEOUT_SECONDS
        result = await function()
        assert result == "success"


class TestRetryDecorator:
    """Test retry decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test retry decorator with success on first attempt."""
        @with_retry(max_retries=3)
        async def successful_function():
            return "success"
        
        result = await successful_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_retries_on_failure(self):
        """Test retry decorator retries on failure."""
        call_count = 0
        
        @with_retry(max_retries=3, delay_seconds=0.1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Test retry decorator exhausts all attempts."""
        @with_retry(max_retries=2, delay_seconds=0.1)
        async def failing_function():
            raise ValueError("Permanent failure")
        
        with pytest.raises(RetryError):
            await failing_function()
    
    @pytest.mark.asyncio
    async def test_retry_specific_exception(self):
        """Test retry decorator only retries specific exceptions."""
        @with_retry(max_retries=3, retry_on=(ValueError,))
        async def function():
            raise RuntimeError("Different exception")
        
        # Should not retry on RuntimeError, raise immediately
        with pytest.raises(RuntimeError):
            await function()
    
    @pytest.mark.asyncio
    async def test_retry_uses_config_default(self):
        """Test retry decorator uses config default."""
        from app.core.config import settings
        
        @with_retry()
        async def function():
            return "success"
        
        # Should use settings.MAX_RETRIES
        result = await function()
        assert result == "success"


class TestTimeoutAndRetryDecorator:
    """Test combined timeout and retry decorator."""
    
    @pytest.mark.asyncio
    async def test_timeout_and_retry_success(self):
        """Test combined decorator with success."""
        @with_timeout_and_retry(timeout_seconds=5, max_retries=2)
        async def successful_function():
            return "success"
        
        result = await successful_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_and_retry_retries(self):
        """Test combined decorator retries on failure."""
        call_count = 0
        
        @with_timeout_and_retry(timeout_seconds=5, max_retries=3, delay_seconds=0.1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_timeout_and_retry_timeout(self):
        """Test combined decorator times out."""
        @with_timeout_and_retry(timeout_seconds=1, max_retries=2)
        async def slow_function():
            await asyncio.sleep(2)
            return "success"
        
        with pytest.raises(EnigmaTimeoutError):
            await slow_function()


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_initially(self):
        """Test circuit breaker is closed initially."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        assert breaker.state == "closed"
        assert breaker.can_attempt() is True
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after failures."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        async def failing_function():
            raise ValueError("Failure")
        
        # First failure
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        
        # Second failure - should open circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        
        assert breaker.state == "open"
        assert breaker.can_attempt() is False
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks when open."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        async def failing_function():
            raise ValueError("Failure")
        
        # Trigger circuit to open
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        
        # Circuit should be open
        assert breaker.state == "open"
        
        # Attempt should be blocked
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            await breaker.call(failing_function)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers_after_timeout(self):
        """Test circuit breaker recovers after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        async def failing_function():
            raise ValueError("Failure")
        
        # Trigger circuit to open
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should be in half-open state
        assert breaker.can_attempt() is True
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_on_success(self):
        """Test circuit breaker closes on successful recovery."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        async def failing_function():
            raise ValueError("Failure")
        
        async def successful_function():
            return "success"
        
        # Trigger circuit to open
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Successful call should close circuit
        result = await breaker.call(successful_function)
        assert result == "success"
        assert breaker.state == "closed"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_counts_failures(self):
        """Test circuit breaker failure counting."""
        breaker = CircuitBreaker(failure_threshold=5)
        
        async def failing_function():
            raise ValueError("Failure")
        
        # 4 failures - should not open yet
        for _ in range(4):
            with pytest.raises(ValueError):
                await breaker.call(failing_function)
        
        assert breaker.state == "closed"
        assert breaker.failure_count == 4
        
        # 5th failure - should open
        with pytest.raises(ValueError):
            await breaker.call(failing_function)
        
        assert breaker.state == "open"
        assert breaker.failure_count == 5


class TestErrorHandling:
    """Test error handling in retry/timeout scenarios."""
    
    @pytest.mark.asyncio
    async def test_retry_error_contains_info(self):
        """Test RetryError contains attempt information."""
        @with_retry(max_retries=2, delay_seconds=0.1)
        async def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(RetryError) as exc_info:
            await failing_function()
        
        error = exc_info.value
        assert error.attempts == 2
        assert error.last_exception is not None
        assert "Test error" in str(error.last_exception)
    
    @pytest.mark.asyncio
    async def test_timeout_error_contains_info(self):
        """Test TimeoutError contains timeout information."""
        @with_timeout(timeout_seconds=1)
        async def slow_function():
            await asyncio.sleep(2)
        
        with pytest.raises(EnigmaTimeoutError) as exc_info:
            await slow_function()
        
        error = exc_info.value
        assert error.timeout_seconds == 1
        assert "timed out" in error.message.lower()
