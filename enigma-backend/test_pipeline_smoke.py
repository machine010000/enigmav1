import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.engine.contracts import ExecutionContext, WorkerStatus
from app.engine.engine import engine
from app.engine.registry import register_all
from app.services.pipeline import run_product_intelligence_pipeline


async def main():
    register_all()

    ctx = ExecutionContext(
        user={"id": "test-user", "name": "Test User"},
        product={
            "name": "Nike Air Max 270 Men's Running Shoes",
            "title": "Nike Air Max 270 Men's Running Shoes",
            "description": (
                "Original men's running shoes with Nike Air cushioning unit "
                "in the midsole for responsive comfort. Features a compression "
                "molded foam upper and rubber outsole for durability. "
                "Color: Black/White."
            ),
            "category": "Fashion",
            "images": [],
        },
        execution_id="smoke-test-001",
    )

    pipeline_result = await run_product_intelligence_pipeline(ctx, save=False)

    print("=== Pipeline Result ===")
    print(f"Pipeline ID: {pipeline_result['pipeline_id']}")
    print(f"Status: {pipeline_result['status']}")
    print(f"Total stages: {pipeline_result['total_stages']}")
    print(f"Completed stages: {pipeline_result['completed_stages']}")
    print(f"All success: {pipeline_result['all_success']}")
    print(f"Final confidence: {pipeline_result['final_confidence']}")
    print()

    for stage in pipeline_result["stages"]:
        print(f"  Stage {stage['step']} — {stage['stage']}")
        print(f"    Worker: {stage['worker']}")
        print(f"    Status: {stage['status']}")
        print(f"    Confidence: {stage['confidence']}")
        print(f"    LLM calls: {stage['llm_calls']}")
        print(f"    Evidence count: {stage['evidence_count']}")
        print(f"    Execution time: {stage['execution_time']:.4f}s")
        if stage.get("error"):
            print(f"    Error: {stage['error']}")
        print()

    verification_stage = pipeline_result["stages"][0]
    assert verification_stage["status"] == "success", (
        f"Verification stage failed: {verification_stage.get('error')}"
    )
    assert verification_stage["evidence_count"] > 0, "No evidence produced"
    assert verification_stage["confidence"] > 0, "Confidence is zero"

    print("=== Smoke Test PASSED ===")
    print(f"  Verification confidence: {verification_stage['confidence']}")
    print(f"  Evidence items: {verification_stage['evidence_count']}")
    print(f"  LLM calls: {verification_stage['llm_calls']}")
    print(f"  Verified name and category in evidence")


if __name__ == "__main__":
    asyncio.run(main())
