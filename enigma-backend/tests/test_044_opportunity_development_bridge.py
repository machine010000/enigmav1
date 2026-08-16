from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.engine.capabilities import capability_registry
from app.freelancing.brain_decision import BrainReadinessEvaluator
from app.freelancing.capability_matcher import CapabilityMatcher
from app.freelancing.contracts import OpportunityRequirements
from app.freelancing.development_bridge import (
    DevelopmentPlan,
    DevelopmentPlanError,
    OpportunityDevelopmentBridge,
    StaleDevelopmentPlanError,
)
from app.learning.curriculum import TrainingMode, TrainingRunResult
from app.learning.observation import ObservationStatus
from app.learning.product_verification_curriculum import ProductVerificationTrainingRunner
from app.learning.promotion_service import CapabilityEvidencePromotionService
from app.models.enigma_profile import CapabilityStatus
from app.routers.enigma_profile import (
    DevelopmentPlanExecutionRequest,
    DevelopmentPlanRequest,
    execute_opportunity_development_plan,
    generate_opportunity_development_plan,
)


def _assessment(capability, confidence, status="practicing", evidence=4):
    assessment = CapabilityMatcher().match(
        OpportunityRequirements(
            opportunity_id="opp-043", required_capabilities=[capability]
        ),
        {capability: {
            "confidence": confidence,
            "evidence_count": evidence,
            "successful_execution_count": evidence,
            "failed_execution_count": 0,
            "capability_status": status,
        }},
    )
    return assessment, BrainReadinessEvaluator().evaluate(assessment)


def _progress(confidence=0.4003, status="practicing", evidence=4):
    return SimpleNamespace(
        confidence=confidence, capability_status=status, evidence_count=evidence,
        freshness="fresh",
    )


def _db(*values):
    db = AsyncMock()
    db.scalar = AsyncMock(side_effect=list(values))
    return db


@pytest.mark.asyncio
async def test_task043_gap_creates_only_product_verification_plan():
    capability_registry.register_worker_capabilities(
        "product_verification", ["product_verification"]
    )
    assessment, decision = _assessment("product_verification", 0.4003)
    product = SimpleNamespace(id="owned-product", user_id="user-a")
    bridge = OpportunityDevelopmentBridge()

    plans = await bridge.generate(
        assessment=assessment, decision=decision,
        db=_db(_progress(), product), user_id="user-a", target_id="owned-product",
    )

    assert len(plans) == 1
    plan = plans[0]
    assert plan.capability_id == "product_verification"
    assert plan.current_confidence == 0.4003
    assert plan.required_threshold == 0.65
    assert plan.recommended_training_mode == TrainingMode.QUALIFICATION.value
    assert plan.execution_available and plan.state == "executable"


@pytest.mark.asyncio
async def test_ready_keyword_opportunity_produces_no_plan():
    assessment, decision = _assessment(
        "keyword_research", 0.8456, status="proven", evidence=28
    )
    plans = await OpportunityDevelopmentBridge().generate(
        assessment=assessment, decision=decision,
        db=_db(), user_id="user-a",
    )
    assert plans == []


@pytest.mark.asyncio
async def test_non_executable_gap_is_explicitly_blocked():
    assessment, decision = _assessment("seo_analysis", 0.0, status="unknown", evidence=0)
    plans = await OpportunityDevelopmentBridge().generate(
        assessment=assessment, decision=decision,
        db=_db(_progress(0.0, "unknown", 0)), user_id="user-a",
    )
    assert len(plans) == 1
    assert plans[0].state == "blocked"
    assert not plans[0].execution_available
    assert plans[0].recommended_training_mode is None


@pytest.mark.asyncio
async def test_product_target_must_be_owned_by_authenticated_user():
    capability_registry.register_worker_capabilities(
        "product_verification", ["product_verification"]
    )
    assessment, decision = _assessment("product_verification", 0.4003)
    with pytest.raises(DevelopmentPlanError, match="owned target"):
        await OpportunityDevelopmentBridge().generate(
            assessment=assessment, decision=decision,
            db=_db(_progress(), None), user_id="user-b", target_id="user-a-product",
        )


class _FakeRunner:
    async def run_next(self, db, user_id, mode=None):
        return TrainingRunResult(
            action="advance", execution_id="execution-1", attempts_run=1
        )


class _FakeRegistry:
    def __init__(self):
        self.kwargs = None

    def resolve(self, capability_id, **kwargs):
        self.kwargs = {"capability_id": capability_id, **kwargs}
        return _FakeRunner()


