"""
Test brain route error mapping for AI provider failures.

Tests that AI provider errors are correctly mapped to HTTP status codes.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.ai.client import AITimeoutError, AIProviderError, AIAuthenticationError
from app.routers.master_brain import router, chat_with_master_brain
from app.models.user import User
from uuid import uuid4


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        hashed_password="hash",
        plan="free"
    )


def test_timeout_maps_to_504():
    """Test that AITimeoutError maps to HTTP 504 Gateway Timeout."""
    from app.ai.master_brain import master_brain
    from fastapi import HTTPException
    
    mock_user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        hashed_password="hash",
        plan="free"
    )
    
    with patch.object(master_brain, 'chat', side_effect=AITimeoutError("NVIDIA API request timed out")):
        with pytest.raises(HTTPException) as exc_info:
            # Call the router function directly
            import asyncio
            asyncio.run(chat_with_master_brain(
                data=MagicMock(message="test"),
                current_user=mock_user,
                db=AsyncMock()
            ))
        
        # Verify the HTTPException has status 504 and generic safe message
        assert exc_info.value.status_code == 504
        # TASK-016: unified error message — does not expose error type detail
        assert "AI provider" in exc_info.value.detail


def test_timeout_exception_propagates():
    """Test that AITimeoutError propagates through MasterBrain.chat."""
    from app.ai.master_brain import master_brain
    from app.ai.client import AITimeoutError
    
    with patch("app.ai.gateway.gateway.chat", side_effect=AITimeoutError("timeout")):
        with pytest.raises(AITimeoutError):
            import asyncio
            asyncio.run(master_brain.chat(
                db=AsyncMock(),
                user_id=str(uuid4()),
                message="test"
            ))


def test_provider_error_propagates():
    """Test that AIProviderError propagates through MasterBrain.chat."""
    from app.ai.master_brain import master_brain
    from app.ai.client import AIProviderError
    
    with patch("app.ai.gateway.gateway.chat", side_effect=AIProviderError("provider error")):
        with pytest.raises(AIProviderError):
            import asyncio
            asyncio.run(master_brain.chat(
                db=AsyncMock(),
                user_id=str(uuid4()),
                message="test"
            ))


def test_provider_error_maps_to_502():
    """Test that AIProviderError maps to HTTP 502 Bad Gateway."""
    from app.ai.master_brain import master_brain
    from fastapi import HTTPException
    
    mock_user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        hashed_password="hash",
        plan="free"
    )
    
    with patch.object(master_brain, 'chat', side_effect=AIProviderError("NVIDIA API request failed")):
        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.run(chat_with_master_brain(
                data=MagicMock(message="test"),
                current_user=mock_user,
                db=AsyncMock()
            ))
        
        # Verify the HTTPException has status 502
        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "AI provider error. Please try again later."


def test_successful_response_preserves_contract():
    """Test that successful AI responses preserve the expected contract."""
    from app.ai.master_brain import master_brain
    
    mock_gateway_response = {
        "choices": [
            {"message": {"content": "Test AI response"}}
        ]
    }
    
    with patch("app.ai.gateway.gateway.chat", return_value=mock_gateway_response):
        import asyncio
        result = asyncio.run(master_brain.chat(
            db=AsyncMock(),
            user_id=str(uuid4()),
            message="test"
        ))
        
        assert result["reply"] == "Test AI response"
        assert result["intent"] == "general"
        assert result["knowledge_used"] == []
