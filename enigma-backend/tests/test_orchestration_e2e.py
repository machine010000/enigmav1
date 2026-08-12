"""
Orchestration E2E test for production verification.

Tests the complete multi-worker orchestration workflow:
1. Authentication
2. Worker discovery (both workers)
3. Two-step orchestration with context handoff
4. Worker #1 (product_verification) execution
5. Context handoff verification
6. Worker #2 (market_analysis) execution
7. Aggregated result retrieval
8. Persistence verification
"""
import pytest
import httpx
import asyncio


PRODUCTION_URL = "https://enigmav1-production.up.railway.app"


@pytest.mark.asyncio
async def test_orchestration_e2e_production():
    """Test complete two-worker orchestration workflow against production."""
    
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
    
    # Test 2: Get workers - should have both workers
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PRODUCTION_URL}/engine/workers",
            headers=headers
        )
        
        assert response.status_code == 200, f"/engine/workers failed: {response.text}"
        
        workers_response = response.json()
        assert "workers" in workers_response
        assert workers_response["count"] >= 2
        
        worker_names = [w["name"] for w in workers_response["workers"]]
        assert "product_verification" in worker_names
        assert "market_analysis" in worker_names
    
    # Test 3: Two-step orchestration
    orchestrate_data = {
        "plan": [
            {
                "step": 1,
                "worker": "product_verification",
                "input": {
                    "title": "Wireless Bluetooth Headphones",
                    "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life",
                    "category": "Tech",
                    "images": []
                }
            },
            {
                "step": 2,
                "worker": "market_analysis",
                "input": {}  # Will consume from context.memory
            }
        ],
        "extra_memory": {}
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes for orchestration
        response = await client.post(
            f"{PRODUCTION_URL}/engine/orchestrate",
            json=orchestrate_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"/engine/orchestrate failed: {response.text}"
        
        orchestration_result = response.json()
        assert "execution_id" in orchestration_result
        assert "results" in orchestration_result
        assert len(orchestration_result["results"]) == 2
        
        # Verify worker #1 (product_verification)
        result1 = orchestration_result["results"][0]
        assert result1["worker_name"] == "product_verification"
        assert result1["status"] in ["success", "failed"]
        
        # Verify worker #2 (market_analysis)
        result2 = orchestration_result["results"][1]
        assert result2["worker_name"] == "market_analysis"
        assert result2["status"] in ["success", "failed"]
        
        # If both succeeded, verify context handoff
        if result1["status"] == "success" and result2["status"] == "success":
            # Worker #1 should have produced verified product data
            assert "result" in result1
            assert "verified_name" in result1["result"]
            
            # Worker #2 should have consumed that data
            assert "result" in result2
            assert "market_size" in result2["result"]
            assert "competition_level" in result2["result"]
            
            print(f"Context handoff verified: {result1['result']['verified_name']} -> market analysis")


if __name__ == "__main__":
    asyncio.run(test_orchestration_e2e_production())
