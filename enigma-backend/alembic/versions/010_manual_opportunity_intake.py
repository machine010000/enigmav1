"""Add durable manual opportunity intake and submission tracking.

Revision ID: 010_manual_opportunity_intake
Revises: 009_durable_opportunity_pipeline

Historic startup called ``Base.metadata.create_all()`` before this revision was
applied. Existing objects are therefore reused only after validation;
incompatible objects fail closed and are never dropped or replaced.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "010_manual_opportunity_intake"
down_revision = "009_durable_opportunity_pipeline"
branch_labels = None
depends_on = None

ColumnFactory = Callable[[], sa.Column[Any]]


def _marketplace_columns() -> dict[str, ColumnFactory]:
    return {
        "original_text": lambda: sa.Column("original_text", sa.Text(), nullable=True),
        "normalized_requirements": lambda: sa.Column("normalized_requirements", sa.JSON(), nullable=True),
        "source_language": lambda: sa.Column("source_language", sa.String(10), nullable=True),
        "customer_preferred_language": lambda: sa.Column("customer_preferred_language", sa.String(10), nullable=True),
        "proposal_language": lambda: sa.Column("proposal_language", sa.String(10), nullable=True),
        "translation_metadata": lambda: sa.Column("translation_metadata", sa.JSON(), nullable=True),
        "created_by_user_id": lambda: sa.Column("created_by_user_id", sa.String(64), nullable=True),
    }


def _submission_columns() -> dict[str, ColumnFactory]:
    return {
        "id": lambda: sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        "profile_id": lambda: sa.Column("profile_id", sa.String(), nullable=False),
        "job_id": lambda: sa.Column("job_id", sa.String(), nullable=False),
        "created_by_user_id": lambda: sa.Column("created_by_user_id", sa.String(64), nullable=False),
        "marketplace_proposal_id": lambda: sa.Column("marketplace_proposal_id", sa.String(200), nullable=True),
        "submitted_at": lambda: sa.Column("submitted_at", sa.DateTime(), nullable=False),
        "proposal_text_snapshot": lambda: sa.Column("proposal_text_snapshot", sa.Text(), nullable=False),
        "submitted_price": lambda: sa.Column("submitted_price", sa.Numeric(10, 2), nullable=True),
        "currency": lambda: sa.Column("currency", sa.String(3), nullable=False),
        "delivery_estimate": lambda: sa.Column("delivery_estimate", sa.String(200), nullable=True),
        "outcome_status": lambda: sa.Column("outcome_status", sa.String(40), nullable=False, server_default="manually_submitted"),
        "admin_notes": lambda: sa.Column("admin_notes", sa.Text(), nullable=True),
        "created_at": lambda: sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        "updated_at": lambda: sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    }


_SUBMISSION_INDEXES = {
    "ix_manual_opportunity_submissions_profile_id": (("profile_id",), False),
    "ix_manual_opportunity_submissions_job_id": (("job_id",), True),
    "ix_manual_opportunity_submissions_created_by_user_id": (("created_by_user_id",), False),
    "ix_manual_submission_profile_job": (("profile_id", "job_id"), True),
}


def _fail(message: str) -> None:
    raise RuntimeError(f"Migration 010 schema drift is incompatible: {message}")


def _type_compatible(actual: sa.types.TypeEngine[Any], expected: sa.types.TypeEngine[Any]) -> bool:
    if isinstance(expected, sa.Text):
        return isinstance(actual, sa.Text)
    if isinstance(expected, sa.String):
        if not isinstance(actual, sa.String):
            return False
        return expected.length is None or actual.length is None or actual.length >= expected.length
    if isinstance(expected, sa.Integer):
        return isinstance(actual, sa.Integer)
    if isinstance(expected, sa.DateTime):
        return isinstance(actual, sa.DateTime)
    if isinstance(expected, sa.Numeric):
        if not isinstance(actual, sa.Numeric):
            return False
        precision_ok = actual.precision is None or (
            expected.precision is not None and actual.precision >= expected.precision
        )
        scale_ok = actual.scale is None or (
            expected.scale is not None and actual.scale >= expected.scale
        )
        return precision_ok and scale_ok
    if isinstance(expected, sa.JSON):
        return isinstance(actual, sa.JSON)
    return actual._type_affinity is expected._type_affinity


def _row_count(bind: sa.engine.Connection, table_name: str) -> int:
    return int(bind.execute(
        sa.text(f'SELECT count(*) FROM "{table_name}"')
    ).scalar_one())


def _null_count(bind: sa.engine.Connection, table_name: str, column_name: str) -> int:
    return int(bind.execute(
        sa.text(f'SELECT count(*) FROM "{table_name}" WHERE "{column_name}" IS NULL')
    ).scalar_one())


def _alter_column(
    bind: sa.engine.Connection,
    table_name: str,
    column_name: str,
    *,
    existing_type: sa.types.TypeEngine[Any],
    nullable: bool | None = None,
    server_default: Any = False,
) -> None:
    kwargs: dict[str, Any] = {"existing_type": existing_type}
    if nullable is not None:
        kwargs["nullable"] = nullable
    if server_default is not False:
        kwargs["server_default"] = server_default
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch:
            batch.alter_column(column_name, **kwargs)
    else:
        op.alter_column(table_name, column_name, **kwargs)


def _default_is_compatible(actual: Any, expected: str) -> bool:
    if actual is None:
        return False
    normalized = str(actual).lower().replace("'", "").replace('"', "")
    if "manually_submitted" in expected:
        return "manually_submitted" in normalized
    return "current_timestamp" in normalized or "now()" in normalized


def _ensure_columns(
    bind: sa.engine.Connection,
    table_name: str,
    factories: dict[str, ColumnFactory],
    *,
    require_primary_key: bool = False,
) -> None:
    existing = {
        column["name"]: column for column in sa.inspect(bind).get_columns(table_name)
    }
    row_count = _row_count(bind, table_name)
    for name, factory in factories.items():
        expected = factory()
        actual = existing.get(name)
        if actual is None:
            if expected.primary_key:
                _fail(f"{table_name}.{name} primary key is missing")
            if not expected.nullable and expected.server_default is None and row_count:
                _fail(
                    f"cannot add required column {table_name}.{name} to a non-empty table; "
                    "backfill values explicitly before retrying"
                )
            op.add_column(table_name, expected)
            actual = next(
                column for column in sa.inspect(bind).get_columns(table_name)
                if column["name"] == name
            )
        if not _type_compatible(actual["type"], expected.type):
            _fail(
                f"{table_name}.{name} has type {actual['type']!s}; "
                f"expected a compatible {expected.type!s}"
            )
        if not expected.nullable and actual.get("nullable", True) and not expected.primary_key:
            if _null_count(bind, table_name, name):
                _fail(f"{table_name}.{name} contains NULL values but must be NOT NULL")
            _alter_column(bind, table_name, name, existing_type=actual["type"], nullable=False)
            actual = next(
                column for column in sa.inspect(bind).get_columns(table_name)
                if column["name"] == name
            )
        if expected.server_default is not None and not _default_is_compatible(
            actual.get("default"), str(expected.server_default.arg)
        ):
            _alter_column(
                bind, table_name, name,
                existing_type=actual["type"], server_default=expected.server_default.arg,
            )
    if require_primary_key:
        primary_key = sa.inspect(bind).get_pk_constraint(table_name)
        if tuple(primary_key.get("constrained_columns") or ()) != ("id",):
            _fail(f"{table_name} must have primary key (id)")


def _has_duplicate_key(
    bind: sa.engine.Connection, table_name: str, columns: tuple[str, ...]
) -> bool:
    table = sa.table(table_name, *(sa.column(column) for column in columns))
    query = (
        sa.select(*(table.c[column] for column in columns))
        .where(*(table.c[column].is_not(None) for column in columns))
        .group_by(*(table.c[column] for column in columns))
        .having(sa.func.count() > 1)
        .limit(1)
    )
    return bind.execute(query).first() is not None


def _ensure_index(
    bind: sa.engine.Connection,
    table_name: str,
    name: str,
    columns: tuple[str, ...],
    unique: bool,
) -> None:
    indexes = {index["name"]: index for index in sa.inspect(bind).get_indexes(table_name)}
    existing = indexes.get(name)
    if existing is not None:
        if tuple(existing.get("column_names") or ()) != columns or bool(existing.get("unique")) != unique:
            _fail(
                f"index {name} is incompatible; found columns={existing.get('column_names')} "
                f"unique={bool(existing.get('unique'))}, expected columns={list(columns)} unique={unique}"
            )
        return
    if unique and _has_duplicate_key(bind, table_name, columns):
        _fail(f"cannot create unique index {name}; duplicate values exist for {table_name}{columns}")
    op.create_index(name, table_name, list(columns), unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    if "marketplace_jobs" not in sa.inspect(bind).get_table_names():
        _fail("required revision-009 table marketplace_jobs is missing")
    _ensure_columns(bind, "marketplace_jobs", _marketplace_columns())
    _ensure_index(
        bind, "marketplace_jobs", "ix_marketplace_jobs_created_by_user_id",
        ("created_by_user_id",), False,
    )

    if "manual_opportunity_submissions" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "manual_opportunity_submissions",
            *[factory() for factory in _submission_columns().values()],
        )
    _ensure_columns(
        bind, "manual_opportunity_submissions", _submission_columns(),
        require_primary_key=True,
    )
    for name, (columns, unique) in _SUBMISSION_INDEXES.items():
        _ensure_index(bind, "manual_opportunity_submissions", name, columns, unique)


def downgrade() -> None:
    op.drop_table("manual_opportunity_submissions")
    op.drop_index("ix_marketplace_jobs_created_by_user_id", table_name="marketplace_jobs")
    for name in (
        "created_by_user_id", "translation_metadata", "proposal_language",
        "customer_preferred_language", "source_language",
        "normalized_requirements", "original_text",
    ):
        op.drop_column("marketplace_jobs", name)
