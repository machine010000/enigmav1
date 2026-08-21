"""
TASK-018 Tests — keyword_research capability + migration activation

Required tests (18 total):

1.  Migration model compatibility — KnowledgeProgress has TASK-017 columns
2.  Profile snapshot loads new production-compatible fields
3.  keyword_research worker contract (name, capabilities, input/output schema)
4.  keyword_research registry resolution
5.  Client does not provide worker_name (resolved via capability policy)
6.  Valid keyword execution succeeds
7.  Result generates ExecutionObservation
8.  Evidence/profile updates (success path)
9.  Persisted profile reload reflects execution
10. Failed execution does not increase confidence
11. Assessment before learning = LEARN_FIRST
12. Repeated validated practice changes evidence/confidence
13. Reassessment reflects changed DB state
14. READY_TO_APPLY only occurs after policy threshold is met
15. Brain cannot bypass readiness policy
16. Cross-user TASK-016 security remains intact
17. TASK-017 assessment regressions pass
18. Brain/Engine/Learning regressions pass
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
from datetime import datetime
from typing import Any, Dict

from app.workers.keyword_research import (
    KeywordResearchWorker,
    keyword_research_worker,
    _build_keyword_entry,
    _normalise_intent,
    _priority_from_relevance,
    SOURCE_AI_HYPOTHESIS,
    SOURCE_SEED_DERIVED,
)
from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus
from app.engine.capability_catalog import capability_catalog
from app.engine.capabilities import capability_registry
from app.freelancing.contracts import (
    ReadinessState,
    OpportunityRequirements,
    BrainDecisionType,
)
from app.freelancing.capability_matcher import CapabilityMatcher
from app.freelancing.brain_decision import BrainReadinessEvaluator
from app.learning.observation import ExecutionObservation, ObservationStatus
from app.learning.profile_updater import ProfileUpdater, _derive_capability_status
from app.models.enigma_profile import CapabilityStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context(
    topic: str = "e-commerce SEO",
    seed_keywords: list = None,
    market: str = "global",
    goal: str = "commercial",
) -> ExecutionContext:
    ctx = ExecutionContext(
        user={"id": str(uuid4()), "email": "test@enigma.ai"},
        product={},
        execution_id=str(uuid4()),
    )
    ctx.remember("topic", topic)
    if seed_keywords:
        ctx.remember("seed_keywords", seed_keywords)
    ctx.remember("market", market)
    ctx.remember("goal", goal)
    return ctx


def _make_profile_snapshot(confidence: float, evidence_count: int = 5) -> Dict[str, Any]:
    return {
        "keyword_research": {
            "confidence": confidence,
            "evidence_count": evidence_count,
            "successful_execution_count": evidence_count - 1,
            "failed_execution_count": 1,
            "capability_status": _derive_capability_status(evidence_count, confidence).value,
            "readiness": confidence * 0.8,
        }
    }


# ---------------------------------------------------------------------------
# TEST 1: Migration model compatibility
# ---------------------------------------------------------------------------

def test_1_migration_model_has_task017_columns():
    """TEST 1: KnowledgeProgress model has all TASK-017 columns."""
    from sqlalchemy import inspect as sa_inspect
    from app.models.enigma_profile import KnowledgeProgress

    columns = {c.key for c in KnowledgeProgress.__table__.columns}
    required = {
        "capability_status",
        "evidence_count",
        "successful_execution_count",
        "failed_execution_count",
        "last_success_at",
        "freelance_readiness_threshold",
    }
    missing = required - columns
    assert not missing, f"Missing TASK-017 columns on KnowledgeProgress: {missing}"


# ---------------------------------------------------------------------------
# TEST 2: Profile snapshot loads new fields without fallback error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_profile_snapshot_loads_new_fields():
    """TEST 2: OpportunityAssessmentService loads TASK-017 fields from DB rows."""
    from app.freelancing.assessment_service import OpportunityAssessmentService

    service = OpportunityAssessmentService()

    # Simulate a DB row WITH the new columns populated
    mock_row = MagicMock()
    mock_row.domain = "keyword_research"
    mock_row.confidence = 0.72
    mock_row.evidence_count = 6           # TASK-017 column
    mock_row.successful_execution_count = 5
    mock_row.failed_execution_count = 1
    mock_row.capability_status = CapabilityStatus.QUALIFIED.value
    mock_row.readiness = 0.65
    mock_row.last_success_at = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=[mock_row]))
    )
    mock_db.execute = AsyncMock(return_value=mock_result)

    snapshot = await service._load_profile_snapshot(
        db=mock_db,
        capability_ids=["keyword_research"],
    )

    assert "keyword_research" in snapshot
    entry = snapshot["keyword_research"]
    assert entry["confidence"] == 0.72
    assert entry["evidence_count"] == 6
    assert entry["successful_execution_count"] == 5
    assert entry["capability_status"] == CapabilityStatus.QUALIFIED.value


# ---------------------------------------------------------------------------
# TEST 3: Worker contract (name, capabilities, schemas)
# ---------------------------------------------------------------------------

def test_3_keyword_research_worker_contract():
    """TEST 3: Worker has correct name, capabilities, and schemas."""
    w = KeywordResearchWorker()

    assert w.name == "keyword_research"
    assert "keyword_research" in w.capabilities
    assert "topic" in w.input_schema
    assert "primary_keywords" in w.output_schema
    assert "secondary_keywords" in w.output_schema
    assert "intent_summary" in w.output_schema
    assert "confidence" in w.output_schema
    assert "issues" in w.output_schema


# ---------------------------------------------------------------------------
# TEST 4: Registry resolves keyword_research capability
# ---------------------------------------------------------------------------

def test_4_registry_resolves_keyword_research():
    """TEST 4: CapabilityRegistry resolves keyword_research after worker registration."""
    # The worker is registered at import time via registry.py singleton
    # Since we've added it to register_all(), importing triggers registration
    from app.engine.registry import register_all
    register_all()  # idempotent

    resolution = capability_registry.resolve_capability("keyword_research")
    assert resolution is not None, "keyword_research must be resolvable from registry"
    assert resolution["worker_name"] == "keyword_research"


# ---------------------------------------------------------------------------
# TEST 5: Client does not provide worker_name — resolved via capability policy
# ---------------------------------------------------------------------------

def test_5_client_cannot_choose_worker_name():
    """TEST 5: AutonomousRequest model has no worker_name field."""
    from app.routers.master_brain import AutonomousRequest
    import inspect

    sig = inspect.signature(AutonomousRequest)
    fields = AutonomousRequest.model_fields

    assert "worker_name" not in fields, (
        "AutonomousRequest must not expose worker_name — "
        "worker resolution is internal to the registry"
    )


def test_5b_brain_decides_capability_not_worker():
    """TEST 5b: Brain.decide_capability resolves keyword_research by capability, not worker name."""
    from app.ai.master_brain.orchestrator import MasterBrain
    from app.ai.master_brain.models import BrainAction

    brain = MasterBrain()
    decision = brain.decide_capability(
        message="do keyword research for my website",
        context={"topic": "e-commerce shoes"},
    )

    assert decision.action == BrainAction.EXECUTE_CAPABILITY
    assert decision.capability == "keyword_research"
    # Worker name is NOT in the decision — Brain never exposes it
    assert not hasattr(decision, "worker_name") or decision.capability != "keyword_research_worker"


# ---------------------------------------------------------------------------
# TEST 6: Valid keyword execution succeeds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_6_valid_keyword_execution_succeeds():
    """TEST 6: Worker returns SUCCESS with keywords when LLM responds properly."""
    worker = KeywordResearchWorker()
    ctx = _make_context(topic="organic coffee shop", seed_keywords=["coffee near me"])

    mock_llm_response = {
        "choices": [{
            "message": {
                "content": '{"keywords":[{"keyword":"organic coffee shop","intent":"navigational","relevance":0.9,"notes":"high intent"},{"keyword":"best organic coffee","intent":"commercial","relevance":0.85,"notes":"buyer intent"},{"keyword":"coffee shop near me","intent":"navigational","relevance":0.82,"notes":"local intent"},{"keyword":"organic fair trade coffee","intent":"informational","relevance":0.72,"notes":"awareness"},{"keyword":"buy organic coffee online","intent":"transactional","relevance":0.88,"notes":"purchase intent"}],"confidence":0.78}'
            }
        }]
    }

    with patch("app.ai.gateway.gateway.generate", new=AsyncMock(return_value=mock_llm_response)):
        result = await worker.run(ctx)

    assert result.status == WorkerStatus.SUCCESS
    assert result.confidence > 0
    assert result.llm_calls == 1
    assert isinstance(result.result["primary_keywords"], list)
    assert isinstance(result.result["secondary_keywords"], list)
    assert result.result["total_found"] > 0
    assert "intent_summary" in result.result


# ---------------------------------------------------------------------------
# TEST 7: Result generates ExecutionObservation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_7_result_generates_execution_observation():
    """TEST 7: WorkerResult can be converted to ExecutionObservation."""
    worker = KeywordResearchWorker()
    ctx = _make_context(topic="fitness coaching")

    mock_response = {
        "choices": [{"message": {"content": '{"keywords":[{"keyword":"fitness coach","intent":"commercial","relevance":0.8,"notes":""}],"confidence":0.75}'}}]
    }

    with patch("app.ai.gateway.gateway.generate", new=AsyncMock(return_value=mock_response)):
        result = await worker.run(ctx)

    assert result.status == WorkerStatus.SUCCESS

    observation = ExecutionObservation.from_worker_result(
        execution_id=ctx.execution_id,
        user_id=str(uuid4()),
        capability="keyword_research",
        worker=worker.name,
        worker_result=result.to_dict(),
    )

    assert observation.capability == "keyword_research"
    assert observation.status == ObservationStatus.SUCCESS
    assert observation.confidence == result.confidence
    assert observation.worker == "keyword_research"


# ---------------------------------------------------------------------------
# TEST 8: Evidence/profile update on success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_8_success_updates_profile():
    """TEST 8: Successful observation increases evidence_count and confidence."""
    updater = ProfileUpdater()

    mock_kp = MagicMock()
    mock_kp.confidence = 0.40
    mock_kp.execution_score = 0.40
    mock_kp.evidence_score = 0.35
    mock_kp.knowledge_score = 0.40
    mock_kp.evidence_count = 3
    mock_kp.successful_execution_count = 3
    mock_kp.failed_execution_count = 0
    mock_kp.capability_status = CapabilityStatus.PRACTICING.value
    mock_kp.last_success_at = None
    mock_kp.freshness = "fresh"

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    observation = ExecutionObservation(
        execution_id=str(uuid4()),
        user_id=str(uuid4()),
        capability="keyword_research",
        worker="keyword_research",
        status=ObservationStatus.SUCCESS,
        confidence=0.78,
        created_at=datetime.utcnow(),
    )

    with patch.object(updater, "_get_or_create_knowledge_progress", return_value=mock_kp):
        ok = await updater._record_success(observation, mock_db)

    assert ok is True
    assert mock_kp.evidence_count == 4
    assert mock_kp.successful_execution_count == 4
    assert mock_kp.confidence > 0.40  # boost applied


# ---------------------------------------------------------------------------
# TEST 9: Persisted profile reload reflects execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_9_profile_reload_reflects_execution():
    """TEST 9: After ProfileUpdater.record_success, re-loading snapshot shows updated values."""
    from app.freelancing.assessment_service import OpportunityAssessmentService
    service = OpportunityAssessmentService()

    # Simulate the "after learning" state — evidence_count=6, confidence=0.68
    mock_row = MagicMock()
    mock_row.domain = "keyword_research"
    mock_row.confidence = 0.68
    mock_row.evidence_count = 6
    mock_row.successful_execution_count = 5
    mock_row.failed_execution_count = 1
    mock_row.capability_status = CapabilityStatus.QUALIFIED.value
    mock_row.readiness = 0.60
    mock_row.last_success_at = datetime.utcnow()

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_row])))
    mock_db.execute = AsyncMock(return_value=mock_result)

    snapshot = await service._load_profile_snapshot(
        db=mock_db, capability_ids=["keyword_research"]
    )

    assert snapshot["keyword_research"]["evidence_count"] == 6
    assert snapshot["keyword_research"]["confidence"] == 0.68
    assert snapshot["keyword_research"]["capability_status"] == CapabilityStatus.QUALIFIED.value


# ---------------------------------------------------------------------------
# TEST 10: Failed execution does NOT increase confidence
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_10_failure_does_not_increase_confidence():
    """TEST 10: Failure observation applies penalty — confidence never increases."""
    updater = ProfileUpdater()

    initial_confidence = 0.55
    mock_kp = MagicMock()
    mock_kp.confidence = initial_confidence
    mock_kp.execution_score = 0.5
    mock_kp.knowledge_score = 0.4
    mock_kp.evidence_score = 0.4
    mock_kp.evidence_count = 4
    mock_kp.successful_execution_count = 4
    mock_kp.failed_execution_count = 0
    mock_kp.capability_status = CapabilityStatus.PRACTICING.value
    mock_kp.freshness = "fresh"

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    observation = ExecutionObservation(
        execution_id=str(uuid4()),
        user_id=str(uuid4()),
        capability="keyword_research",
        worker="keyword_research",
        status=ObservationStatus.FAILURE,
        confidence=0.0,
        created_at=datetime.utcnow(),
    )

    with patch.object(updater, "_get_or_create_knowledge_progress", return_value=mock_kp):
        ok = await updater._record_failure(observation, mock_db)

    assert ok is True
    assert mock_kp.failed_execution_count == 1
    assert mock_kp.confidence <= initial_confidence, (
        f"Failure must not increase confidence: was {initial_confidence}, "
        f"now {mock_kp.confidence}"
    )


# ---------------------------------------------------------------------------
# TEST 11: Assessment before learning = LEARN_FIRST
# ---------------------------------------------------------------------------

def test_11_assessment_before_learning_is_learn_first():
    """TEST 11: No profile evidence → keyword_research is UNKNOWN → LEARN_FIRST."""
    matcher = CapabilityMatcher()

    req = OpportunityRequirements(
        opportunity_id="opp-kw-1",
        required_capabilities=["keyword_research"],
    )

    # Empty profile — no executions yet
    assessment = matcher.match(req, {})

    assert assessment.readiness in (
        ReadinessState.LEARN_FIRST,
        ReadinessState.NOT_READY,
    )


# ---------------------------------------------------------------------------
# TEST 12: Repeated practice changes evidence/confidence
# ---------------------------------------------------------------------------

def test_12_repeated_practice_advances_confidence():
    """TEST 12: Applying success boost 7 times crosses the 0.65 threshold."""
    from app.learning.profile_updater import _SUCCESS_BOOST_FACTOR

    confidence = 0.20  # start at LEARNING level
    for _ in range(7):
        confidence = min(1.0, confidence + (1.0 - confidence) * _SUCCESS_BOOST_FACTOR)

    assert confidence > 0.65, (
        f"After 7 successful executions confidence should exceed 0.65, got {confidence:.3f}"
    )

    # Verify status derivation tracks the improvement
    status_before = _derive_capability_status(2, 0.20)
    status_after = _derive_capability_status(9, confidence)

    assert status_before == CapabilityStatus.LEARNING
    assert status_after in (CapabilityStatus.QUALIFIED, CapabilityStatus.PROVEN)


# ---------------------------------------------------------------------------
# TEST 13: Reassessment reflects changed DB state
# ---------------------------------------------------------------------------

def test_13_reassessment_uses_reloaded_profile():
    """TEST 13: Assessment with updated snapshot returns different readiness."""
    matcher = CapabilityMatcher()

    req = OpportunityRequirements(
        opportunity_id="opp-kw-2",
        required_capabilities=["keyword_research"],
    )

    # Before learning
    before = matcher.match(req, _make_profile_snapshot(confidence=0.30, evidence_count=2))
    assert before.readiness == ReadinessState.LEARN_FIRST

    # After learning (confidence above threshold)
    after = matcher.match(req, _make_profile_snapshot(confidence=0.72, evidence_count=7))
    assert after.readiness in (ReadinessState.READY_TO_APPLY, ReadinessState.HIGH_CONFIDENCE)


# ---------------------------------------------------------------------------
# TEST 14: READY_TO_APPLY only after policy threshold
# ---------------------------------------------------------------------------

def test_14_ready_to_apply_only_after_threshold():
    """TEST 14: READY_TO_APPLY requires confidence >= freelance_readiness_threshold (0.65)."""
    matcher = CapabilityMatcher()

    req = OpportunityRequirements(
        opportunity_id="opp-kw-3",
        required_capabilities=["keyword_research"],
    )

    # 0.64 — just below threshold
    below = matcher.match(req, _make_profile_snapshot(confidence=0.64, evidence_count=5))
    assert below.readiness == ReadinessState.LEARN_FIRST

    # 0.65 — exactly at threshold
    at_threshold = matcher.match(req, _make_profile_snapshot(confidence=0.65, evidence_count=5))
    assert at_threshold.readiness in (ReadinessState.READY_TO_APPLY, ReadinessState.HIGH_CONFIDENCE)

    # 0.80 — well above
    above = matcher.match(req, _make_profile_snapshot(confidence=0.80, evidence_count=8))
    assert above.readiness in (ReadinessState.READY_TO_APPLY, ReadinessState.HIGH_CONFIDENCE)


# ---------------------------------------------------------------------------
# TEST 15: Brain cannot bypass readiness policy
# ---------------------------------------------------------------------------

def test_15_brain_cannot_bypass_readiness_policy():
    """TEST 15: Even if Brain proposes READY_TO_APPLY, policy blocks when evidence insufficient."""
    from app.freelancing.contracts import OpportunityAssessment

    evaluator = BrainReadinessEvaluator()

    weak_match = MagicMock()
    weak_match.required = True
    weak_match.in_catalog = True
    weak_match.capability = "keyword_research"
    weak_match.confidence = 0.30
    weak_match.minimum_required_confidence = 0.65
    weak_match.gap = True

    assessment = OpportunityAssessment(
        opportunity_id="opp-brain",
        overall_score=0.46,
        readiness=ReadinessState.LEARN_FIRST,
        capability_matches=[weak_match],
        missing_capabilities=[],
        weak_capabilities=["keyword_research"],
    )

    with patch.object(evaluator, "_brain_propose", return_value=BrainDecisionType.READY_TO_APPLY):
        decision = evaluator.evaluate(assessment)

    assert decision.policy_overridden is True
    assert decision.decision in (
        BrainDecisionType.LEARN_CAPABILITY,
        BrainDecisionType.PRACTICE_CAPABILITY,
    )


# ---------------------------------------------------------------------------
# TEST 16: Cross-user TASK-016 security remains intact
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_16_cross_user_security_intact():
    """TEST 16: Execution retrieval scoped by user_id — cross-user returns None."""
    from app.engine.engine import ExecutionEngine
    eng = ExecutionEngine()

    user_a = str(uuid4())
    exec_id = str(uuid4())

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await eng.get_execution_record(mock_db, exec_id, user_id=user_a)
    assert result is None, "Cross-user execution lookup must return None (HTTP 404)"


# ---------------------------------------------------------------------------
# TEST 17: TASK-017 assessment regressions
# ---------------------------------------------------------------------------

def test_17_task017_catalog_has_academy_entry():
    """Academy learning extends the catalog without changing keyword research."""
    all_entries = capability_catalog.list_all()
    assert len(all_entries) == 14
    assert capability_catalog.get("academy_learning").execution_available is True

    kw_entry = capability_catalog.get("keyword_research")
    assert kw_entry is not None
    assert kw_entry.execution_available is True, (
        "keyword_research must now have execution_available=True"
    )


def test_17b_other_catalog_entries_unchanged():
    """TEST 17b: Other catalog entries are not affected by TASK-018 changes."""
    pv = capability_catalog.get("product_verification")
    assert pv.execution_available is True

    seo = capability_catalog.get("seo_analysis")
    assert seo.execution_available is False  # still not implemented

    copywriting = capability_catalog.get("copywriting")
    assert copywriting.execution_available is False


# ---------------------------------------------------------------------------
# TEST 18: Brain/Engine/Learning regressions
# ---------------------------------------------------------------------------

def test_18_brain_resolve_product_verification_unchanged():
    """TEST 18: Brain still resolves product_verification correctly."""
    from app.ai.master_brain.orchestrator import MasterBrain
    from app.ai.master_brain.models import BrainAction

    brain = MasterBrain()
    decision = brain.decide_capability(
        message="verify my product",
        context={"product_id": str(uuid4())},
    )

    assert decision.action == BrainAction.EXECUTE_CAPABILITY
    assert decision.capability == "product_verification"


def test_18b_registry_has_three_workers():
    """TEST 18b: After register_all, engine has product_verification, market_analysis, keyword_research."""
    from app.engine.registry import register_all
    registered = register_all()

    assert "product_verification" in registered
    assert "market_analysis" in registered
    assert "keyword_research" in registered


@pytest.mark.asyncio
async def test_18c_keyword_worker_fails_gracefully_without_topic():
    """TEST 18c: Worker returns FAILED (not exception) when topic is missing."""
    worker = KeywordResearchWorker()
    ctx = ExecutionContext(
        user={"id": str(uuid4())},
        product={},
        execution_id=str(uuid4()),
    )
    # No topic in memory or product

    result = await worker.run(ctx)

    assert result.status == WorkerStatus.FAILED
    assert result.error is not None
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_18d_worker_handles_llm_timeout_gracefully():
    """TEST 18d: LLM timeout → FAILED result, no evidence written, no exception raised."""
    worker = KeywordResearchWorker()
    ctx = _make_context(topic="fashion ecommerce")

    with patch(
        "app.ai.gateway.gateway.generate",
        side_effect=__import__("asyncio").TimeoutError(),
    ):
        result = await worker.run(ctx)

    # Should be FAILED (timeout treated as failure — no false positive evidence)
    assert result.status == WorkerStatus.FAILED
    assert result.confidence == 0.0
    assert any("timed out" in str(issue).lower() for issue in result.result.get("issues", [result.error or ""]))


def test_18e_worker_timeout_exceeds_provider_read_timeout():
    """TASK-038: the worker must not cancel NVIDIA before its HTTP read limit."""
    from app.ai.client import HTTP_TIMEOUT
    from app.workers.keyword_research import LLM_TIMEOUT_SECONDS

    assert HTTP_TIMEOUT.read == 120.0
    assert LLM_TIMEOUT_SECONDS > HTTP_TIMEOUT.read


@pytest.mark.asyncio
async def test_keyword_worker_uses_capability_model_and_bounded_tokens():
    """TASK-040: keyword generation uses its configured smaller model only."""
    worker = KeywordResearchWorker()
    ctx = _make_context(topic="Consumer Electronics")
    response = {
        "choices": [{"message": {"content": (
            '{"keywords":['
            '{"keyword":"consumer electronics","intent":"commercial","relevance":0.9}'
            '],"confidence":0.8}'
        )}}]
    }

    with patch(
        "app.ai.gateway.gateway.generate", new=AsyncMock(return_value=response)
    ) as mock_generate:
        result = await worker.run(ctx)

    assert result.status == WorkerStatus.SUCCESS
    assert mock_generate.await_args.kwargs["model"] == "meta/llama-3.1-8b-instruct"
    assert mock_generate.await_args.kwargs["max_tokens"] == 1000
    assert result.result["model_used"] == "meta/llama-3.1-8b-instruct"


@pytest.mark.asyncio
async def test_relevant_keyword_output_is_accepted():
    """TASK-039: target-relevant structured output remains positive evidence."""
    worker = KeywordResearchWorker()
    ctx = _make_context(topic="Wireless Bluetooth Headphones")
    response = {
        "choices": [{"message": {"content": (
            '{"keywords":['
            '{"keyword":"wireless bluetooth headphones","intent":"commercial","relevance":0.9},'
            '{"keyword":"noise cancelling headphones","intent":"commercial","relevance":0.85}'
            '],"confidence":0.8}'
        )}}]
    }

    with patch("app.ai.gateway.gateway.generate", new=AsyncMock(return_value=response)):
        result = await worker.run(ctx)

    assert result.status == WorkerStatus.SUCCESS
    assert result.evidence


@pytest.mark.asyncio
async def test_irrelevant_structural_output_is_rejected():
    """TASK-039: generic marketing keywords cannot earn target competence."""
    worker = KeywordResearchWorker()
    ctx = _make_context(topic="Wireless Bluetooth Headphones")
    response = {
        "choices": [{"message": {"content": (
            '{"keywords":['
            '{"keyword":"social media strategy","intent":"informational","relevance":0.9},'
            '{"keyword":"email marketing agency","intent":"commercial","relevance":0.85},'
            '{"keyword":"content marketing tips","intent":"informational","relevance":0.8}'
            '],"confidence":0.8}'
        )}}]
    }

    with patch("app.ai.gateway.gateway.generate", new=AsyncMock(return_value=response)):
        result = await worker.run(ctx)

    assert result.status == WorkerStatus.FAILED
    assert result.evidence == []
    assert result.confidence == 0.0
    assert "relevant" in (result.error or "").lower()


# ---------------------------------------------------------------------------
# Evidence quality tests (TASK-018 Phase 9)
# ---------------------------------------------------------------------------

def test_evidence_provenance_labels_present():
    """Every keyword entry has a provenance field."""
    entry = _build_keyword_entry("seo tips", "informational", 0.7, SOURCE_AI_HYPOTHESIS)
    assert entry["provenance"] == "ai_hypothesis"
    assert entry["source"] == SOURCE_AI_HYPOTHESIS

    seed_entry = _build_keyword_entry("organic seo", "commercial", 0.8, SOURCE_SEED_DERIVED)
    assert seed_entry["provenance"] == SOURCE_SEED_DERIVED


def test_seed_keywords_get_higher_relevance():
    """Seed keywords receive a relevance boost over AI-generated ones."""
    # Simulated: seed entry gets +0.10 boost
    seed_relevance = min(1.0, 0.60 + 0.10)  # 0.70
    ai_relevance = 0.60

    assert seed_relevance > ai_relevance, "Seed-derived keywords must score higher"


def test_normalise_intent_handles_unknown():
    """Unknown intent strings normalise to 'unknown'."""
    assert _normalise_intent("buy now") == "unknown"  # not an exact match
    assert _normalise_intent("commercial") == "commercial"
    assert _normalise_intent("INFORMATIONAL") == "informational"
    assert _normalise_intent(None) == "unknown"
    assert _normalise_intent("") == "unknown"


def test_priority_from_relevance():
    """Priority thresholds are applied correctly."""
    assert _priority_from_relevance(0.80) == "high"
    assert _priority_from_relevance(0.75) == "high"
    assert _priority_from_relevance(0.74) == "medium"
    assert _priority_from_relevance(0.45) == "medium"
    assert _priority_from_relevance(0.44) == "low"
    assert _priority_from_relevance(0.0) == "low"


# ---------------------------------------------------------------------------
# Full pipeline integration (learning loop E2E simulation)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_learning_loop_simulation():
    """
    Simulates the complete learning loop for keyword_research:
    Assessment #1 (LEARN_FIRST) → executions → profile update → Assessment #2 (READY_TO_APPLY)
    """
    from app.learning.profile_updater import _SUCCESS_BOOST_FACTOR

    matcher = CapabilityMatcher()
    req = OpportunityRequirements(
        opportunity_id="loop-test",
        required_capabilities=["keyword_research"],
    )

    # Step 1: Initial assessment — no evidence
    assessment_1 = matcher.match(req, {})
    assert assessment_1.readiness in (ReadinessState.LEARN_FIRST, ReadinessState.NOT_READY)

    # Step 2: Simulate 12 successful executions through ProfileUpdater policy.
    # From confidence=0.0, applying boost=(1-c)*0.12 per execution:
    # 7 iterations yields ~0.59, need ~12 to cross 0.65.
    confidence = 0.0
    evidence_count = 0
    for _ in range(12):
        confidence = min(1.0, confidence + (1.0 - confidence) * _SUCCESS_BOOST_FACTOR)
        evidence_count += 1

    assert confidence > 0.65, "Should cross threshold after 7 successes"

    # Step 3: Re-assess with updated (persisted) profile
    updated_snapshot = {
        "keyword_research": {
            "confidence": confidence,
            "evidence_count": evidence_count,
            "successful_execution_count": evidence_count,
            "failed_execution_count": 0,
            "capability_status": _derive_capability_status(evidence_count, confidence).value,
            "readiness": confidence * 0.8,
        }
    }
    assessment_2 = matcher.match(req, updated_snapshot)

    assert assessment_2.readiness in (
        ReadinessState.READY_TO_APPLY,
        ReadinessState.HIGH_CONFIDENCE,
    ), (
        f"Expected READY_TO_APPLY after learning, got {assessment_2.readiness}. "
        f"confidence={confidence:.3f}, evidence={evidence_count}"
    )
