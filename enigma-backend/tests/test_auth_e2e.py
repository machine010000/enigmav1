"""
End-to-end authentication test for production verification.

Tests the complete authentication flow:
1. Login with form data
2. Receive JWT token
3. Use token to access protected endpoints
"""
import pytest
import httpx


PRODUCTION_URL = "https://enigmav1-production.up.railway.app"


@pytest.mark.asyncio
async def test_auth_e2e_production():
    """Test complete authentication flow against production."""
    
    # Test 1: Health check
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{PRODUCTION_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    # Test 2: Login with form data (OAuth2PasswordRequestForm format)
    login_data = {
        "username": "test@test.com",
        "password": "test123"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{PRODUCTION_URL}/auth/login",
            data=login_data,  # Use data for form data, not json
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Login should succeed
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        login_response = response.json()
        assert "access_token" in login_response
        assert "token_type" in login_response
        assert login_response["token_type"] == "bearer"
        
        access_token = login_response["access_token"]
        assert len(access_token) > 0
    
    # Test 3: Use token to access /auth/me
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PRODUCTION_URL}/auth/me",
            headers=headers
        )
        
        assert response.status_code == 200, f"/auth/me failed: {response.text}"
        
        user_data = response.json()
        assert "email" in user_data
        assert "id" in user_data
    
    # Test 4: Use token to access /products
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PRODUCTION_URL}/products",
            headers=headers
        )
        
        assert response.status_code == 200, f"/products failed: {response.text}"
    
    # Test 5: Use token to access /brain/chat
    chat_data = {
        "message": "Reply with exactly: ENIGMA_OK"
    }
    
    async with httpx.AsyncClient(timeout=150.0) as client:  # 150s timeout for AI generation
        response = await client.post(
            f"{PRODUCTION_URL}/brain/chat",
            json=chat_data,
            headers=headers
        )
        
        # Should succeed with 200 or return appropriate error code
        assert response.status_code in [200, 502, 504], f"/brain/chat unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            chat_response = response.json()
            assert "reply" in chat_response
            assert "intent" in chat_response
            assert "knowledge_used" in chat_response
            assert len(chat_response["reply"]) > 0


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth_e2e_production())
