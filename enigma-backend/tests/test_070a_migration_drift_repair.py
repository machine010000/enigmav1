"""Isolated schema-drift tests for TASK-070A."""
from __future__ import annotations

import hashlib
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
    spec = importlib.util.spec_from_file_location(f"task_070a_{number}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def engine():
    result = sa.create_engine("sqlite:///:memory:")

    @sa.event.listens_for(result, "connect")
    def add_md5(dbapi_connection, _connection_record):
        dbapi_connection.create_function(
            "md5", 1,
            lambda value: hashlib.md5(str(value).encode(), usedforsecurity=False).hexdigest(),
        )

    return result


def revision_009_schema(connection, *, include_010_columns: bool = False):
    metadata = sa.MetaData()
    columns = [
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("profile_id", sa.String, nullable=False),
        sa.Column("job_id", sa.String, nullable=False),
        sa.Column("platform", sa.String, nullable=False),
        sa.Column("platform_job_id", sa.String),
        sa.Column("title", sa.String),
        sa.Column("description", sa.Text),
        sa.Column("client_info", sa.JSON),
        sa.Column("url", sa.String),
        sa.Column("metadata", sa.JSON),
        sa.Column("identity_fingerprint", sa.String(64)),
        sa.Column("ingestion_source", sa.String(100)),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    ]
    if include_010_columns:
        columns.extend([
            sa.Column("original_text", sa.Text),
            sa.Column("normalized_requirements", sa.JSON),
            sa.Column("source_language", sa.String(10)),
            sa.Column("customer_preferred_language", sa.String(10)),
            sa.Column("proposal_language", sa.String(10)),
            sa.Column("translation_metadata", sa.JSON),
            sa.Column("created_by_user_id", sa.String(64)),
        ])
    jobs = sa.Table("marketplace_jobs", metadata, *columns)
    if include_010_columns:
        sa.Index("ix_marketplace_jobs_created_by_user_id", jobs.c.created_by_user_id)
    metadata.create_all(connection)
    return jobs


def compatible_submission_table(
    connection, *, include_011_columns: bool = False, incompatible_snapshot: bool = False
):
    metadata = sa.MetaData()
    table = sa.Table(
        "manual_opportunity_submissions", metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.String, nullable=False),
        sa.Column("job_id", sa.String, nullable=False),
        sa.Column("created_by_user_id", sa.String(64), nullable=False),
        sa.Column("marketplace_proposal_id", sa.String(200)),
        sa.Column("submitted_at", sa.DateTime, nullable=False),
        sa.Column(
            "proposal_text_snapshot",
            sa.Integer if incompatible_snapshot else sa.Text,
            nullable=False,
        ),
        sa.Column("submitted_price", sa.Numeric(10, 2)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("delivery_estimate", sa.String(200)),
        sa.Column("outcome_status", sa.String(40), nullable=False),
        sa.Column("admin_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        *(
            [
                sa.Column("application_id", sa.String(64)),
                sa.Column("submission_intent_id", sa.String(64)),
            ]
            if include_011_columns else []
        ),
    )
    sa.Index("ix_manual_opportunity_submissions_profile_id", table.c.profile_id)
    sa.Index("ix_manual_opportunity_submissions_job_id", table.c.job_id, unique=True)
    sa.Index("ix_manual_opportunity_submissions_created_by_user_id", table.c.created_by_user_id)
    sa.Index("ix_manual_submission_profile_job", table.c.profile_id, table.c.job_id, unique=True)
    metadata.create_all(connection)
    return table


def operations(connection):
    return Operations(MigrationContext.configure(connection))


def run_upgrade(module, connection):
    module.op = operations(connection)
    module.upgrade()


def insert_submission(connection, table, *, job_id="job-1"):
    timestamp = datetime(2026, 1, 1)
    connection.execute(table.insert().values(
        profile_id="enigma_profile",
        job_id=job_id,
        created_by_user_id="admin",
        submitted_at=timestamp,
        proposal_text_snapshot=7 if isinstance(table.c.proposal_text_snapshot.type, sa.Integer) else "preserve me",
        currency="USD",
        outcome_status="manually_submitted",
        created_at=timestamp,
        updated_at=timestamp,
    ))


def assert_010_schema(connection):
    inspector = sa.inspect(connection)
    job_columns = {column["name"] for column in inspector.get_columns("marketplace_jobs")}
    assert {
        "original_text", "normalized_requirements", "source_language",
        "customer_preferred_language", "proposal_language",
        "translation_metadata", "created_by_user_id",
    } <= job_columns
    submission_columns = {
        column["name"] for column in inspector.get_columns("manual_opportunity_submissions")
    }
    assert {
        "id", "profile_id", "job_id", "created_by_user_id",
        "proposal_text_snapshot", "outcome_status", "created_at", "updated_at",
    } <= submission_columns
    indexes = {index["name"] for index in inspector.get_indexes("manual_opportunity_submissions")}
    assert set(migration("010")._SUBMISSION_INDEXES) <= indexes
    reflected = {
        column["name"]: column
        for column in inspector.get_columns("manual_opportunity_submissions")
    }
    for name in ("outcome_status", "created_at", "updated_at"):
        assert reflected[name]["nullable"] is False
        assert reflected[name]["default"] is not None


def test_previous_blind_create_reproduces_duplicate_table_failure():
    with engine().begin() as connection:
        revision_009_schema(connection)
        compatible_submission_table(connection)
        legacy_operations = operations(connection)
        with pytest.raises(sa.exc.OperationalError, match="already exists"):
            legacy_operations.create_table(
                "manual_opportunity_submissions",
                sa.Column("id", sa.Integer, primary_key=True),
            )


def test_clean_revision_009_upgrades_to_010():
    with engine().begin() as connection:
        revision_009_schema(connection)
        run_upgrade(migration("010"), connection)
        assert_010_schema(connection)


def test_compatible_preexisting_submission_is_reused_and_data_preserved():
    with engine().begin() as connection:
        revision_009_schema(connection)
        table = compatible_submission_table(connection)
        insert_submission(connection, table)
        run_upgrade(migration("010"), connection)
        row = connection.execute(sa.select(table)).mappings().one()
        assert row["proposal_text_snapshot"] == "preserve me"
        assert_010_schema(connection)


def test_all_compatible_010_objects_preexisting_pass():
    with engine().begin() as connection:
        revision_009_schema(connection, include_010_columns=True)
        compatible_submission_table(connection)
        run_upgrade(migration("010"), connection)
        assert_010_schema(connection)


def test_incompatible_existing_table_fails_without_deleting_data():
    with engine().begin() as connection:
        revision_009_schema(connection)
        table = compatible_submission_table(connection, incompatible_snapshot=True)
        insert_submission(connection, table)
        with pytest.raises(RuntimeError, match="proposal_text_snapshot has type INTEGER"):
            run_upgrade(migration("010"), connection)
        assert connection.execute(sa.select(sa.func.count()).select_from(table)).scalar_one() == 1
        assert "manual_opportunity_submissions" in sa.inspect(connection).get_table_names()


def test_create_all_style_011_columns_do_not_break_chain():
    with engine().begin() as connection:
        revision_009_schema(connection)
        table = compatible_submission_table(connection, include_011_columns=True)
        insert_submission(connection, table)
        run_upgrade(migration("010"), connection)
        run_upgrade(migration("011"), connection)
        columns = {column["name"] for column in sa.inspect(connection).get_columns(table.name)}
        assert {"application_id", "submission_intent_id"} <= columns
        assert connection.execute(sa.select(sa.func.count()).select_from(table)).scalar_one() == 1


def test_009_through_014_and_head_downgrade_reupgrade():
    with engine().begin() as connection:
        revision_009_schema(connection)
        modules = [migration(number) for number in ("010", "011", "012", "013", "014")]
        for module in modules:
            run_upgrade(module, connection)
        tables = set(sa.inspect(connection).get_table_names())
        assert {
            "manual_opportunity_submissions", "freelancer_conversations",
            "freelancer_chat_messages", "freelancer_project_artifacts",
        } <= tables
        modules[-1].op = operations(connection)
        modules[-1].downgrade()
        assert "freelancer_conversations" not in sa.inspect(connection).get_table_names()
        run_upgrade(modules[-1], connection)
        assert "freelancer_project_artifacts" in sa.inspect(connection).get_table_names()


def test_required_freelancer_routes_remain_registered():
    from app.routers import freelancing, freelancer_chat

    paths = {route.path for route in freelancing.router.routes} | {
        route.path for route in freelancer_chat.router.routes
    }
    assert {
        "/api/freelancing/manual",
        "/api/freelancing/chat",
        "/api/freelancing/chat/projects",
        "/api/freelancing/chat/samples",
    } <= paths
