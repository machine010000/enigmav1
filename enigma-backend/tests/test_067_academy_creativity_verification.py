from unittest.mock import AsyncMock, Mock

import pytest

from app.academy.learning_service import AcademyLearningService
from app.ai.master_brain.orchestrator import MasterBrain
from app.creativity.ai_service import CreativityAIService
from app.creativity.engine import CreativityEngine
from app.engine.capabilities import capability_registry
from app.engine.contracts import WorkerResult, WorkerStatus
from app.engine.registry import register_all
from app.services.product_verification_gate import (
    ProductVerificationGate,
    VerificationStage,
)


@pytest.mark.asyncio
async def test_creativity_uses_gateway_and_returns_structured_result():
    gateway = Mock()
    gateway.generate = AsyncMock(return_value={
        "ideas": [{"title": "Pilot", "approach": "small milestone", "benefit": "lower risk"}],
        "alternative_approaches": ["discovery first"],
        "proposal_angles": ["fast validated outcome"],
        "risks": ["unclear scope"], "confidence": 0.82, "rationale": "Context grounded",
    })
    engine = CreativityEngine(ai_service=CreativityAIService(gateway))
    result = await engine.generate_for_task(task="Draft proposal", project_context={"budget": 500})
    assert result.ideas[0]["title"] == "Pilot"
    assert result.proposal_angles == ["fast validated outcome"]
    assert result.confidence == 0.82
    gateway.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_academy_uses_gateway_and_existing_governance_path():
    gateway = Mock()
    gateway.generate = AsyncMock(return_value={
        "knowledge_summary": "Validate inputs before implementation.",
        "execution_checklist": ["Confirm requirements", "Test safely"],
        "risks_common_mistakes": ["Assuming missing facts"],
        "recommended_skills_tools": ["API documentation"],
        "sources": [], "confidence": 0.78,
    })
    governance = Mock()
    governance.submit_candidate.return_value.concept.id = "knowledge-1"
    material = await AcademyLearningService(gateway, governance).learn(
        topic="API integration", task="Build adapter", capability_gap="api_contracts"
    )
    assert material.knowledge_id == "knowledge-1"
    assert material.execution_checklist == ["Confirm requirements", "Test safely"]
    governance.submit_candidate.assert_called_once()


def test_brain_can_route_academy_through_capability_registry():
    register_all()
    decision = MasterBrain().decide_capability(
        "Create training material for this capability gap",
        {"topic": "OAuth", "capability_gap": "oauth_security", "task": "Integrate safely"},
    )
    assert capability_registry.resolve_capability("academy_learning") is not None
    assert decision.capability == "academy_learning"
    assert decision.execution_input["topic"] == "OAuth"


def test_product_verification_gate_blocks_review_and_allows_pass():
    gate = ProductVerificationGate()
    review = WorkerResult(
        worker_name="product_verification", status=WorkerStatus.SUCCESS,
        result={"recommendation": "review", "confidence": 0.7, "risks": ["uncertain claim"],
                "missing_information": ["evidence"], "evidence_context": []},
    )
    decision = gate.evaluate(review, VerificationStage.PROPOSAL_SUBMISSION)
    assert decision.allowed is False
    assert decision.missing_information == ["evidence"]

    passed = WorkerResult(
        worker_name="product_verification", status=WorkerStatus.SUCCESS,
        result={"recommendation": "pass", "confidence": 0.94, "risks": [],
                "missing_information": [], "evidence_context": [{"source": "test"}]},
    )
    delivery = gate.evaluate(passed, VerificationStage.FINAL_DELIVERY)
    assert delivery.allowed is True
    assert delivery.to_dict()["stage"] == "final_delivery"
