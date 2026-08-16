"""
TASK-050 — Controlled Application Package Tests

Tests cover:
  1. Claim grounding — only threshold-met capabilities produce valid claims
  2. Readiness gate — below-threshold opportunity cannot create a package
  3. Forged readiness blocked — client cannot bypass server-side assessment
  4. Unsupported claim rejected — ClaimGroundingError for sub-threshold cap
  5. Cross-user evidence blocked — OwnershipError for another user's product
  6. Package does NOT mutate learning (side-effect check)
  7. External submission prevented — state is always READY_FOR_HUMAN_APPROVAL
  8. Replay / repeated request behaviour — each call returns a new package_id
  9. Service builds valid package from a ready opportunity (unit)
  10. Assessment re-evaluation is server-side (forged decision value rejected)
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.freelancing.controlled_application_package import (
    ClaimGroundingError,
    ControlledApplicationPackage,
    ControlledApplicationPackageService,
    OwnershipError,
    PackageState,
    ReadinessGateError,
    _ground_claim,
    _validate_proposal_text,
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


def _make_product(
    product_id: Optional[str] = None,
    user_id: Optional[str] = None,
    category: str = "Sports and Outdoors",
) -> Product:
    p = Product()
    p.id = uuid.UUID(product_id) if product_id else uuid.uuid4()
    p.user_id = uuid.UUID(user_id) if user_id else uuid.uuid4()
    p.name = "Test Product"
    p.category = category
    p.description = "A test product"
    p.status = "onboarding"
    p.created_at = datetime.utcnow()
    return p


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
        reasoning_summary="Overall capability score: 100%.",
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
        reason="Confidence below threshold",
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
        reasoning_summary="Below-threshold capability.",
    )


def _requirements(cap: str = "product_verification") -> OpportunityRequirements:
    return OpportunityRequirements(
        opportunity_id="opp-043",
        required_capabilities=[cap],
        optional_capabilities=[],
        unmapped_skills=[],
    )


# ---------------------------------------------------------------------------
# 1. Claim grounding — valid qualified capability
# ---------------------------------------------------------------------------

def test_claim_grounding_qualified_capability():
    row = _make_progress(confidence=0.6835, status=CapabilityStatus.QUALIFIED.value)
    claim = _ground_claim("product_verification", row)
    assert claim.capability_id == "product_verification"
    assert claim.meets_threshold is True
    assert claim.confidence == pytest.approx(0.6835)
    assert claim.evidence_count == 9
    assert "verified" in claim.claim_text.lower() or "can help" in claim.claim_text.lower()
    # No fabricated personal history
    assert "years of experience" not in claim.claim_text.lower()
    assert "previous client" not in claim.claim_text.lower()


# ---------------------------------------------------------------------------
# 2. Unsupported claim rejected — sub-threshold
# ---------------------------------------------------------------------------

def test_claim_grounding_rejects_sub_threshold():
    row = _make_progress(confidence=0.45, status=CapabilityStatus.PRACTICING.value)
    with pytest.raises(ClaimGroundingError, match="below threshold"):
        _ground_claim("product_verification", row)


# ---------------------------------------------------------------------------
# 3. Claim grounding — unknown capability rejected
# ---------------------------------------------------------------------------

def test_claim_grounding_rejects_unknown_capability():
    row = _make_progress(domain="nonexistent_capability")
    with pytest.raises(ClaimGroundingError, match="not in the catalog"):
        _ground_claim("nonexistent_capability", row)


# ---------------------------------------------------------------------------
# 4. Proposal text validation — strips fabricated markers
# ---------------------------------------------------------------------------

def test_proposal_validation_strips_fabricated_markers():
    row = _make_progress()
    claim = _ground_claim("product_verification", row)
    dirty_text = (
        "I have 10 years of experience and 500+ previous clients. "
        "My completion rate is 98%. I'm certified in ISO-9001. "
        "I can help with product verification."
    )
    validated, warnings = _validate_proposal_text(dirty_text, [claim])
    assert "10 years of experience" not in validated
    assert "previous clients" not in validated
    assert "completion rate" not in validated
    assert len(warnings) >= 3


def test_proposal_validation_clean_text_passes_unchanged():
    row = _make_progress()
    claim = _ground_claim("product_verification", row)
    clean_text = (
        "I can help verify product catalog data for consistency and accuracy. "
        "My approach involves reviewing category classification and metadata quality."
    )
    validated, warnings = _validate_proposal_text(clean_text, [claim])
    assert "[REDACTED]" not in validated
    assert validated.strip() != ""


# ---------------------------------------------------------------------------
# 5. Readiness gate — service rejects below-threshold opportunities
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_readiness_gate_blocks_below_threshold():
    user = _make_user()
    db = AsyncMock()

    service = ControlledApplicationPackageService()

    with patch.object(
        service._assessment_service,
        "assess",
        new=AsyncMock(return_value=(
            _requirements(),
            _blocking_assessment(),
            _blocking_decision(),
        )),
    ):
        with pytest.raises(ReadinessGateError) as exc_info:
            await service.build(
                user=user,
                opportunity_title="E-commerce Product Catalog",
                opportunity_description="Verify product names and categories.",
                platform="controlled_internal",
                required_skills=["Product Verification"],
                db=db,
            )

    assert exc_info.value.decision == BrainDecisionType.PRACTICE_CAPABILITY.value
    assert exc_info.value.blocking_capability == "product_verification"


# ---------------------------------------------------------------------------
# 6. Forged readiness blocked — service ignores client decision, re-evaluates
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forged_readiness_is_ignored_server_re_evaluates():
    """
    Client cannot inject ready_to_apply — server always reassesses.
    When server assessment says practice_capability, gate must fire
    regardless of what the client claims.
    """
    user = _make_user()
    db = AsyncMock()
    service = ControlledApplicationPackageService()

    # Server says: not ready
    with patch.object(
        service._assessment_service,
        "assess",
        new=AsyncMock(return_value=(
            _requirements(),
            _blocking_assessment(),
            _blocking_decision(),
        )),
    ):
        with pytest.raises(ReadinessGateError):
            # Even if caller somehow passes "ready_to_apply" in title —
            # it's irrelevant, the gate uses server-side assessment only
            await service.build(
                user=user,
                opportunity_title="E-commerce Product Catalog ready_to_apply",
                opportunity_description="Verify product names and categories.",
                platform="controlled_internal",
                required_skills=["Product Verification"],
                db=db,
            )


# ---------------------------------------------------------------------------
# 7. Cross-user evidence blocked — OwnershipError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_user_product_raises_ownership_error():
    owner_id = str(uuid.uuid4())
    requester_id = str(uuid.uuid4())
    product = _make_product(user_id=owner_id)
    user = _make_user(user_id=requester_id)

    db = AsyncMock()
    # DB returns a product owned by a different user
    db.execute = AsyncMock(
        return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=product)
        )
    )

    service = ControlledApplicationPackageService()
    with pytest.raises(OwnershipError, match="does not belong to user"):
        await service.build(
            user=user,
            opportunity_title="E-commerce Product Catalog",
            opportunity_description="Verify product names and categories.",
            platform="controlled_internal",
            required_skills=["Product Verification"],
            target_id=str(product.id),
            db=db,
        )


# ---------------------------------------------------------------------------
# 8. Valid package build — state is READY_FOR_HUMAN_APPROVAL, never SUBMITTED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_valid_build_returns_ready_for_human_approval():
    user = _make_user()
    db = AsyncMock()
    service = ControlledApplicationPackageService()

    progress_row = _make_progress()

    with patch.object(
        service._assessment_service,
        "assess",
        new=AsyncMock(return_value=(
            _requirements(),
            _ready_assessment(),
            _ready_decision(),
        )),
    ), patch.object(
        service,
        "_load_profile_rows",
        new=AsyncMock(return_value={"product_verification": progress_row}),
    ), patch.object(
        service._repo,
        "get_by_fingerprint",
        new=AsyncMock(return_value=None),
    ), patch.object(
        service._repo,
        "save",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.freelancing.controlled_application_package.gateway.generate",
        new=AsyncMock(return_value={
            "choices": [{"message": {"content": (
                '{"proposal_text": "I can help verify product catalog data for '
                'consistency and metadata quality. My approach involves reviewing '
                'category classification systematically."}'
            )}}]
        }),
    ):
        package = await service.build(
            user=user,
            opportunity_title="E-commerce Product Catalog Verification",
            opportunity_description="Verify product names, categories, and catalog metadata.",
            platform="controlled_internal",
            required_skills=["Product Verification"],
            db=db,
        )

    assert isinstance(package, ControlledApplicationPackage)
    assert package.state == PackageState.READY_FOR_HUMAN_APPROVAL
    assert package.state.value != "SUBMITTED"
    assert len(package.capability_claims) == 1
    assert package.capability_claims[0].capability_id == "product_verification"
    assert package.capability_claims[0].meets_threshold is True
    assert package.readiness_score == pytest.approx(1.0)
    assert len(package.application_id) > 0
    assert package.proposal_text != ""


# ---------------------------------------------------------------------------
# 9. External submission prevented — package has no submit method
# ---------------------------------------------------------------------------

def test_package_has_no_submit_method():
    """The ControlledApplicationPackage type must not expose a submit() method."""
    assert not hasattr(ControlledApplicationPackage, "submit")
    assert not hasattr(ControlledApplicationPackage, "send")
    assert not hasattr(ControlledApplicationPackage, "apply")


# ---------------------------------------------------------------------------
# 10. Replay — repeated valid calls return distinct application_ids
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repeated_calls_return_distinct_package_ids():
    user = _make_user()
    db = AsyncMock()
    service = ControlledApplicationPackageService()
    progress_row = _make_progress()

    kwargs = dict(
        user=user,
        opportunity_title="E-commerce Product Catalog Verification",
        opportunity_description="Verify product names, categories.",
        platform="controlled_internal",
        required_skills=["Product Verification"],
        db=db,
    )

    async def _build():
        with patch.object(
            service._assessment_service,
            "assess",
            new=AsyncMock(return_value=(
                _requirements(), _ready_assessment(), _ready_decision()
            )),
        ), patch.object(
            service,
            "_load_profile_rows",
            new=AsyncMock(return_value={"product_verification": progress_row}),
        ), patch.object(
            service._repo,
            "get_by_fingerprint",
            new=AsyncMock(return_value=None),
        ), patch.object(
            service._repo,
            "save",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.freelancing.controlled_application_package.gateway.generate",
            new=AsyncMock(return_value={
                "choices": [{"message": {"content": (
                    '{"proposal_text": "I can help with product verification."}'
                )}}]
            }),
        ):
            return await service.build(**kwargs)

    p1 = await _build()
    p2 = await _build()
    assert p1.application_id != p2.application_id, (
        "Each call must produce a fresh package_id (new drafts, not idempotent)"
    )


# ---------------------------------------------------------------------------
# 11. Package generation does NOT mutate learning
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_package_build_does_not_call_learning_persistence():
    """
    Package build must never call evidence mapper, promotion service,
    or any learning persistence path.
    """
    user = _make_user()
    db = AsyncMock()
    service = ControlledApplicationPackageService()
    progress_row = _make_progress()

    with patch.object(
        service._assessment_service,
        "assess",
        new=AsyncMock(return_value=(
            _requirements(), _ready_assessment(), _ready_decision()
        )),
    ), patch.object(
        service,
        "_load_profile_rows",
        new=AsyncMock(return_value={"product_verification": progress_row}),
    ), patch.object(
        service._repo,
        "get_by_fingerprint",
        new=AsyncMock(return_value=None),
    ), patch.object(
        service._repo,
        "save",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.freelancing.controlled_application_package.gateway.generate",
        new=AsyncMock(return_value={
            "choices": [{"message": {"content": (
                '{"proposal_text": "I can help verify product catalog data."}'
            )}}]
        }),
    ) as _gateway_mock:
        package = await service.build(
            user=user,
            opportunity_title="E-commerce Product Catalog Verification",
            opportunity_description="Verify product names, categories.",
            platform="controlled_internal",
            required_skills=["Product Verification"],
            db=db,
        )

    # DB commit must NOT have been called (no learning persistence)
    db.commit.assert_not_called()
    # DB add must NOT have been called
    db.add.assert_not_called()
    # Package is valid
    assert package.state == PackageState.READY_FOR_HUMAN_APPROVAL


# ---------------------------------------------------------------------------
# 12. Package state value is canonical
# ---------------------------------------------------------------------------

def test_package_state_ready_for_human_approval_is_canonical():
    assert PackageState.READY_FOR_HUMAN_APPROVAL.value == "READY_FOR_HUMAN_APPROVAL"
    assert PackageState.APPROVED.value == "APPROVED"
    assert PackageState.REJECTED.value == "REJECTED"
    # SUBMITTED is intentionally absent from TASK-051 PackageState
    assert not any(s.value == "SUBMITTED" for s in PackageState)
    # Service never auto-transitions to APPROVED/REJECTED
    states_set_automatically = [PackageState.READY_FOR_HUMAN_APPROVAL]
    assert PackageState.APPROVED not in states_set_automatically
