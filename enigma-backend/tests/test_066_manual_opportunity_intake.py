from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.freelancing.manual_intake import (
    canonical_dedupe_key,
    DuplicateOpportunityError,
    ManualOpportunityService,
    ManualOpportunityStateError,
    fallback_fingerprint,
    normalize_external_id,
    normalize_source_url,
)
from app.models.marketplace import MarketplaceJob, ManualOpportunitySubmission
from app.routers.auth import require_admin_user
from app.routers.freelancing import ManualOpportunityCreate, create_manual_opportunity, router


def payload(**overrides):
    data = dict(
        platform="workana", source_url="https://EXAMPLE.com/job/1/?utm_source=x&b=2&a=1",
        external_project_id="wk-1", title="Build a FastAPI service",
        original_description="<script>alert(1)</script> Original Arabic/English text",
        normalized_requirements={"requirements": ["API"]}, budget_type="fixed",
        budget_min=100, budget_max=200, currency="usd", required_skills=["Python"],
        client_info={"name": "Public Client"}, source_language="ar",
        customer_preferred_language="en", proposal_language="en",
        translation_metadata={"detected_language_is_suggestion": True},
    )
    data.update(overrides)
    return data


class FakeDB:
    def __init__(self, scalars=None, commit_error=None, flush_error=None):
        self.scalars = list(scalars or [])
        self.added = []
        self.commit = AsyncMock(side_effect=commit_error)
        self.flush = AsyncMock(side_effect=flush_error)
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()

    async def scalar(self, _query):
        return self.scalars.pop(0) if self.scalars else None

    def add(self, value):
        self.added.append(value)


def test_url_normalization_removes_fragment_tracking_and_sorts_query():
    assert normalize_source_url("HTTPS://Example.COM:443/job/1/?utm_source=x&b=2&a=1#frag") == "https://example.com/job/1?a=1&b=2"


@pytest.mark.parametrize("url", ["javascript:alert(1)", "//example.com/job", "ftp://example.com/job"])
def test_url_validation_rejects_unsafe_or_non_http_urls(url):
    with pytest.raises(ValueError):
        normalize_source_url(url)


def test_fallback_fingerprint_is_stable_for_title_and_client():
    assert fallback_fingerprint("UPWORK", "  Build API ", {"name": "Client"}) == fallback_fingerprint("upwork", "build   api", {"name": "Client"})


def test_external_id_and_canonical_key_normalization_is_deterministic():
    assert normalize_external_id("  JOB-AbC  ") == "job-abc"
    first = canonical_dedupe_key("UPWORK", " JOB-ABC ", None, "Title", {})
    assert first == canonical_dedupe_key("upwork", "job-abc", None, "Different", {"name": "Other"})
    assert canonical_dedupe_key("upwork", "one", "https://EXAMPLE.com/job/1/?utm_source=x", "A", {}) == \
        canonical_dedupe_key("upwork", "two", "https://example.com/job/1", "B", {})
    assert first != canonical_dedupe_key("freelancer", "job-abc", None, "Title", {})


@pytest.mark.parametrize("platform", ["workana", "peopleperhour", "upwork", "freelancer", "mostaql", "other"])
def test_supported_platforms(platform):
    assert ManualOpportunityCreate(**payload(platform=platform)).platform == platform


@pytest.mark.parametrize("language", ["ar", "en", "es", "fr"])
def test_multilingual_fields_are_preserved(language):
    model = ManualOpportunityCreate(**payload(source_language=language, customer_preferred_language=language, proposal_language=language))
    assert (model.source_language, model.customer_preferred_language, model.proposal_language) == (language, language, language)


@pytest.mark.parametrize("change", [
    {"currency": "US"}, {"source_language": "de"}, {"budget_min": -1},
    {"budget_min": 300, "budget_max": 200}, {"title": ""}, {"original_description": ""},
])
def test_invalid_currency_language_budget_and_required_content(change):
    with pytest.raises((ValidationError, ValueError)):
        ManualOpportunityCreate(**payload(**change))


@pytest.mark.asyncio
async def test_creation_is_durable_profile_owned_and_audited_without_source_mutation():
    db = FakeDB()
    service = ManualOpportunityService()
    original = payload()["original_description"]
    job = await service.create(db, actor_id="admin-user-id", data=payload())
    assert db.added == [job]
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()
    assert job.profile_id == "enigma_profile"
    assert job.created_by_user_id == "admin-user-id"
    assert job.ingestion_source == "manual" and job.lifecycle_status == "draft"
    assert job.original_text == original and job.description == original
    assert job.source_language == "ar" and job.proposal_language == "en"


