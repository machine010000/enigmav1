"""TASK-065 offline-only tests for Freelancer discovery orchestration."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.freelancing.freelancer_client import (
    FreelancerRateLimited,
    FreelancerTimeout,
    FreelancerUnauthorized,
)
from app.freelancing.freelancer_discovery_service import (
    FreelancerDiscoveryService,
    FreelancerNotConfiguredError,
    PROFILE_ID,
)
from app.freelancing.ingestion import NormalizedMarketplaceOpportunity
from app.routers.auth import require_admin_user
from app.routers import freelancing as freelancing_router


class _Savepoint:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.savepoints = 0

    def begin_nested(self):
        self.savepoints += 1
        return _Savepoint()

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class FakeAdapter:
    def __init__(self, opportunities=None, error=None, skipped=0):
        self.opportunities = opportunities or []
        self.error = error
        self.discovery_skipped_count = skipped
        self.closed = False
        self.calls = []

    async def discover_opportunities(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.opportunities

    async def close(self):
        self.closed = True


class FakeIngestion:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.profile_ids = []

    async def ingest(self, db, *, profile_id, opportunity):
        self.profile_ids.append(profile_id)
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(outcome=outcome)


def settings(token="offline-token", sandbox=True):
    return SimpleNamespace(FREELANCER_API_TOKEN=token, FREELANCER_SANDBOX=sandbox)


def opportunity(project_id: str, title: str = "Python API"):
    return NormalizedMarketplaceOpportunity(
        platform="freelancer",
        platform_job_id=project_id,
        title=title,
        description="Build an offline-tested API",
        skills=("Python", "FastAPI"),
    )


@pytest.mark.asyncio
async def test_adapter_to_ingestion_counts_scope_transaction_and_close():
    adapter = FakeAdapter([opportunity("1"), opportunity("2"), opportunity("3")])
    ingestion = FakeIngestion(["CREATED", "UPDATED", "EXISTING"])
    db = FakeSession()
    factory_calls = []
    service = FreelancerDiscoveryService(
        settings(),
        adapter_factory=lambda token, sandbox: factory_calls.append((bool(token), sandbox)) or adapter,
        ingestion_service=ingestion,
    )

    result = await service.sync(db, query="python", skills=["FastAPI"], limit=25)

    assert result["created"] == result["updated"] == result["existing"] == 1
    assert result["skipped"] == result["failed"] == 0
    assert result["state"] == "success"
    assert ingestion.profile_ids == [PROFILE_ID, PROFILE_ID, PROFILE_ID]
    assert db.commits == 1 and db.rollbacks == 0 and db.savepoints == 3
    assert adapter.closed is True
    assert adapter.calls == [{"query": "python", "skills": ["FastAPI"], "limit": 25}]
    assert factory_calls == [(True, True)]


@pytest.mark.asyncio
async def test_partial_malformed_and_failed_records_are_isolated():
    malformed = NormalizedMarketplaceOpportunity(platform="freelancer", platform_job_id="bad", title="", description="missing title")
    adapter = FakeAdapter([opportunity("1"), malformed, opportunity("2")], skipped=1)
    ingestion = FakeIngestion(["CREATED", RuntimeError("row failure")])
    db = FakeSession()
    service = FreelancerDiscoveryService(settings(), adapter_factory=lambda *_: adapter, ingestion_service=ingestion)

    result = await service.sync(db, query=None, skills=[], limit=10)

    assert result["created"] == 1
    assert result["skipped"] == 2
    assert result["failed"] == 1
    assert result["state"] == "partial_failure"
    assert db.commits == 1
    assert adapter.closed is True


@pytest.mark.asyncio
async def test_missing_token_does_not_construct_adapter_or_touch_database():
    constructed = []
    db = FakeSession()
    service = FreelancerDiscoveryService(settings(token=""), adapter_factory=lambda *_: constructed.append(True))

    assert service.connection_status().state == "not_configured"
    with pytest.raises(FreelancerNotConfiguredError):
        await service.sync(db, query=None, skills=[], limit=10)
    assert constructed == []
    assert db.commits == db.rollbacks == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("upstream_error", [FreelancerUnauthorized("bad"), FreelancerRateLimited("slow"), FreelancerTimeout("late")])
async def test_upstream_failure_rolls_back_and_always_closes(upstream_error):
    adapter = FakeAdapter(error=upstream_error)
    db = FakeSession()
    service = FreelancerDiscoveryService(settings(), adapter_factory=lambda *_: adapter)

    with pytest.raises(type(upstream_error)):
        await service.sync(db, query=None, skills=[], limit=10)
    assert db.rollbacks == 1 and db.commits == 0
    assert adapter.closed is True


def test_status_or_service_construction_never_creates_marketplace_client():
    constructed = []
    service = FreelancerDiscoveryService(settings(), adapter_factory=lambda *_: constructed.append(True))
    status = service.connection_status()
    assert status.state == "configured"
    assert constructed == []


def test_sync_request_validates_query_skills_and_limit():
    request = freelancing_router.FreelancerSyncRequest(query="  python   api ", skills=[" FastAPI "], limit=50)
    assert request.query == "python api" and request.skills == ["FastAPI"]
    for payload in (
        {"query": "x" * 201, "limit": 10},
        {"skills": ["x" * 65], "limit": 10},
        {"skills": ["x"] * 21, "limit": 10},
        {"limit": 0},
        {"limit": 51},
    ):
        with pytest.raises(ValidationError):
            freelancing_router.FreelancerSyncRequest(**payload)


def test_connection_and_sync_routes_require_admin_dependency():
    protected = {
        "/api/freelancing/freelancer/connection/status",
        "/api/freelancing/freelancer/sync",
        "/api/freelancing/freelancer/sync/summary",
    }
    for route in freelancing_router.router.routes:
        if route.path not in protected:
            continue
        dependencies = {dependency.call for dependency in route.dependant.dependencies}
        assert require_admin_user in dependencies


@pytest.mark.asyncio
async def test_admin_boundary_rejects_non_admin_and_accepts_configured_admin(monkeypatch):
    monkeypatch.setattr("app.routers.auth.settings.ADMIN_USER_EMAIL", "admin@example.test")
    with pytest.raises(HTTPException) as denied:
        await require_admin_user(SimpleNamespace(email="member@example.test", plan="free"))
    assert denied.value.status_code == 403
    with pytest.raises(HTTPException):
        await require_admin_user(SimpleNamespace(email="admin@example.test", plan="free"))
    admin = SimpleNamespace(email="ADMIN@example.test", plan="admin")
    assert await require_admin_user(admin) is admin


class FailingRouterService:
    def __init__(self, error):
        self.error = error
        self.error_code = None

    async def sync(self, *args, **kwargs):
        raise self.error

    def record_upstream_error(self, code):
        self.error_code = code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error,status_code,error_code",
    [
        (FreelancerUnauthorized("bad"), 502, "upstream_unauthorized"),
        (FreelancerRateLimited("slow"), 503, "upstream_rate_limited"),
        (FreelancerTimeout("late"), 504, "upstream_timeout"),
    ],
)
async def test_router_maps_upstream_errors_without_leaking_credentials(monkeypatch, error, status_code, error_code):
    service = FailingRouterService(error)
    monkeypatch.setattr(freelancing_router, "_freelancer_discovery_service", service)
    with pytest.raises(HTTPException) as response:
        await freelancing_router.sync_freelancer_opportunities(
            freelancing_router.FreelancerSyncRequest(),
            current_user=SimpleNamespace(email="admin@example.test"),
            db=FakeSession(),
        )
    assert response.value.status_code == status_code
    assert response.value.detail["code"] == error_code
    assert service.error_code == error_code
    assert "token" not in json.dumps(response.value.detail).lower()


@pytest.mark.asyncio
async def test_router_maps_missing_configuration(monkeypatch):
    service = FailingRouterService(FreelancerNotConfiguredError("not configured"))
    monkeypatch.setattr(freelancing_router, "_freelancer_discovery_service", service)
    with pytest.raises(HTTPException) as response:
        await freelancing_router.sync_freelancer_opportunities(
            freelancing_router.FreelancerSyncRequest(),
            current_user=SimpleNamespace(email="admin@example.test"),
            db=FakeSession(),
        )
    assert response.value.status_code == 503
    assert response.value.detail["code"] == "not_configured"


@pytest.mark.asyncio
async def test_success_responses_never_contain_token():
    adapter = FakeAdapter([opportunity("1")])
    service = FreelancerDiscoveryService(settings(token="super-secret-value"), adapter_factory=lambda *_: adapter, ingestion_service=FakeIngestion(["CREATED"]))
    result = await service.sync(FakeSession(), query=None, skills=[], limit=10)
    payload = json.dumps({"summary": result, "status": service.connection_status().__dict__})
    assert "super-secret-value" not in payload
    assert "token" not in payload.lower()
