from datetime import datetime
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.creativity.ai_service import CreativeTaskResult
from app.freelancing.manual_intake import DuplicateOpportunityError, ManualOpportunityStateError
from app.freelancing.project_chat import (
    FreelancerChatService,
    FreelancerIntentRouter,
    FreelancerProjectResolver,
    PROFILE_ID,
)
from app.models.freelancer_chat import (
    FreelancerChatMessage,
    FreelancerConversation,
    FreelancerProjectArtifact,
)
from app.models.marketplace import MarketplaceJob
from app.routers import freelancer_chat as chat_router
from app.routers.freelancer_chat import ChatRequest, OpportunityInput
from app.routers import freelancing as manual_router
from app.routers.freelancing import ManualOpportunityCreate
from app.routers.auth import require_admin_user


def project(job_id="project-a", title="Store Dashboard", user_id="user-a", client="Ahmed"):
    return MarketplaceJob(
        profile_id=PROFILE_ID, job_id=job_id, platform="upwork", platform_job_id=job_id,
        title=title, description="Editable normalized description", original_text="IMMUTABLE SOURCE",
        normalized_requirements={"requirements": ["FastAPI"]}, skills_required=["Python"],
        client_info={"name": client}, ingestion_source="manual", lifecycle_status="draft",
        created_by_user_id=user_id, currency="USD", job_metadata={},
    )


@pytest.mark.parametrize(("message", "intent"), [
    ("record loss for Store Dashboard", "record_loss"),
    ("فزنا بالمشروع", "record_win"),
    ("save this example", "add_sample"),
    ("اكتبلي عرض للمشروع", "proposal_request"),
    ("draft a reply", "client_reply_request"),
    ("client replied and said hello", "client_message"),
    ("study FastAPI capability gap", "learning_request"),
    ("switch project Store Dashboard", "project_switch"),
    ("analyze this project", "opportunity_analysis"),
    ("client requires a new feature", "project_requirement"),
    ("create an execution plan", "project_work"),
    ("hello", "general_freelancer_chat"),
])
def test_intent_routing(message, intent):
    assert FreelancerIntentRouter.classify(message) == intent


def test_long_pasted_opportunity_detected_even_with_active_project():
    pasted = "Job description budget skills " + ("build a secure API " * 20)
    assert FreelancerIntentRouter.classify(pasted, has_active_project=True) == "new_opportunity"


@pytest.mark.asyncio
async def test_project_resolution_selects_owned_metadata_and_preserves_isolation(monkeypatch):
    resolver = FreelancerProjectResolver()
    owned = [project(), project("project-b", "Marketing Site", client="Sara")]
    monkeypatch.setattr(resolver, "_projects", AsyncMock(return_value=owned))
    conversation = SimpleNamespace(active_project_id=None)
    result = await resolver.resolve(None, user_id="user-a", message="كمل مشروع Store Dashboard", conversation=conversation)
    assert result.selected_project_id == "project-a"
    assert not result.ambiguity


@pytest.mark.asyncio
async def test_project_resolution_refuses_ambiguous_reference(monkeypatch):
    resolver = FreelancerProjectResolver()
    owned = [project("a", "Store API"), project("b", "Store Web")]
    monkeypatch.setattr(resolver, "_projects", AsyncMock(return_value=owned))
    result = await resolver.resolve(None, user_id="user-a", message="continue store project", conversation=SimpleNamespace(active_project_id=None))
    assert result.selected_project_id is None
    assert result.ambiguity
    assert {item["project_id"] for item in result.candidate_projects} == {"a", "b"}


@pytest.mark.asyncio
async def test_explicit_foreign_project_is_not_selected(monkeypatch):
    resolver = FreelancerProjectResolver()
    monkeypatch.setattr(resolver, "_projects", AsyncMock(return_value=[project()]))
    result = await resolver.resolve(None, user_id="user-a", message="work", conversation=SimpleNamespace(active_project_id=None), explicit_project_id="user-b-project")
    assert result.selected_project_id is None
    assert result.confidence == 0.0


