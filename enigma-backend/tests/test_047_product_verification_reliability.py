import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.client import HTTP_TIMEOUT
from app.engine.contracts import ExecutionContext, WorkerStatus
from app.learning.product_verification_curriculum import ProductVerificationTrainingRunner
from app.workers.product_verification import ProductVerificationWorker, settings


def _response(payload):
    return {"choices": [{"message": {"content": json.dumps(payload)}}]}


def _context():
    return ExecutionContext(
        execution_id="task-047-local",
        product={
            "name": "TrailGuard Pro Waterproof Hiking Backpack 35L",
            "description": (
                "A 35-liter forest-green hiking backpack made from ripstop nylon, "
                "with a rain cover, padded straps, hydration sleeve, and bottle pockets."
            ),
            "category": "Sports and Outdoors",
        },
    )


def test_product_verification_timeout_exceeds_provider_read_timeout():
    assert HTTP_TIMEOUT.read == 120.0
    assert ProductVerificationWorker.LLM_TIMEOUT_SECONDS > HTTP_TIMEOUT.read


@pytest.mark.asyncio
async def test_product_verification_uses_configured_8b_model_for_all_subtasks():
    responses = [
        _response({"verified_name": "TrailGuard Pro Backpack 35L", "confidence": 0.9, "issues": []}),
        _response({"category": "Sports", "confidence": 0.9, "evidence": "Hiking product"}),
        _response({"attributes": {"capacity_liters": 35}, "confidence": 0.9}),
    ]
    with patch("app.ai.gateway.gateway.generate", new=AsyncMock(side_effect=responses)) as generate:
        result = await ProductVerificationWorker().run(_context())

    assert result.status == WorkerStatus.SUCCESS
    assert generate.await_count == 3
    assert [call.kwargs["model"] for call in generate.await_args_list] == [
        settings.PRODUCT_VERIFICATION_MODEL,
    ] * 3
    assert [call.kwargs["max_tokens"] for call in generate.await_args_list] == [256, 256, 512]


@pytest.mark.asyncio
async def test_real_worker_output_passes_real_training_evaluator():
    responses = [
        _response({"verified_name": "TrailGuard Pro Backpack 35L", "confidence": 0.92, "issues": []}),
        _response({"category": "Sports", "confidence": 0.90, "evidence": "Hiking product"}),
        _response({"attributes": {"capacity_liters": 35, "material": "ripstop nylon"}, "confidence": 0.88}),
    ]
    with patch("app.ai.gateway.gateway.generate", new=AsyncMock(side_effect=responses)):
        result = await ProductVerificationWorker().run(_context())

    evaluation = ProductVerificationTrainingRunner._evaluate(result.to_dict())
    assert result.confidence == pytest.approx(0.9)
    assert evaluation.passed is True
    assert evaluation.criteria["quality"] == 1.0


@pytest.mark.asyncio
async def test_provider_timeouts_remain_low_quality_and_rejected():
    with patch(
        "app.ai.gateway.gateway.generate",
        new=AsyncMock(side_effect=asyncio.TimeoutError),
    ):
        result = await ProductVerificationWorker().run(_context())

    evaluation = ProductVerificationTrainingRunner._evaluate(result.to_dict())
    assert result.confidence == pytest.approx((0.3 + 0.2 + 0.0) / 3)
    assert evaluation.passed is False
    assert "quality" in evaluation.issues