@pytest.mark.asyncio
async def test_duplicate_returns_existing_reference_and_never_writes():
    existing = SimpleNamespace(job_id="existing-job")
    db = FakeDB([existing])
    with pytest.raises(DuplicateOpportunityError) as error:
        await ManualOpportunityService().create(db, actor_id="admin", data=payload())
    assert error.value.existing_job_id == "existing-job"
    assert db.added == []
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_database_uniqueness_race_returns_canonical_existing_job():
    existing = SimpleNamespace(job_id="winner")
    db = FakeDB([None, None, None, existing], flush_error=IntegrityError("insert", {}, Exception("unique")))
    with pytest.raises(DuplicateOpportunityError) as error:
        await ManualOpportunityService().create(db, actor_id="admin", data=payload())
    assert error.value.existing_job_id == "winner"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_uniqueness_race_uses_same_duplicate_contract_as_create():
    job = await ManualOpportunityService().create(FakeDB(), actor_id="admin", data=payload())
    existing = SimpleNamespace(job_id="canonical-job")
    db = FakeDB([None, None, None, existing], flush_error=IntegrityError("update", {}, Exception("unique")))
    with pytest.raises(DuplicateOpportunityError) as error:
        await ManualOpportunityService().update(db, job=job, data={"source_url": "https://example.com/collision"})
    assert error.value.existing_job_id == "canonical-job"
    db.rollback.assert_awaited_once()


def test_migration_012_uses_runtime_canonical_identity_order():
    source = (Path(__file__).parents[1] / "alembic/versions/012_canonical_manual_dedupe.py").read_text(encoding="utf-8")
    assert "md5(" in source
    assert "lower(trim(platform)) || '|'" in source
    assert "COALESCE(NULLIF(url, ''), NULLIF(lower(trim(platform_job_id)), ''), identity_fingerprint)" in source
    assert "row_number()" in source and "duplicate_rank > 1" in source


@pytest.mark.asyncio
async def test_general_assessment_preserves_terminal_manual_lifecycle(monkeypatch):
    from app.routers import enigma_profile
    job = SimpleNamespace(
        job_id="manual-1", profile_id="enigma_profile", ingestion_source="manual", lifecycle_status="won",
        platform="workana", title="Job", description="Description", budget_min=None, budget_max=None,
        currency="USD", skills_required=[],
    )
    assessment = SimpleNamespace(
        opportunity_id="manual-1", overall_score=0.9, assessed_at=datetime(2026, 1, 1),
        readiness=SimpleNamespace(value="ready_to_apply"), capability_matches=[], missing_capabilities=[],
        weak_capabilities=[], unmapped_skills=[], risk_flags=[], reasoning_summary="ready",
    )
    decision = SimpleNamespace(
        decision=SimpleNamespace(value="ready_to_apply"), blocking_capability=None,
        execution_available=True, policy_overridden=False,
    )
    db = FakeDB([job, None])
    monkeypatch.setattr(enigma_profile._assessment_service, "assess", AsyncMock(return_value=(None, assessment, decision)))
    await enigma_profile.assess_existing_job("manual-1", SimpleNamespace(id="user-1"), db)
    assert job.lifecycle_status == "won"
    db.commit.assert_awaited_once()


def test_general_assessment_route_does_not_expose_commit_control():
    import inspect
    from app.routers.enigma_profile import assess_existing_job
    assert "commit" not in inspect.signature(assess_existing_job).parameters


@pytest.mark.asyncio
async def test_service_flushes_without_intermediate_commit():
    db = FakeDB()
    await ManualOpportunityService().create(db, actor_id="admin", data=payload())
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_endpoint_rolls_back_on_partial_failure(monkeypatch):
    from app.routers import freelancing as freelancing_router
    db = FakeDB()
    monkeypatch.setattr(freelancing_router._manual_intake_service, "create", AsyncMock(side_effect=RuntimeError("analysis failed")))
    with pytest.raises(RuntimeError, match="analysis failed"):
        await create_manual_opportunity(ManualOpportunityCreate(**payload()), SimpleNamespace(id="admin"), db)
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_editing_draft_commits_and_preserves_audit_identity():
    job = await ManualOpportunityService().create(FakeDB(), actor_id="creator", data=payload())
    db = FakeDB()
    updated = await ManualOpportunityService().update(db, job=job, data={"title": "Updated title"})
    assert updated.title == "Updated title" and updated.created_by_user_id == "creator"
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()
    assert updated.original_text == payload()["original_description"]


@pytest.mark.asyncio
async def test_editing_description_never_replaces_original_source_text():
    job = await ManualOpportunityService().create(FakeDB(), actor_id="creator", data=payload())
    original = job.original_text
    await ManualOpportunityService().update(FakeDB(), job=job, data={"original_description": "Corrected derived description"})
    assert job.description == "Corrected derived description"
    assert job.original_text == original


@pytest.mark.asyncio
async def test_edit_after_submission_is_forbidden():
    job = SimpleNamespace(lifecycle_status="manually_submitted")
    with pytest.raises(ManualOpportunityStateError, match="immutable"):
        await ManualOpportunityService().update(FakeDB(), job=job, data={"title": "Changed"})