class FakeGateway:
    async def generate(self, *, system, user, **_kwargs):
        if "proposal" in system.lower():
            return {"proposal_text": "Grounded proposal", "confidence": 0.9, "risks": [], "missing_information": []}
        if "client requirements" in system.lower():
            return {"response": "Recommended reply", "requirements": ["API"], "questions": [], "missing_clarification": [], "new_tasks": ["API task"]}
        if "client reply" in system.lower():
            return {"response": "Manual reply draft", "risks": [], "missing_clarification": []}
        if "execution" in system.lower():
            return {"summary": "Execution plan", "steps": ["Build"], "risks": [], "missing_information": [], "confidence": 0.9}
        if "opportunity" in system.lower() or "suitability" in system.lower():
            return {"summary": "Good fit", "required_skills": ["Python"], "suitability_score": 0.9, "recommendation": "apply", "reasoning": "Relevant skill", "risks": [], "missing_information": []}
        return {"response": "General response", "next_action": None}


class FakeManualIntake:
    def __init__(self):
        self.jobs = {}

    async def create(self, _db, *, actor_id, data, analyze=False):
        item = project(f"project-{len(self.jobs) + 1}", data["title"], actor_id)
        item.platform = data["platform"]
        item.description = data["original_description"]
        item.original_text = data["original_description"]
        item.normalized_requirements = data["normalized_requirements"]
        self.jobs[item.job_id] = item
        return item

    async def update_outcome(self, _db, *, job, outcome, notes):
        if not getattr(job, "has_submission", False):
            raise ManualOpportunityStateError("Manual submission snapshot does not exist")
        job.lifecycle_status = outcome
        return SimpleNamespace(outcome_status=outcome)