@pytest.mark.asyncio
async def test_plan_hands_off_to_existing_runner_registry():
    registry = _FakeRegistry()
    bridge = OpportunityDevelopmentBridge(runners=registry)
    plan = DevelopmentPlan(
        plan_id="dev-one", opportunity_id="opp-043",
        capability_id="product_verification", reason="gap",
        current_status="practicing", current_confidence=0.4003,
        evidence_count=4, required_threshold=0.65,
        execution_available=True,
        recommended_training_mode=TrainingMode.QUALIFICATION.value,
        state="executable", current_freshness="fresh",
        target_id="owned-product", readiness_gap=0.2497,
    )
    result = await bridge.execute(
        plan, db=_db(SimpleNamespace(id="owned-product"), _progress()),
        user_id="user-a",
    )
    assert result.execution_id == "execution-1"
    assert registry.kwargs["capability_id"] == "product_verification"
    assert registry.kwargs["plan_id"] == "dev-one"


@pytest.mark.asyncio
async def test_stale_plan_is_rejected_before_runner_execution():
    plan = DevelopmentPlan(
        plan_id="dev-stale", opportunity_id="opp-043",
        capability_id="product_verification", reason="gap",
        current_status="practicing", current_confidence=0.4003,
        evidence_count=4, required_threshold=0.65,
        execution_available=True,
        recommended_training_mode=TrainingMode.QUALIFICATION.value,
        state="executable", current_freshness="fresh", target_id="owned-product",
    )
    with pytest.raises(StaleDevelopmentPlanError):
        await OpportunityDevelopmentBridge().execute(
            plan, db=_db(SimpleNamespace(id="owned-product"), _progress(0.5)),
            user_id="user-a",
        )


@pytest.mark.asyncio
async def test_same_plan_replay_returns_prior_execution_without_rerun():
    record = SimpleNamespace(
        id="existing-execution",
        result={"_training": {"development_plan_id": "dev-replay"}},
    )
    scalars = MagicMock()
    scalars.all.return_value = [record]
    db = AsyncMock()
    db.scalars = AsyncMock(return_value=scalars)
    db.scalar = AsyncMock(return_value=_progress())
    runner = ProductVerificationTrainingRunner(
        target_id="owned-product", plan_id="dev-replay"
    )
    result = await runner.run_next(db, "user-a")
    assert result.action == "already_executed"
    assert result.execution_id == "existing-execution"
    assert result.attempts_run == 0


def test_failed_product_result_cannot_pass_training_evaluation():
    evaluation = ProductVerificationTrainingRunner._evaluate({
        "status": "failed", "confidence": 0.0, "result": {}, "evidence": [],
    })
    assert not evaluation.passed
    assert evaluation.score == 0.0
    eligibility, decision, _ = CapabilityEvidencePromotionService._decide(
        owner_id="user-a", status=ObservationStatus.FAILURE,
        training_mode=TrainingMode.QUALIFICATION.value,
        evaluation=evaluation.to_dict(),
    )
    assert eligibility == "ineligible"
    assert decision == "rejected"


@pytest.mark.asyncio
async def test_product_runner_handoff_uses_existing_evidence_and_promotion_pipeline(monkeypatch):
    payload = {
        "status": "success",
        "result": {
            "verified_name": "Controlled Product",
            "category": "Home",
        },
        "evidence": [{"field": "verified_name"}],
        "confidence": 0.9,
        "llm_calls": 1,
    }
    mapper = SimpleNamespace(persist_observation=AsyncMock(return_value={}))
    brain = SimpleNamespace(
        execute_decision=AsyncMock(return_value={
            "execution_id": "execution-new",
            "worker_name": "product_verification",
            "result": payload,
        }),
        evidence_mapper=mapper,
    )
    promotion = SimpleNamespace(submit=AsyncMock())
    record = SimpleNamespace(result={})
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=record)
    runner = ProductVerificationTrainingRunner(
        target_id="owned-product", plan_id="dev-new",
        brain=brain, promotion_service=promotion,
    )
    monkeypatch.setattr(runner, "_status", AsyncMock(return_value="practicing"))
    monkeypatch.setattr(runner, "_replay", AsyncMock(return_value=None))

    result = await runner.run_next(db, "user-a")

    assert result.action == "advance"
    assert result.execution_id == "execution-new"
    mapper.persist_observation.assert_awaited_once()
    assert promotion.submit.await_args.kwargs["training_mode"] == (
        TrainingMode.QUALIFICATION.value
    )
    assert promotion.submit.await_args.kwargs["evaluation"].passed
    assert record.result["_training"]["development_plan_id"] == "dev-new"


