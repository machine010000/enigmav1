from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus
from app.engine.engine import engine

CONFIDENCE_THRESHOLD = 0.7

PIPELINE_STAGES = [
    {"step": 1, "worker": "product_verification", "name": "Product Verification", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 2, "worker": "product_research", "name": "Product Research", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 3, "worker": "audience_discovery", "name": "Audience Discovery", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 4, "worker": "keyword_discovery", "name": "Keyword Discovery", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 5, "worker": "competitor_discovery", "name": "Competitor Discovery", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 6, "worker": "trend_discovery", "name": "Trend Discovery", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 7, "worker": "community_discovery", "name": "Community Discovery", "min_confidence": CONFIDENCE_THRESHOLD},
    {"step": 8, "worker": "intelligence_report", "name": "Product Intelligence Report", "min_confidence": CONFIDENCE_THRESHOLD},
]

async def run_product_intelligence_pipeline(context: ExecutionContext, db: Optional[Any] = None, save: bool = True) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    pipeline_id = context.execution_id or str(__import__("uuid").uuid4())
    context.execution_id = pipeline_id

    for stage in PIPELINE_STAGES:
        worker_name = stage["worker"]
        stage_name = stage["name"]
        min_confidence: float = stage["min_confidence"]  # type: ignore[assignment]

        if worker_name not in engine.registered_names:
            results.append({"step": stage["step"], "stage": stage_name, "worker": worker_name, "status": "skipped", "error": "Worker not registered"})
            continue

        result = await engine.execute(worker_name, context, save=save, db=db)

        stage_result = {
            "step": stage["step"],
            "stage": stage_name,
            "worker": worker_name,
            "status": result.status.value,
            "confidence": result.confidence,
            "execution_time": result.execution_time,
            "evidence_count": len(result.evidence),
            "llm_calls": result.llm_calls,
            "error": result.error,
        }
        results.append(stage_result)

        if result.status == WorkerStatus.FAILED:
            break
        if result.confidence < float(min_confidence) and not (result.metadata and result.metadata.get("needs_review")):
            break

    final_confidence = results[-1]["confidence"] if results else 0.0
    all_success = all(r["status"] == "success" for r in results)

    return {
        "pipeline_id": pipeline_id,
        "stages": results,
        "total_stages": len(PIPELINE_STAGES),
        "completed_stages": len(results),
        "all_success": all_success,
        "final_confidence": final_confidence,
        "status": "success" if all_success and final_confidence >= CONFIDENCE_THRESHOLD else "incomplete",
    }
