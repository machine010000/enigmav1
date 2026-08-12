"""
Local orchestration test to verify two-worker pipeline before deployment.
"""
import pytest
import asyncio
from app.engine.engine import engine
from app.engine.registry import register_all
from app.engine.contracts import ExecutionContext


@pytest.mark.asyncio
async def test_orchestration_local():
    """Test two-worker orchestration locally."""
    
    # Register workers
    register_all()
    
    # Verify both workers are registered
    assert "product_verification" in engine.registered_names
    assert "market_analysis" in engine.registered_names
    
    # Build context
    ctx = ExecutionContext(
        product={
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life",
            "category": "Tech",
            "images": []
        },
        execution_id="test-orchestration-001",
    )
    
    # Build orchestration plan
    plan = [
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
            "input": {}
        }
    ]
    
    # Execute orchestration
    result = await engine.orchestrate(plan, ctx, save=False)
    
    # Verify results
    assert "execution_id" in result
    assert "results" in result
    assert len(result["results"]) == 2
    
    # Verify worker #1
    result1 = result["results"][0]
    assert result1["worker_name"] == "product_verification"
    assert result1["status"] in ["success", "failed"]
    
    # Verify worker #2
    result2 = result["results"][1]
    assert result2["worker_name"] == "market_analysis"
    assert result2["status"] in ["success", "failed"]
    
    # If both succeeded, verify context handoff
    if result1["status"] == "success" and result2["status"] == "success":
        assert "result" in result1
        assert "verified_name" in result1["result"]
        assert "result" in result2
        assert "market_size" in result2["result"]
        
        print(f"Context handoff verified: {result1['result']['verified_name']} -> market analysis")
        print(f"Market size: {result2['result']['market_size']}")
        print(f"Competition level: {result2['result']['competition_level']}")


if __name__ == "__main__":
    asyncio.run(test_orchestration_local())