@pytest.mark.asyncio
async def test_manual_submission_creates_immutable_snapshot_and_lifecycle_transition():
    job = SimpleNamespace(job_id="job-1", lifecycle_status="proposal_prepared", proposal_application_id="pkg-1")
    package = SimpleNamespace(application_id="pkg-1", state="APPROVED")
    intent = SimpleNamespace(submission_id="intent-1")
    db = FakeDB([package, intent, None])
    record = await ManualOpportunityService().record_submission(db, job=job, actor_id="admin", data={
        "proposal_text": "Exact submitted proposal", "currency": "usd", "submitted_price": 150,
        "marketplace_proposal_id": None, "submitted_at": datetime(2026, 1, 1),
        "delivery_estimate": "7 days", "admin_notes": "Entered by admin",
    })
    assert isinstance(record, ManualOpportunitySubmission)
    assert record.proposal_text_snapshot == "Exact submitted proposal"
    assert record.created_by_user_id == "admin" and job.lifecycle_status == "manually_submitted"
    assert record.application_id == "pkg-1" and record.submission_intent_id == "intent-1"
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_second_submission_cannot_overwrite_snapshot():
    job = SimpleNamespace(job_id="job-1", lifecycle_status="proposal_prepared", proposal_application_id="pkg-1")
    package = SimpleNamespace(application_id="pkg-1", state="APPROVED")
    intent = SimpleNamespace(submission_id="intent-1")
    db = FakeDB([package, intent, SimpleNamespace(id=1)])
    with pytest.raises(ManualOpportunityStateError, match="already exists"):
        await ManualOpportunityService().record_submission(db, job=job, actor_id="admin", data={"proposal_text": "replacement", "currency": "USD"})


@pytest.mark.parametrize("source,target", [
    ("draft", "analyzed"), ("analyzed", "manually_submitted"),
    ("won", "client_replied"), ("lost", "manually_submitted"),
])
def test_invalid_lifecycle_transitions_are_rejected(source, target):
    job = SimpleNamespace(lifecycle_status=source)
    with pytest.raises(ManualOpportunityStateError, match="Invalid lifecycle transition"):
        ManualOpportunityService.transition(job, target)


def test_valid_lifecycle_transitions_and_terminal_states():
    job = SimpleNamespace(lifecycle_status="draft")
    for target in ("ready_for_analysis", "analyzed", "proposal_prepared", "manually_submitted", "client_replied", "won"):
        ManualOpportunityService.transition(job, target)
    with pytest.raises(ManualOpportunityStateError):
        ManualOpportunityService.transition(job, "lost")


@pytest.mark.asyncio
@pytest.mark.parametrize("package,intent", [
    (None, None), (SimpleNamespace(application_id="pkg-1", state="READY_FOR_HUMAN_APPROVAL"), None),
    (SimpleNamespace(application_id="pkg-1", state="APPROVED"), None),
])
async def test_submission_requires_owned_approved_package_and_active_intent(package, intent):
    job = SimpleNamespace(job_id="job-1", lifecycle_status="proposal_prepared", proposal_application_id="pkg-1")
    db = FakeDB([package] + ([intent] if package and package.state == "APPROVED" else []))
    with pytest.raises(ManualOpportunityStateError):
        await ManualOpportunityService().record_submission(db, job=job, actor_id="admin", data={"proposal_text": "x", "currency": "USD"})


@pytest.mark.asyncio
async def test_non_admin_rejected_and_admin_accepted():
    with pytest.raises(HTTPException) as rejected:
        await require_admin_user(SimpleNamespace(email="user@example.com", plan="user"))
    assert rejected.value.status_code == 403


def test_every_manual_endpoint_requires_admin_dependency():
    manual_routes = [route for route in router.routes if "/manual" in route.path]
    assert manual_routes
    for route in manual_routes:
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert require_admin_user in dependency_calls


def test_pipeline_handoff_routes_exist_without_external_submission_route():
    paths = {route.path for route in router.routes}
    assert "/api/freelancing/manual/{job_id}/analyze" in paths
    assert "/api/freelancing/manual/{job_id}/proposal-package" in paths
    assert "/api/freelancing/manual/{job_id}/submission" in paths
    assert not any("external-submit" in path for path in paths)


def test_frontend_has_validation_api_integration_labels_and_safe_text_rendering():
    source = (Path(__file__).parents[2] / "enigma-frontend-v2/app/components/freelancing-control-center.tsx").read_text(encoding="utf-8")
    for expected in ("Save Draft", "Save and Analyze", "/api/freelancing/manual", "Manual entry", "Not submitted", "Submitted manually", "No live API connection"):
        assert expected in source
    assert "dangerouslySetInnerHTML" not in source
    assert "manualDetail.original_text" in source
