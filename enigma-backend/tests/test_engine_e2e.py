"""
Engine E2E test for production verification.

Tests the complete Engine workflow:
1. Authentication
2. Worker discovery
3. Execution creation
4. Worker execution
5. Status retrieval
6. Result retrieval
"""
import pytest
import httpx
import asyncio


PRODUCTION_URL = "https://enigmav1-production.up.railway.app"


@pytest.mark.asyncio
async def test_engine_e2e_production():
    """Test complete Engine workflow against production."""
    
    # Test 1: Login
    login_data = {
        "username": "test@test.com",
        "password": "test123"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{PRODUCTION_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        login_response = response.json()
        access_token = login_response["access_token"]
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Test 2: Get workers
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PRODUCTION_URL}/engine/workers",
            headers=headers
        )
        
        assert response.status_code == 200, f"/engine/workers failed: {response.text}"
        
        workers_response = response.json()
        assert "workers" in workers_response
        assert workers_response["count"] > 0
        assert any(w["name"] == "product_verification" for w in workers_response["workers"])
    
    # Test 3: Execute product_verification worker with direct product context
    execute_data = {
        "worker": "product_verification",
        "context": {
            "title": "Test Product",
            "description": "A test product for engine verification",
            "category": "Tech",
            "images": []
        }
    }
    
    async with httpx.AsyncClient(timeout=150.0) as client:  # 150s for worker execution
        response = await client.post(
            f"{PRODUCTION_URL}/engine/execute",
            json=execute_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"/engine/execute failed: {response.text}"
        
        execution_result = response.json()
        assert "worker_name" in execution_result
        assert "status" in execution_result
        assert "result" in execution_result
        assert execution_result["worker_name"] == "product_verification"
        
        execution_id = execution_result.get("metadata", {}).get("execution_id")
        
        # Test 4: Get execution status
        if execution_id:
            status_response = await client.get(
                f"{PRODUCTION_URL}/engine/executions/{execution_id}/status",
                headers=headers
            )
            
            assert status_response.status_code == 200, f"/engine/executions/{id}/status failed: {status_response.text}"
            
            status_data = status_response.json()
            assert "status" in status_data
            assert status_data["status"] in ["success", "failed"]
            
            # Test 5: Get execution result
            result_response = await client.get(
                f"{PRODUCTION_URL}/engine/executions/{execution_id}/result",
                headers=headers
            )
            
            assert result_response.status_code == 200, f"/engine/executions/{id}/result failed: {result_response.text}"
            
            result_data = result_response.json()
            assert "result" in result_data
            assert "evidence" in result_data


if __name__ == "__main__":
    asyncio.run(test_engine_e2e_production())
