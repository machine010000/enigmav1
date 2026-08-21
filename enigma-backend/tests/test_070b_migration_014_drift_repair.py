"""Isolated migration-014 drift reconciliation tests for TASK-070B."""
from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


VERSIONS = Path(__file__).parents[1] / "alembic" / "versions"


def migration(number: str):
    path = next(VERSIONS.glob(f"{number}_*.py"))
    spec = importlib.util.spec_from_file_location(f"task_070b_{number}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_upgrade(module, connection):
    module.op = Operations(MigrationContext.configure(connection))
    module.upgrade()


def chat_metadata(*, all_indexes: bool = True, omit_active_project: bool = False, incompatible_title: bool = False):
    metadata = sa.MetaData()
    conversations = sa.Table(
        "freelancer_conversations", metadata,
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("title", sa.Integer if incompatible_title else sa.String(300), nullable=False),
        *([] if omit_active_project else [sa.Column("active_project_id", sa.String(64))]),
        sa.Column("metadata", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    messages = sa.Table(
        "freelancer_chat_messages", metadata,
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("freelancer_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(64)),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("intent", sa.String(50)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("structured_data", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    artifacts = sa.Table(
        "freelancer_project_artifacts", metadata,
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(64)),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("visibility", sa.String(30), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("source_message_id", sa.String(64), sa.ForeignKey("freelancer_chat_messages.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    if all_indexes:
        sa.Index("ix_freelancer_conversations_user_updated", conversations.c.user_id, conversations.c.updated_at)
        sa.Index("ix_freelancer_conversations_profile", conversations.c.profile_id)
        sa.Index("ix_freelancer_messages_conversation_created", messages.c.conversation_id, messages.c.created_at)
        sa.Index("uq_freelancer_messages_conversation_sequence", messages.c.conversation_id, messages.c.sequence, unique=True)
        sa.Index("ix_freelancer_messages_user_project", messages.c.user_id, messages.c.project_id)
        sa.Index("ix_freelancer_artifacts_user_project_type", artifacts.c.user_id, artifacts.c.project_id, artifacts.c.artifact_type)
        sa.Index("ix_freelancer_artifacts_visibility_type", artifacts.c.user_id, artifacts.c.visibility, artifacts.c.artifact_type)
        sa.Index("uq_freelancer_artifact_version", artifacts.c.user_id, artifacts.c.project_id, artifacts.c.artifact_type, artifacts.c.version, unique=True)
    return metadata, conversations, messages, artifacts


def assert_schema(connection):
    inspector = sa.inspect(connection)
    assert {name for name, _ in migration("014")._TABLES} <= set(inspector.get_table_names())
    for table, indexes in migration("014")._INDEXES.items():
        reflected = {item["name"]: item for item in inspector.get_indexes(table)}
        for name, (columns, unique) in indexes.items():
            assert tuple(reflected[name]["column_names"]) == columns
            assert bool(reflected[name]["unique"]) is unique
    assert inspector.get_foreign_keys("freelancer_chat_messages")[0]["options"]["ondelete"] == "CASCADE"
    assert inspector.get_foreign_keys("freelancer_project_artifacts")[0]["options"]["ondelete"] == "SET NULL"


def test_clean_013_to_014_and_round_trip():
    module = migration("014")
    with sa.create_engine("sqlite:///:memory:").begin() as connection:
        run_upgrade(module, connection)
        assert_schema(connection)
        run_upgrade(module, connection)
        module.op = Operations(MigrationContext.configure(connection))
        module.downgrade()
        assert "freelancer_conversations" not in sa.inspect(connection).get_table_names()
        run_upgrade(module, connection)
        assert_schema(connection)


def test_preexisting_conversations_only_is_reused():
    metadata, conversations, _, _ = chat_metadata()
    isolated = sa.MetaData()
    conversations.to_metadata(isolated)
    with sa.create_engine("sqlite:///:memory:").begin() as connection:
        isolated.create_all(connection)
        run_upgrade(migration("014"), connection)
        assert_schema(connection)


def test_all_compatible_create_all_tables_and_data_are_preserved():
    metadata, conversations, messages, artifacts = chat_metadata()
    now = datetime(2026, 1, 1)
    with sa.create_engine("sqlite:///:memory:").begin() as connection:
        metadata.create_all(connection)
        connection.execute(conversations.insert().values(id="c1", profile_id="enigma_profile", user_id="u1", title="Keep", metadata={}, created_at=now, updated_at=now))
        connection.execute(messages.insert().values(id="m1", conversation_id="c1", profile_id="enigma_profile", user_id="u1", role="user", sequence=1, content="Keep message", structured_data={}, created_at=now))
        connection.execute(artifacts.insert().values(id="a1", profile_id="enigma_profile", user_id="u1", artifact_type="sample", visibility="project_private", version=1, content="Keep artifact", data={}, source_message_id="m1", created_at=now))
        run_upgrade(migration("014"), connection)
        assert connection.execute(sa.select(conversations.c.title)).scalar_one() == "Keep"
        assert connection.execute(sa.select(messages.c.content)).scalar_one() == "Keep message"
        assert connection.execute(sa.select(artifacts.c.content)).scalar_one() == "Keep artifact"
        assert_schema(connection)


def test_partial_empty_schema_adds_nullable_column_and_missing_indexes():
    metadata, _, _, _ = chat_metadata(all_indexes=False, omit_active_project=True)
    with sa.create_engine("sqlite:///:memory:").begin() as connection:
        metadata.create_all(connection)
        run_upgrade(migration("014"), connection)
        columns = {item["name"] for item in sa.inspect(connection).get_columns("freelancer_conversations")}
        assert "active_project_id" in columns
        assert_schema(connection)


def test_incompatible_existing_object_fails_without_deleting_data():
    metadata, conversations, _, _ = chat_metadata(incompatible_title=True)
    now = datetime(2026, 1, 1)
    with sa.create_engine("sqlite:///:memory:").begin() as connection:
        metadata.create_all(connection)
        connection.execute(conversations.insert().values(id="c1", profile_id="enigma_profile", user_id="u1", title=7, metadata={}, created_at=now, updated_at=now))
        with pytest.raises(RuntimeError, match="freelancer_conversations.title has type INTEGER"):
            run_upgrade(migration("014"), connection)
        assert connection.execute(sa.select(sa.func.count()).select_from(conversations)).scalar_one() == 1


def test_unique_index_repair_fails_closed_when_duplicates_exist():
    metadata, conversations, messages, _ = chat_metadata(all_indexes=False)
    now = datetime(2026, 1, 1)
    with sa.create_engine("sqlite:///:memory:").begin() as connection:
        metadata.create_all(connection)
        connection.execute(conversations.insert().values(id="c1", profile_id="p", user_id="u", title="T", metadata={}, created_at=now, updated_at=now))
        for identifier in ("m1", "m2"):
            connection.execute(messages.insert().values(id=identifier, conversation_id="c1", profile_id="p", user_id="u", role="user", sequence=1, content=identifier, structured_data={}, created_at=now))
        with pytest.raises(RuntimeError, match="uq_freelancer_messages_conversation_sequence"):
            run_upgrade(migration("014"), connection)
        assert connection.execute(sa.select(sa.func.count()).select_from(messages)).scalar_one() == 2


def test_full_009_through_014_chain_uses_reconciled_head():
    path = Path(__file__).with_name("test_070a_migration_drift_repair.py")
    spec = importlib.util.spec_from_file_location("task_070a_helpers", path)
    helpers = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(helpers)

    with helpers.engine().begin() as connection:
        helpers.revision_009_schema(connection)
        for number in ("010", "011", "012", "013", "014"):
            run_upgrade(migration(number), connection)
        assert_schema(connection)
