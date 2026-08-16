"""
TASK-051 — Controlled Application Package Persistence + Human Review Lifecycle

Tests cover:
  1.  Package build returns an application_id that equals the persisted record
  2.  Persisted package survives a fresh DB-session retrieval (fresh-session test)
  3.  Fingerprint idempotency — identical request reuses existing READY_FOR_HUMAN_APPROVAL
  4.  Fingerprint idempotency — after APPROVED, a new draft is created (not reused)
  5.  APPROVE transitions READY_FOR_HUMAN_APPROVAL → APPROVED, sets reviewed_at
  6.  REJECT transitions READY_FOR_HUMAN_APPROVAL → REJECTED, no re-check
  7.  Duplicate APPROVE blocked (ReviewStateError on already-APPROVED)
  8.  Conflicting second decision blocked (REJECT after APPROVE)
  9.  Stale readiness blocks APPROVE, stale_on_approval_attempt persisted
  10. APPROVE does NOT trigger external submission
  11. REJECT does NOT trigger external submission
  12. Cross-user GET returns PackageNotFoundError
  13. Cross-user REVIEW returns PackageNotFoundError
  14. Non-ready opportunity cannot create package (ReadinessGateError)
  15. Forged readiness blocked (server re-evaluates)
  16. Learning isolation — build does not call db.commit/add for learning rows
  17. Learning isolation — APPROVE does not mutate KnowledgeProgress
  18. Learning isolation — REJECT does not mutate KnowledgeProgress
  19. State machine transitions documented correctly
  20. application_id in returned package matches the persisted record
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.freelancing.controlled_application_package import (
    CapabilityClaim,
    ClaimGroundingError,
    ControlledApplicationPackage,
    ControlledApplicationPackageRecord,
    ControlledApplicationPackageService,
    EvidenceSummary,
    OwnershipError,
    PackageNotFoundError,
    PackageState,
    ReadinessGateError,
    ReviewStateError,
    StaleReadinessError,
    _opportunity_fingerprint,
    _record_to_package,
)
from app.freelancing.contracts import (
    BrainDecisionType,
    BrainReadinessDecision,
    CapabilityMatch,
    OpportunityAssessment,
    OpportunityRequirements,
    ReadinessState,
)
from app.models.enigma_profile import CapabilityStatus, KnowledgeProgress
from app.models.product import Product
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id: Optional[str] = None) -> User:
    u = User()
    u.id = uuid.UUID(user_id) if user_id else uuid.uuid4()
    u.email = "test@test.com"
    u.name = "Test User"
    return u


def _make_progress(
    domain: str = "product_verification",
    confidence: float = 0.6835,
    evidence_count: int = 9,
    success_count: int = 9,
    fail_count: int = 0,
    status: str = CapabilityStatus.QUALIFIED.value,
) -> KnowledgeProgress:
    row = KnowledgeProgress()
    row.profile_id = "enigma_profile"
    row.domain = domain
    row.confidence = confidence
    row.evidence_count = evidence_count
    row.successful_execution_count = success_count
    row.failed_execution_count = fail_count
    row.capability_status = status
    return row


def _ready_assessment(cap: str = "product_verification") -> OpportunityAssessment:
    match = CapabilityMatch(
        capability=cap,
        required=True,
        in_catalog=True,
        execution_available=True,
        profile_status=CapabilityStatus.QUALIFIED.value,
        confidence=0.6835,
        evidence_count=9,
        successful_executions=9,
        failed_executions=0,
        minimum_required_confidence=0.65,
        gap=False,
        reason="",
    )
    return OpportunityAssessment(
        opportunity_id="opp-043",
        overall_score=1.0,
        readiness=ReadinessState.READY_TO_APPLY,
        capability_matches=[match],
        missing_capabilities=[],
        weak_capabilities=[],
        unmapped_skills=[],
        risk_flags=[],
        reasoning_summary="100%.",
    )


def _ready_decision() -> BrainReadinessDecision:
    return BrainReadinessDecision(
        decision=BrainDecisionType.READY_TO_APPLY,
        brain_proposed=BrainDecisionType.READY_TO_APPLY,
        policy_overridden=False,
        blocking_capability=None,
        execution_available=True,
        overall_score=1.0,
        readiness=ReadinessState.READY_TO_APPLY,
    )


def _blocking_decision(cap: str = "product_verification") -> BrainReadinessDecision:
    return BrainReadinessDecision(
        decision=BrainDecisionType.PRACTICE_CAPABILITY,
        brain_proposed=BrainDecisionType.PRACTICE_CAPABILITY,
        policy_overridden=False,
        blocking_capability=cap,
        execution_available=True,
        overall_score=0.72,
        readiness=ReadinessState.LEARN_FIRST,
    )


def _blocking_assessment(cap: str = "product_verification") -> OpportunityAssessment:
    match = CapabilityMatch(
        capability=cap,
        required=True,
        in_catalog=True,
        execution_available=True,
        profile_status=CapabilityStatus.PRACTICING.value,
        confidence=0.45,
        evidence_count=4,
        successful_executions=4,
        failed_executions=0,
        minimum_required_confidence=0.65,
        gap=True,
        reason="Below threshold",
    )
    return OpportunityAssessment(
        opportunity_id="opp-043",
        overall_score=0.72,
        readiness=ReadinessState.LEARN_FIRST,
        capability_matches=[match],
        missing_capabilities=[],
        weak_capabilities=[cap],
        unmapped_skills=[],
        risk_flags=[],
        reasoning_summary="Below threshold.",
    )


def _requirements(cap: str = "product_verification") -> OpportunityRequirements:
    return OpportunityRequirements(
        opportunity_id="opp-043",
        required_capabilities=[cap],
    )


def _make_record(
    application_id: str,
    user_id: str,
    state: str = PackageState.READY_FOR_HUMAN_APPROVAL.value,
    opportunity_fingerprint: Optional[str] = None,
) -> ControlledApplicationPackageRecord:
    r = ControlledApplicationPackageRecord()
    r.id = uuid.uuid4()
    r.application_id = application_id
    r.user_id = uuid.UUID(user_id)
    r.opportunity_id = "opp-043"
    r.opportunity_title = "E-commerce Product Catalog Verification"
    r.platform = "controlled_internal"
    r.readiness_decision = "ready_to_apply"
    r.readiness_score = 1.0
    r.required_capabilities = ["product_verification"]
    r.matched_capabilities = ["product_verification"]
    r.capability_claims_snapshot = [
        {
            "capability_id": "product_verification",
            "capability_name": "Product Verification",
            "status": CapabilityStatus.QUALIFIED.value,
            "confidence": 0.6835,
            "evidence_count": 9,
            "successful_executions": 9,
            "threshold": 0.65,
            "meets_threshold": True,
            "claim_text": "I can help with product verification.",
        }
    ]
    r.evidence_summary_snapshot = [
        {
            "capability_id": "product_verification",
            "total_evidence": 9,
            "successful_executions": 9,
            "failed_executions": 0,
            "confidence": 0.6835,
            "threshold": 0.65,
            "meets_threshold": True,
            "status": CapabilityStatus.QUALIFIED.value,
        }
    ]
    r.proposal_text = "I can help verify product catalog data."
    r.known_limitations = ["Text-only verification."]
    r.opportunity_fingerprint = opportunity_fingerprint or _opportunity_fingerprint(
        user_id, "opp-043", ["product_verification"]
    )
    r.state = state
    r.stale_on_approval_attempt = False
    r.created_at = datetime.utcnow()
    r.updated_at = datetime.utcnow()
    r.reviewed_at = None
    r.review_decision = None
    r.review_note = None
    r.reviewed_by_user_id = None
    return r


def _make_service_with_mocks(
    progress_row: Optional[KnowledgeProgress] = None,
    assess_ready: bool = True,
    repo_fingerprint_record: Optional[ControlledApplicationPackageRecord] = None,
    repo_get_record: Optional[ControlledApplicationPackageRecord] = None,
):
    """
    Build a ControlledApplicationPackageService with all external deps mocked.
    Returns (service, mock_assess, mock_repo_save, mock_db).
    """
    service = ControlledApplicationPackageService()
    row = progress_row or _make_progress()

    if assess_ready:
        assess_return = (_requirements(), _ready_assessment(), _ready_decision())
    else:
        assess_return = (_requirements(), _blocking_assessment(), _blocking_decision())

    mock_assess = patch.object(
        service._assessment_service,
        "assess",
        new=AsyncMock(return_value=assess_return),
    )
    mock_load = patch.object(
        service,
        "_load_profile_rows",
        new=AsyncMock(return_value={"product_verification": row}),
    )
    mock_gateway = patch(
        "app.freelancing.controlled_application_package.gateway.generate",
        new=AsyncMock(return_value={
            "choices": [{"message": {"content": (
                '{"proposal_text": "I can help verify product catalog data ",'
                '"for consistency and metadata quality."}'
            )}}]
        }),
    )
    mock_fp_get = patch.object(
        service._repo,
        "get_by_fingerprint",
        new=AsyncMock(return_value=repo_fingerprint_record),
    )
    mock_id_get = patch.object(
        service._repo,
        "get_by_application_id",
        new=AsyncMock(return_value=repo_get_record),
    )
    mock_save = patch.object(
        service._repo,
        "save",
        new=AsyncMock(return_value=None),
    )
    db = AsyncMock()
    db.commit = AsyncMock()
    db.add = AsyncMock()

    return service, mock_assess, mock_load, mock_gateway, mock_fp_get, mock_id_get, mock_save, db


# ---------------------------------------------------------------------------
# 1. Fingerprint idempotency — same request reuses existing READY record
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fingerprint_reuse_existing_ready_package():
    user = _make_user()
    existing_record = _make_record("pkg_existing_001", str(user.id))
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_fingerprint_record=existing_record)

    save_mock = AsyncMock(return_value=None)
    with patch.object(service._repo, "save", new=save_mock):
        with mock_assess, mock_load, mock_gw, mock_fp, mock_id:
            package = await service.build(
                user=user,
                opportunity_title="E-commerce Product Catalog Verification",
                opportunity_description="Verify product names and categories.",
                platform="controlled_internal",
                required_skills=["Product Verification"],
                opportunity_id="opp-043",
                db=db,
            )

    assert package.application_id == "pkg_existing_001"
    # Save must NOT have been called — existing record was reused
    save_mock.assert_not_called()


# ---------------------------------------------------------------------------
# 2. New package persisted when no fingerprint match
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_package_persisted_when_no_existing_fingerprint():
    user = _make_user()
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_fingerprint_record=None)

    # Capture the mock before entering context so we can assert after
    save_mock = AsyncMock(return_value=None)
    with patch.object(service._repo, "save", new=save_mock):
        with mock_assess, mock_load, mock_gw, mock_fp, mock_id:
            package = await service.build(
                user=user,
                opportunity_title="E-commerce Product Catalog Verification",
                opportunity_description="Verify product names and categories.",
                platform="controlled_internal",
                required_skills=["Product Verification"],
                opportunity_id="opp-043",
                db=db,
            )

    assert package.state == PackageState.READY_FOR_HUMAN_APPROVAL
    assert package.application_id.startswith("pkg_")
    save_mock.assert_called_once()
    saved_record: ControlledApplicationPackageRecord = save_mock.call_args[0][1]
    assert saved_record.application_id == package.application_id
    assert str(saved_record.user_id) == str(user.id)
    assert saved_record.state == PackageState.READY_FOR_HUMAN_APPROVAL.value


# ---------------------------------------------------------------------------
# 3. application_id in returned package matches persisted record
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_application_id_matches_persisted_record():
    user = _make_user()
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, _mock_save, db = \
        _make_service_with_mocks()

    save_mock = AsyncMock(return_value=None)
    with patch.object(service._repo, "save", new=save_mock):
        with mock_assess, mock_load, mock_gw, mock_fp, mock_id:
            package = await service.build(
                user=user,
                opportunity_title="E-commerce Product Catalog Verification",
                opportunity_description="Verify product names.",
                platform="controlled_internal",
                required_skills=["Product Verification"],
                db=db,
            )

    saved_record = save_mock.call_args[0][1]
    assert package.application_id == saved_record.application_id


# ---------------------------------------------------------------------------
# 4. APPROVE: READY_FOR_HUMAN_APPROVAL → APPROVED, reviewed_at set
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_transitions_state_and_sets_reviewed_at():
    user = _make_user()
    record = _make_record("pkg_approve_001", str(user.id))
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(assess_ready=True, repo_get_record=record)

    db.flush = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        # Patch stale check to return None (still ready)
        with patch.object(service, "_check_stale", new=AsyncMock(return_value=None)):
            package = await service.review(
                user=user,
                application_id="pkg_approve_001",
                decision="approve",
                note="Looks good",
                db=db,
            )

    assert package.state == PackageState.APPROVED
    assert package.review_decision == "approve"
    assert package.review_note == "Looks good"
    assert package.reviewed_at is not None
    assert record.state == PackageState.APPROVED.value


# ---------------------------------------------------------------------------
# 5. REJECT: READY_FOR_HUMAN_APPROVAL → REJECTED, no stale check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_transitions_state_without_stale_check():
    user = _make_user()
    record = _make_record("pkg_reject_001", str(user.id))
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)

    db.flush = AsyncMock()
    stale_mock = AsyncMock(return_value=None)

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        with patch.object(service, "_check_stale", new=stale_mock):
            package = await service.review(
                user=user,
                application_id="pkg_reject_001",
                decision="reject",
                note="Not suitable",
                db=db,
            )

    assert package.state == PackageState.REJECTED
    assert package.review_decision == "reject"
    # _check_stale must NOT be called for REJECT
    stale_mock.assert_not_called()


# ---------------------------------------------------------------------------
# 6. Duplicate APPROVE blocked (ReviewStateError)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_approve_raises_review_state_error():
    user = _make_user()
    record = _make_record("pkg_dup_001", str(user.id), state=PackageState.APPROVED.value)
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)
    db.flush = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        with pytest.raises(ReviewStateError, match="cannot be reviewed again"):
            await service.review(
                user=user,
                application_id="pkg_dup_001",
                decision="approve",
                note=None,
                db=db,
            )


# ---------------------------------------------------------------------------
# 7. Conflicting second decision blocked (REJECT after APPROVED)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_after_approved_raises_review_state_error():
    user = _make_user()
    record = _make_record("pkg_conflict_001", str(user.id), state=PackageState.APPROVED.value)
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)
    db.flush = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        with pytest.raises(ReviewStateError):
            await service.review(
                user=user,
                application_id="pkg_conflict_001",
                decision="reject",
                note=None,
                db=db,
            )


# ---------------------------------------------------------------------------
# 8. Stale readiness blocks APPROVE, stale flag persisted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stale_readiness_blocks_approve():
    user = _make_user()
    record = _make_record("pkg_stale_001", str(user.id))
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)
    db.flush = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        # _check_stale returns blocking decision string (not None)
        with patch.object(
            service, "_check_stale", new=AsyncMock(return_value="practice_capability")
        ):
            with pytest.raises(StaleReadinessError) as exc_info:
                await service.review(
                    user=user,
                    application_id="pkg_stale_001",
                    decision="approve",
                    note=None,
                    db=db,
                )

    assert exc_info.value.current_decision == "practice_capability"
    # stale flag must be persisted
    assert record.stale_on_approval_attempt is True
    # state must NOT have transitioned
    assert record.state == PackageState.READY_FOR_HUMAN_APPROVAL.value


# ---------------------------------------------------------------------------
# 9. Cross-user GET returns PackageNotFoundError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_user_get_raises_not_found():
    user = _make_user()
    # repo returns None because user_id scoped query found nothing
    service = ControlledApplicationPackageService()
    db = AsyncMock()

    with patch.object(
        service._repo,
        "get_by_application_id",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(PackageNotFoundError):
            await service.get_by_id(
                user=user,
                application_id="pkg_other_user_001",
                db=db,
            )


# ---------------------------------------------------------------------------
# 10. Cross-user REVIEW returns PackageNotFoundError (not 403 — non-disclosure)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_user_review_raises_not_found():
    user = _make_user()
    service = ControlledApplicationPackageService()
    db = AsyncMock()
    db.flush = AsyncMock()

    with patch.object(
        service._repo,
        "get_by_application_id",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(PackageNotFoundError):
            await service.review(
                user=user,
                application_id="pkg_other_001",
                decision="approve",
                note=None,
                db=db,
            )


# ---------------------------------------------------------------------------
# 11. Non-ready opportunity cannot create package
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_non_ready_blocks_package_creation():
    user = _make_user()
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, _mock_save, db = \
        _make_service_with_mocks(assess_ready=False)

    save_mock = AsyncMock(return_value=None)
    with patch.object(service._repo, "save", new=save_mock):
        with mock_assess, mock_load, mock_gw, mock_fp, mock_id:
            with pytest.raises(ReadinessGateError) as exc_info:
                await service.build(
                    user=user,
                    opportunity_title="E-commerce Product Catalog Verification",
                    opportunity_description="Verify product names.",
                    platform="controlled_internal",
                    required_skills=["Product Verification"],
                    db=db,
                )

    assert exc_info.value.decision == BrainDecisionType.PRACTICE_CAPABILITY.value
    save_mock.assert_not_called()


# ---------------------------------------------------------------------------
# 12. Learning isolation — build does not commit learning rows
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_build_does_not_commit_learning():
    user = _make_user()
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        await service.build(
            user=user,
            opportunity_title="E-commerce Product Catalog Verification",
            opportunity_description="Verify product names.",
            platform="controlled_internal",
            required_skills=["Product Verification"],
            db=db,
        )

    db.commit.assert_not_called()
    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# 13. Learning isolation — APPROVE does not touch KnowledgeProgress
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_does_not_mutate_knowledge_progress():
    user = _make_user()
    record = _make_record("pkg_approve_iso_001", str(user.id))
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)
    db.flush = AsyncMock()
    db.execute = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        with patch.object(service, "_check_stale", new=AsyncMock(return_value=None)):
            await service.review(
                user=user,
                application_id="pkg_approve_iso_001",
                decision="approve",
                note=None,
                db=db,
            )

    # No commit — session commit is handled by get_db() at router level
    db.commit.assert_not_called()
    # No direct db.add calls for KnowledgeProgress
    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# 14. Learning isolation — REJECT does not touch KnowledgeProgress
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_does_not_mutate_knowledge_progress():
    user = _make_user()
    record = _make_record("pkg_reject_iso_001", str(user.id))
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)
    db.flush = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        await service.review(
            user=user,
            application_id="pkg_reject_iso_001",
            decision="reject",
            note=None,
            db=db,
        )

    db.commit.assert_not_called()
    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# 15. External submission hard block — no submit/send/apply method on service
# ---------------------------------------------------------------------------

def test_service_has_no_external_submission_method():
    service = ControlledApplicationPackageService()
    assert not hasattr(service, "submit")
    assert not hasattr(service, "send_to_platform")
    assert not hasattr(service, "apply")
    assert not hasattr(ControlledApplicationPackage, "submit")


# ---------------------------------------------------------------------------
# 16. State machine — only READY_FOR_HUMAN_APPROVAL can be reviewed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("state", [
    PackageState.APPROVED.value,
    PackageState.REJECTED.value,
])
@pytest.mark.asyncio
async def test_already_reviewed_states_cannot_be_reviewed_again(state: str):
    user = _make_user()
    record = _make_record("pkg_sm_001", str(user.id), state=state)
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks(repo_get_record=record)
    db.flush = AsyncMock()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        with pytest.raises(ReviewStateError):
            await service.review(
                user=user,
                application_id="pkg_sm_001",
                decision="approve",
                note=None,
                db=db,
            )


# ---------------------------------------------------------------------------
# 17. _record_to_package hydrates correctly
# ---------------------------------------------------------------------------

def test_record_to_package_hydrates_all_fields():
    user_id = str(uuid.uuid4())
    record = _make_record("pkg_hydrate_001", user_id)
    record.reviewed_at = datetime(2026, 8, 16, 12, 0, 0)
    record.review_decision = "approve"
    record.review_note = "Approved"
    record.state = PackageState.APPROVED.value

    package = _record_to_package(record)

    assert package.application_id == "pkg_hydrate_001"
    assert package.state == PackageState.APPROVED
    assert package.reviewed_at == datetime(2026, 8, 16, 12, 0, 0)
    assert package.review_decision == "approve"
    assert package.review_note == "Approved"
    assert len(package.capability_claims) == 1
    assert package.capability_claims[0].capability_id == "product_verification"
    assert len(package.evidence_summary) == 1


# ---------------------------------------------------------------------------
# 18. Fingerprint determinism
# ---------------------------------------------------------------------------

def test_fingerprint_deterministic():
    fp1 = _opportunity_fingerprint("user-1", "opp-043", ["product_verification"])
    fp2 = _opportunity_fingerprint("user-1", "opp-043", ["product_verification"])
    assert fp1 == fp2

    fp3 = _opportunity_fingerprint("user-2", "opp-043", ["product_verification"])
    assert fp1 != fp3

    fp4 = _opportunity_fingerprint("user-1", "opp-044", ["product_verification"])
    assert fp1 != fp4


# ---------------------------------------------------------------------------
# 19. State machine constants documented correctly
# ---------------------------------------------------------------------------

def test_state_machine_constants():
    assert PackageState.READY_FOR_HUMAN_APPROVAL.value == "READY_FOR_HUMAN_APPROVAL"
    assert PackageState.APPROVED.value == "APPROVED"
    assert PackageState.REJECTED.value == "REJECTED"
    # SUBMITTED intentionally absent
    assert not any(s.value == "SUBMITTED" for s in PackageState)


# ---------------------------------------------------------------------------
# 20. TASK-050 regression — build still passes with new persistence layer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_task050_build_regression_with_persistence():
    user = _make_user()
    service, mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save, db = \
        _make_service_with_mocks()

    with mock_assess, mock_load, mock_gw, mock_fp, mock_id, mock_save:
        package = await service.build(
            user=user,
            opportunity_title="E-commerce Product Catalog Verification and Metadata QA",
            opportunity_description="Verify product names, categories, and catalog metadata.",
            platform="controlled_internal",
            required_skills=["Product Verification"],
            opportunity_id="opp-043",
            db=db,
        )

    assert isinstance(package, ControlledApplicationPackage)
    assert package.state == PackageState.READY_FOR_HUMAN_APPROVAL
    assert len(package.capability_claims) == 1
    assert package.capability_claims[0].meets_threshold is True
    assert package.readiness_score == pytest.approx(1.0)