@pytest.mark.asyncio
async def test_pre_persistence_execution_failure_never_reaches_promotion(monkeypatch):
    mapper = SimpleNamespace(persist_observation=AsyncMock())
    brain = SimpleNamespace(
        execute_decision=AsyncMock(return_value={
            "status": "failed", "reason": "Execution failed"
        }),
        evidence_mapper=mapper,
    )
    promotion = SimpleNamespace(submit=AsyncMock())
    runner = ProductVerificationTrainingRunner(
        target_id="owned-product", plan_id="dev-failed",
        brain=brain, promotion_service=promotion,
    )
    monkeypatch.setattr(runner, "_status", AsyncMock(return_value="practicing"))
    monkeypatch.setattr(runner, "_replay", AsyncMock(return_value=None))

    result = await runner.run_next(AsyncMock(), "user-a")

    assert result.action == "retry"
    assert not result.evaluation.passed
    mapper.persist_observation.assert_not_awaited()
    promotion.submit.assert_not_awaited()


@pytest.mark.parametrize("status,expected", [
    (CapabilityStatus.UNKNOWN.value, TrainingMode.QUALIFICATION),
    (CapabilityStatus.LEARNING.value, TrainingMode.QUALIFICATION),
    (CapabilityStatus.PRACTICING.value, TrainingMode.QUALIFICATION),
    (CapabilityStatus.QUALIFIED.value, TrainingMode.ADVANCED),
])
def test_training_mode_policy_uses_existing_lifecycle(status, expected):
    assert OpportunityDevelopmentBridge._training_mode(status, "fresh") == expected


def test_proven_fresh_capability_gets_no_unnecessary_mode():
    assert OpportunityDevelopmentBridge._training_mode("proven", "fresh") is None
    assert OpportunityDevelopmentBridge._training_mode(
        "proven", "stale"
    ) == TrainingMode.REVALIDATION


def _plan_request(request_type=DevelopmentPlanRequest, **extra):
    return request_type(
        opportunity_id="opp-043",
        title="E-commerce Product Catalog Verification and Metadata QA",
        description="Verify product names, categories, and catalog metadata.",
        platform="controlled_internal",
        required_skills=["Product Verification"],
        target_id="owned-product",
        **extra,
    )


@pytest.mark.asyncio
async def test_plan_endpoint_reassesses_but_does_not_execute(monkeypatch):
    assessment, decision = _assessment("product_verification", 0.4003)
    plan = DevelopmentPlan(
        plan_id="dev-api", opportunity_id="opp-043",
        capability_id="product_verification", reason="gap",
        current_status="practicing", current_confidence=0.4003,
        evidence_count=4, required_threshold=0.65,
        execution_available=True,
        recommended_training_mode=TrainingMode.QUALIFICATION.value,
        state="executable", current_freshness="fresh", target_id="owned-product",
    )
    from app.routers import enigma_profile as router_module
    monkeypatch.setattr(
        router_module._assessment_service, "assess",
        AsyncMock(return_value=(MagicMock(), assessment, decision)),
    )
    generate = AsyncMock(return_value=[plan])
    execute = AsyncMock()
    monkeypatch.setattr(router_module._development_bridge, "generate", generate)
    monkeypatch.setattr(router_module._development_bridge, "execute", execute)

    response = await generate_opportunity_development_plan(
        _plan_request(), current_user=SimpleNamespace(id="user-a"), db=AsyncMock()
    )

    assert response["development_actions"][0]["plan_id"] == "dev-api"
    execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_endpoint_regenerates_plan_before_one_handoff(monkeypatch):
    assessment, decision = _assessment("product_verification", 0.4003)
    plan = DevelopmentPlan(
        plan_id="dev-api", opportunity_id="opp-043",
        capability_id="product_verification", reason="gap",
        current_status="practicing", current_confidence=0.4003,
        evidence_count=4, required_threshold=0.65,
        execution_available=True,
        recommended_training_mode=TrainingMode.QUALIFICATION.value,
        state="executable", current_freshness="fresh", target_id="owned-product",
    )
    from app.routers import enigma_profile as router_module
    monkeypatch.setattr(
        router_module._assessment_service, "assess",
        AsyncMock(return_value=(MagicMock(), assessment, decision)),
    )
    generate = AsyncMock(return_value=[plan])
    execute = AsyncMock(return_value=TrainingRunResult(
        action="advance", execution_id="exec-one", attempts_run=1
    ))
    monkeypatch.setattr(router_module._development_bridge, "generate", generate)
    monkeypatch.setattr(router_module._development_bridge, "execute", execute)

    response = await execute_opportunity_development_plan(
        _plan_request(DevelopmentPlanExecutionRequest, plan_id="dev-api"),
        current_user=SimpleNamespace(id="user-a"), db=AsyncMock(),
    )

    assert response["execution_id"] == "exec-one"
    assert generate.await_count == 1
    assert execute.await_count == 1