class MemoryChatService(FreelancerChatService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.artifacts = []
        self.messages = []

    async def _artifact(self, _db, *, user_id, project_id, artifact_type, content, data, visibility="project_private", source_message_id=None):
        version = 1 + max((item.version for item in self.artifacts if item.user_id == user_id and item.project_id == project_id and item.artifact_type == artifact_type), default=0)
        item = SimpleNamespace(id=f"artifact-{len(self.artifacts) + 1}", user_id=user_id, project_id=project_id, artifact_type=artifact_type, content=content, artifact_data=data, visibility=visibility, version=version, source_message_id=source_message_id, created_at=datetime.utcnow())
        self.artifacts.append(item)
        return item

    async def _latest_artifact(self, _db, user_id, project_id, artifact_type):
        found = [item for item in self.artifacts if item.user_id == user_id and item.project_id == project_id and item.artifact_type == artifact_type]
        return max(found, key=lambda item: item.version) if found else None

    async def _store_message(self, _db, conversation_id, user_id, project_id, role, intent, content, structured):
        sequence = 1 + max((message.sequence for message in self.messages if message.conversation_id == conversation_id), default=0)
        item = SimpleNamespace(id=f"message-{len(self.messages) + 1}", conversation_id=conversation_id, user_id=user_id, project_id=project_id, role=role, sequence=sequence, intent=intent, content=content, structured_data=structured, created_at=datetime.utcnow())
        self.messages.append(item)
        return item

    async def samples(self, _db, *, user_id, project_id):
        return [self._artifact_dict(item) for item in self.artifacts if item.user_id == user_id and item.artifact_type == "sample" and (item.visibility == "reusable_global" or item.project_id == project_id)]


def service():
    creativity = AsyncMock()
    creativity.generate.return_value = CreativeTaskResult(
        ideas=[{"title": "Angle", "approach": "Grounded", "benefit": "Clear"}],
        alternative_approaches=["Alternative"], proposal_angles=["Outcome focus"],
        risks=[], confidence=0.9, rationale="Use relevant experience",
    )
    academy = AsyncMock()
    academy.learn.return_value = SimpleNamespace(
        knowledge_summary="Learned FastAPI", knowledge_id="knowledge-1",
        to_dict=lambda: {"knowledge_summary": "Learned FastAPI", "knowledge_id": "knowledge-1", "confidence": 0.9},
    )
    return MemoryChatService(ai_gateway=FakeGateway(), creativity=creativity, academy=academy, manual_intake=FakeManualIntake())


class AsyncSessionFacade:
    def __init__(self, session):
        self.session = session

    def add(self, value):
        self.session.add(value)

    async def scalar(self, statement):
        return self.session.scalar(statement)

    async def execute(self, statement):
        return self.session.execute(statement)

    async def flush(self):
        self.session.flush()

    async def rollback(self):
        self.session.rollback()


@pytest.mark.asyncio
async def test_pasted_opportunity_preserves_immutable_text_and_structured_analysis(monkeypatch):
    chat = service()
    monkeypatch.setattr("app.freelancing.project_chat.master_brain.decide_capability", lambda *_args, **_kwargs: SimpleNamespace(capability=None))
    conversation = SimpleNamespace(id="conversation-1", active_project_id=None, updated_at=None)
    original = "Job description budget skills " + ("do not alter this source " * 12)
    result = await chat._new_opportunity(None, conversation, "user-a", original, {"title": "Secure API", "platform": "upwork"})
    saved = chat.manual_intake.jobs[result["project_id"]]
    assert saved.original_text == original
    assert result["result"]["recommendation"] == "apply"
    assert result["result"]["product_verification"]["recommendation"] == "pass"
    assert all(item.project_id == saved.job_id for item in chat.artifacts)


@pytest.mark.asyncio
async def test_proposals_are_versioned_and_creativity_verification_are_used():
    chat = service()
    item = project()
    first = await chat._proposal(None, "user-a", item, "write proposal", "proposal_request")
    second = await chat._proposal(None, "user-a", item, "revise proposal", "proposal_request")
    assert first["data"]["proposal_version"] == 1
    assert second["data"]["proposal_version"] == 2
    assert first["data"]["manual_copy_only"] is True
    assert first["data"]["verification"]["recommendation"] == "pass"
    assert chat.creativity.generate.await_count == 2


@pytest.mark.asyncio
async def test_client_message_and_reply_are_immutable_project_artifacts():
    chat = service()
    item = project()
    await chat._client_message(None, "user-a", item, "client said add OAuth", "client_message")
    reply = await chat._client_reply(None, "user-a", item, "draft a reply", "client_reply_request")
    original = next(value for value in chat.artifacts if value.artifact_type == "client_message")
    assert original.content == "client said add OAuth"
    assert original.artifact_data["immutable"] is True
    assert reply["data"]["manual_send_only"] is True


@pytest.mark.asyncio
async def test_academy_learning_has_governed_id_and_durable_project_link(monkeypatch):
    chat = service()
    monkeypatch.setattr("app.freelancing.project_chat.master_brain.decide_capability", lambda *_args, **_kwargs: SimpleNamespace(capability="academy_learning"))
    result = await chat._learning(None, "user-a", project(), "study FastAPI", "learning_request")
    stored = next(value for value in chat.artifacts if value.artifact_type == "academy_learning")
    assert result["data"]["knowledge_id"] == "knowledge-1"
    assert stored.project_id == "project-a"
    assert stored.visibility == "project_private"
    chat.academy.learn.assert_awaited_once_with(topic="Store Dashboard", task="study FastAPI", capability_gap=None, store=True)


@pytest.mark.asyncio
async def test_samples_are_user_scoped_and_only_explicit_global_samples_cross_projects():
    chat = service()
    await chat._artifact(None, user_id="user-a", project_id="project-a", artifact_type="sample", content="private A", data={}, visibility="project_private")
    await chat._artifact(None, user_id="user-a", project_id="project-a", artifact_type="sample", content="global A", data={}, visibility="reusable_global")
    await chat._artifact(None, user_id="user-b", project_id="project-b", artifact_type="sample", content="foreign", data={}, visibility="reusable_global")
    visible = await chat.samples(None, user_id="user-a", project_id="project-b")
    assert [item["content"] for item in visible] == ["global A"]


@pytest.mark.asyncio
async def test_project_a_artifacts_never_appear_in_project_b_lookup():
    chat = service()
    await chat._artifact(None, user_id="user-a", project_id="project-a", artifact_type="client_message", content="A secret", data={})
    assert await chat._latest_artifact(None, "user-a", "project-b", "client_message") is None
    await chat._proposal(None, "user-a", project("project-b", "Other Project"), "proposal", "proposal_request")
    assert all(item.project_id == "project-b" for item in chat.artifacts if item.artifact_type == "proposal_draft")


@pytest.mark.asyncio
async def test_outcome_cannot_bypass_manual_submission_safeguards():
    chat = service()
    result = await chat._outcome(None, "user-a", project(), "record win", "record_win")
    assert result["data"]["status"] == "blocked"
    assert result["data"]["outcome"] == "won"


@pytest.mark.asyncio
async def test_conversation_and_active_project_restore_after_service_restart(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    MarketplaceJob.__table__.create(engine)
    FreelancerConversation.__table__.create(engine)
    FreelancerChatMessage.__table__.create(engine)
    FreelancerProjectArtifact.__table__.create(engine)
    creativity = AsyncMock()
    creativity.generate.return_value = CreativeTaskResult(proposal_angles=["Angle"], confidence=0.9)
    academy = AsyncMock()
    monkeypatch.setattr("app.freelancing.project_chat.master_brain.decide_capability", lambda *_args, **_kwargs: SimpleNamespace(capability=None))

    with Session(engine) as sync_db:
        db = AsyncSessionFacade(sync_db)
        first_service = FreelancerChatService(ai_gateway=FakeGateway(), creativity=creativity, academy=academy)
        created = await first_service.handle(
            db, user_id="user-a", message="Job description budget skills " + ("secure API " * 20),
            opportunity={"title": "Restart-safe API", "platform": "upwork"},
        )
        sync_db.commit()
        conversation_id = created["conversation_id"]
        project_id = created["project_id"]

    with Session(engine) as restarted_db:
        second_service = FreelancerChatService(ai_gateway=FakeGateway(), creativity=creativity, academy=academy)
        restored = await second_service.conversation(
            AsyncSessionFacade(restarted_db), user_id="user-a", conversation_id=conversation_id,
        )
        assert restored["active_project_id"] == project_id
        assert [message["role"] for message in restored["messages"]] == ["user", "assistant"]
        assert all(message["project_id"] == project_id for message in restored["messages"])


@pytest.mark.asyncio
async def test_two_persisted_projects_keep_messages_and_proposals_isolated(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    MarketplaceJob.__table__.create(engine)
    FreelancerConversation.__table__.create(engine)
    FreelancerChatMessage.__table__.create(engine)
    FreelancerProjectArtifact.__table__.create(engine)
    creativity = AsyncMock()
    creativity.generate.return_value = CreativeTaskResult(proposal_angles=["Angle"], confidence=0.9)
    academy = AsyncMock()
    monkeypatch.setattr("app.freelancing.project_chat.master_brain.decide_capability", lambda *_args, **_kwargs: SimpleNamespace(capability=None))
    chat = FreelancerChatService(ai_gateway=FakeGateway(), creativity=creativity, academy=academy)
    with Session(engine) as sync_db:
        db = AsyncSessionFacade(sync_db)
        a = await chat.handle(db, user_id="user-a", message="A", opportunity={"title": "Project Alpha", "platform": "upwork"})
        b = await chat.handle(db, user_id="user-a", message="B", opportunity={"title": "Project Beta", "platform": "freelancer"})
        await chat.handle(db, user_id="user-a", message="write proposal", conversation_id=a["conversation_id"], project_id=a["project_id"])
        await chat.handle(db, user_id="user-a", message="client said add OAuth", conversation_id=b["conversation_id"], project_id=b["project_id"])
        sync_db.commit()
        rows = sync_db.query(FreelancerProjectArtifact).all()
        proposals_a = [row for row in rows if row.project_id == a["project_id"] and row.artifact_type == "proposal_draft"]
        messages_b = [row for row in rows if row.project_id == b["project_id"] and row.artifact_type == "client_message"]
        assert len(proposals_a) == 1 and proposals_a[0].project_id != b["project_id"]
        assert len(messages_b) == 1 and messages_b[0].project_id != a["project_id"]


def test_persistence_schema_and_router_security_contract():
    assert FreelancerConversation.__tablename__ == "freelancer_conversations"
    assert FreelancerChatMessage.__tablename__ == "freelancer_chat_messages"
    assert FreelancerProjectArtifact.__tablename__ == "freelancer_project_artifacts"
    paths = {route.path: route for route in chat_router.router.routes}
    assert set(paths) == {"/api/freelancing/chat", "/api/freelancing/chat/conversations/{conversation_id}", "/api/freelancing/chat/projects", "/api/freelancing/chat/samples"}
    assert all(any(dependency.call is require_admin_user for dependency in route.dependant.dependencies) for route in paths.values())


def test_migration_014_is_linear_reversible_and_contains_only_chat_tables():
    source = (Path(__file__).parents[1] / "alembic/versions/014_project_aware_freelancer_chat.py").read_text(encoding="utf-8")
    assert 'down_revision = "013_runtime_url_canonical_dedupe"' in source
    for table in ("freelancer_conversations", "freelancer_chat_messages", "freelancer_project_artifacts"):
        assert f'"{table}"' in source
        assert f'op.drop_table("{table}")' in source
    assert "marketplace_jobs" not in source


def test_migration_014_upgrade_downgrade_upgrade_on_isolated_database(monkeypatch):
    path = Path(__file__).parents[1] / "alembic/versions/014_project_aware_freelancer_chat.py"
    spec = importlib.util.spec_from_file_location("migration_014_chat", path)
    migration = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(migration, "op", operations)
        migration.upgrade()
        assert {"freelancer_conversations", "freelancer_chat_messages", "freelancer_project_artifacts"} <= set(inspect(connection).get_table_names())
        migration.downgrade()
        assert "freelancer_conversations" not in inspect(connection).get_table_names()
        migration.upgrade()
        assert "freelancer_project_artifacts" in inspect(connection).get_table_names()


def test_chat_service_never_commits_or_submits_externally():
    source = (Path(__file__).parents[1] / "app/freelancing/project_chat.py").read_text(encoding="utf-8")
    assert ".commit(" not in source
    assert "requests." not in source and "httpx." not in source
    assert "record_submission(" not in source


@pytest.mark.asyncio
async def test_http_boundary_owns_one_commit(monkeypatch):
    fake_service = SimpleNamespace(handle=AsyncMock(return_value={"conversation_id": "c"}))
    monkeypatch.setattr(chat_router, "service", fake_service)
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    result = await chat_router.chat(ChatRequest(message="hello"), SimpleNamespace(id="user-a"), db)
    assert result == {"conversation_id": "c"}
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_http_boundary_rolls_back_failed_multi_step_chat(monkeypatch):
    fake_service = SimpleNamespace(handle=AsyncMock(side_effect=RuntimeError("AI failed")))
    monkeypatch.setattr(chat_router, "service", fake_service)
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    with pytest.raises(RuntimeError, match="AI failed"):
        await chat_router.chat(ChatRequest(message="hello"), SimpleNamespace(id="user-a"), db)
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


def test_optional_opportunity_payload_rejects_invalid_budget():
    with pytest.raises(ValueError):
        OpportunityInput(title="Job", budget_min=200, budget_max=100)


@pytest.mark.asyncio
async def test_chat_sample_is_project_private_by_default_and_user_scoped():
    chat = service()
    project_a = project("project-a", "Accounting API", "user-a")
    chat._owned_project = AsyncMock(return_value=project_a)
    result = await chat._add_sample_from_chat(
        None, "user-a", project_a, "save this example", "add_sample",
    )
    assert result["data"]["visibility"] == "project_private"
    assert [item["content"] for item in await chat.samples(None, user_id="user-a", project_id="project-a")] == ["save this example"]
    assert await chat.samples(None, user_id="user-a", project_id="project-b") == []
    assert await chat.samples(None, user_id="user-b", project_id="project-a") == []


@pytest.mark.parametrize("message", [
    "make this reusable across projects",
    "use this example in future projects",
    "خزن المثال ده كخبرة عامة",
    "استخدم المثال ده في المشاريع المستقبلية",
])
@pytest.mark.asyncio
async def test_explicit_promotion_makes_sample_reusable_for_same_user_only(message):
    chat = service()
    project_a = project("project-a", "Accounting API", "user-a")
    chat._owned_project = AsyncMock(return_value=project_a)
    assert FreelancerIntentRouter.classify(message) == "add_sample"
    result = await chat._add_sample_from_chat(None, "user-a", project_a, message, "add_sample")
    assert result["data"]["visibility"] == "reusable_global"
    assert len(await chat.samples(None, user_id="user-a", project_id="project-b")) == 1
    assert await chat.samples(None, user_id="user-b", project_id="project-b") == []


@pytest.mark.asyncio
async def test_relevant_samples_require_positive_score_after_scope_filtering():
    chat = service()
    await chat._artifact(None, user_id="user-a", project_id="project-a", artifact_type="sample", content="FastAPI OAuth success", data={"skills": ["FastAPI"]}, visibility="project_private")
    await chat._artifact(None, user_id="user-a", project_id="project-a", artifact_type="sample", content="Unrelated watercolor painting", data={}, visibility="project_private")
    await chat._artifact(None, user_id="user-a", project_id="project-b", artifact_type="sample", content="FastAPI foreign private", data={}, visibility="project_private")
    await chat._artifact(None, user_id="user-a", project_id="project-b", artifact_type="sample", content="Reusable FastAPI delivery", data={}, visibility="reusable_global")
    await chat._artifact(None, user_id="user-b", project_id="foreign", artifact_type="sample", content="FastAPI other user", data={}, visibility="reusable_global")
    relevant = await chat._relevant_samples(None, user_id="user-a", project_id="project-a", context="Build a FastAPI service")
    assert [item["content"] for item in relevant] == ["FastAPI OAuth success", "Reusable FastAPI delivery"]
    assert await chat._relevant_samples(None, user_id="user-a", project_id="project-a", context="quantum chemistry") == []


@pytest.mark.asyncio
async def test_chat_and_manual_intake_share_duplicate_http_contract(monkeypatch):
    duplicate = DuplicateOpportunityError("existing-job")
    monkeypatch.setattr(chat_router, "service", SimpleNamespace(handle=AsyncMock(side_effect=duplicate)))
    chat_db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    with pytest.raises(HTTPException) as chat_error:
        await chat_router.chat(ChatRequest(message="duplicate opportunity"), SimpleNamespace(id="user-a"), chat_db)

    monkeypatch.setattr(manual_router._manual_intake_service, "create", AsyncMock(side_effect=DuplicateOpportunityError("existing-job")))
    manual_db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock(), refresh=AsyncMock())
    request = ManualOpportunityCreate(
        platform="upwork", title="Duplicate", original_description="Original",
        currency="USD", source_language="en", customer_preferred_language="en",
        proposal_language="en", analyze=False,
    )
    with pytest.raises(HTTPException) as manual_error:
        await manual_router.create_manual_opportunity(request, SimpleNamespace(id="user-a"), manual_db)

    expected = {"code": "duplicate_opportunity", "existing_job_id": "existing-job"}
    assert chat_error.value.status_code == manual_error.value.status_code == 409
    assert chat_error.value.detail == manual_error.value.detail == expected
    chat_db.rollback.assert_awaited_once()
    manual_db.rollback.assert_awaited_once()
