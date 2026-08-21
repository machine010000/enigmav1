"""Add durable project-aware Freelancer Chat persistence.

Revision ID: 014_project_aware_freelancer_chat
Revises: 013_runtime_url_canonical_dedupe

Startup historically used ``Base.metadata.create_all()``. Compatible objects
created ahead of Alembic are preserved; incompatible drift fails closed.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "014_project_aware_freelancer_chat"
down_revision = "013_runtime_url_canonical_dedupe"
branch_labels = None
depends_on = None

ColumnFactory = Callable[[], sa.Column[Any]]


def _conversation_columns() -> dict[str, ColumnFactory]:
    return {
        "id": lambda: sa.Column("id", sa.String(64), primary_key=True),
        "profile_id": lambda: sa.Column("profile_id", sa.String(64), nullable=False),
        "user_id": lambda: sa.Column("user_id", sa.String(64), nullable=False),
        "title": lambda: sa.Column("title", sa.String(300), nullable=False),
        "active_project_id": lambda: sa.Column("active_project_id", sa.String(64), nullable=True),
        "metadata": lambda: sa.Column("metadata", sa.JSON(), nullable=False),
        "created_at": lambda: sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        "updated_at": lambda: sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    }


def _message_columns() -> dict[str, ColumnFactory]:
    return {
        "id": lambda: sa.Column("id", sa.String(64), primary_key=True),
        "conversation_id": lambda: sa.Column("conversation_id", sa.String(64), sa.ForeignKey("freelancer_conversations.id", ondelete="CASCADE"), nullable=False),
        "profile_id": lambda: sa.Column("profile_id", sa.String(64), nullable=False),
        "user_id": lambda: sa.Column("user_id", sa.String(64), nullable=False),
        "project_id": lambda: sa.Column("project_id", sa.String(64), nullable=True),
        "role": lambda: sa.Column("role", sa.String(20), nullable=False),
        "sequence": lambda: sa.Column("sequence", sa.Integer(), nullable=False),
        "intent": lambda: sa.Column("intent", sa.String(50), nullable=True),
        "content": lambda: sa.Column("content", sa.Text(), nullable=False),
        "structured_data": lambda: sa.Column("structured_data", sa.JSON(), nullable=False),
        "created_at": lambda: sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    }


def _artifact_columns() -> dict[str, ColumnFactory]:
    return {
        "id": lambda: sa.Column("id", sa.String(64), primary_key=True),
        "profile_id": lambda: sa.Column("profile_id", sa.String(64), nullable=False),
        "user_id": lambda: sa.Column("user_id", sa.String(64), nullable=False),
        "project_id": lambda: sa.Column("project_id", sa.String(64), nullable=True),
        "artifact_type": lambda: sa.Column("artifact_type", sa.String(50), nullable=False),
        "visibility": lambda: sa.Column("visibility", sa.String(30), nullable=False),
        "version": lambda: sa.Column("version", sa.Integer(), nullable=False),
        "content": lambda: sa.Column("content", sa.Text(), nullable=False),
        "data": lambda: sa.Column("data", sa.JSON(), nullable=False),
        "source_message_id": lambda: sa.Column("source_message_id", sa.String(64), sa.ForeignKey("freelancer_chat_messages.id", ondelete="SET NULL"), nullable=True),
        "created_at": lambda: sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    }


_TABLES = (
    ("freelancer_conversations", _conversation_columns),
    ("freelancer_chat_messages", _message_columns),
    ("freelancer_project_artifacts", _artifact_columns),
)
_INDEXES = {
    "freelancer_conversations": {
        "ix_freelancer_conversations_user_updated": (("user_id", "updated_at"), False),
        "ix_freelancer_conversations_profile": (("profile_id",), False),
    },
    "freelancer_chat_messages": {
        "ix_freelancer_messages_conversation_created": (("conversation_id", "created_at"), False),
        "uq_freelancer_messages_conversation_sequence": (("conversation_id", "sequence"), True),
        "ix_freelancer_messages_user_project": (("user_id", "project_id"), False),
    },
    "freelancer_project_artifacts": {
        "ix_freelancer_artifacts_user_project_type": (("user_id", "project_id", "artifact_type"), False),
        "ix_freelancer_artifacts_visibility_type": (("user_id", "visibility", "artifact_type"), False),
        "uq_freelancer_artifact_version": (("user_id", "project_id", "artifact_type", "version"), True),
    },
}
_FOREIGN_KEYS = {
    "freelancer_chat_messages": (("conversation_id", "freelancer_conversations", "id", "CASCADE"),),
    "freelancer_project_artifacts": (("source_message_id", "freelancer_chat_messages", "id", "SET NULL"),),
}


def _fail(message: str) -> None:
    raise RuntimeError(f"Migration 014 schema drift is incompatible: {message}")


def _compatible_type(actual: Any, expected: Any) -> bool:
    if isinstance(expected, sa.Text):
        return isinstance(actual, sa.Text)
    if isinstance(expected, sa.String):
        return isinstance(actual, sa.String) and (expected.length is None or actual.length is None or actual.length >= expected.length)
    if isinstance(expected, sa.Integer):
        return isinstance(actual, sa.Integer)
    if isinstance(expected, sa.DateTime):
        return isinstance(actual, sa.DateTime)
    if isinstance(expected, sa.JSON):
        return isinstance(actual, sa.JSON)
    return actual._type_affinity is expected._type_affinity


def _count(bind: Any, table: str, where: str = "") -> int:
    return int(bind.execute(sa.text(f'SELECT count(*) FROM "{table}" {where}')).scalar_one())


def _alter(bind: Any, table: str, column: str, **kwargs: Any) -> None:
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table) as batch:
            batch.alter_column(column, **kwargs)
    else:
        op.alter_column(table, column, **kwargs)


def _ensure_columns(bind: Any, table: str, factories: dict[str, ColumnFactory]) -> None:
    existing = {item["name"]: item for item in sa.inspect(bind).get_columns(table)}
    rows = _count(bind, table)
    for name, factory in factories.items():
        expected = factory()
        actual = existing.get(name)
        if actual is None:
            if expected.primary_key:
                _fail(f"{table}.{name} primary key is missing")
            if not expected.nullable and expected.server_default is None and rows:
                _fail(f"cannot add required column {table}.{name} to a non-empty table")
            op.add_column(table, expected)
            actual = next(item for item in sa.inspect(bind).get_columns(table) if item["name"] == name)
        if not _compatible_type(actual["type"], expected.type):
            _fail(f"{table}.{name} has type {actual['type']}; expected compatible {expected.type}")
        if not expected.nullable and actual.get("nullable", True) and not expected.primary_key:
            if _count(bind, table, f'WHERE "{name}" IS NULL'):
                _fail(f"{table}.{name} contains NULL values but must be NOT NULL")
            _alter(bind, table, name, existing_type=actual["type"], nullable=False)
            actual = next(item for item in sa.inspect(bind).get_columns(table) if item["name"] == name)
        if expected.server_default is not None:
            default = str(actual.get("default") or "").lower()
            if "current_timestamp" not in default and "now()" not in default:
                _alter(bind, table, name, existing_type=actual["type"], server_default=expected.server_default.arg)
    primary_key = sa.inspect(bind).get_pk_constraint(table)
    if tuple(primary_key.get("constrained_columns") or ()) != ("id",):
        _fail(f"{table} must have primary key (id)")


def _duplicates(bind: Any, table_name: str, columns: tuple[str, ...]) -> bool:
    table = sa.table(table_name, *(sa.column(column) for column in columns))
    query = (sa.select(*(table.c[column] for column in columns))
             .where(*(table.c[column].is_not(None) for column in columns))
             .group_by(*(table.c[column] for column in columns))
             .having(sa.func.count() > 1).limit(1))
    return bind.execute(query).first() is not None


def _ensure_index(bind: Any, table: str, name: str, columns: tuple[str, ...], unique: bool) -> None:
    existing = {item["name"]: item for item in sa.inspect(bind).get_indexes(table)}.get(name)
    if existing:
        if tuple(existing.get("column_names") or ()) != columns or bool(existing.get("unique")) != unique:
            _fail(f"index {name} is incompatible")
        return
    if unique and _duplicates(bind, table, columns):
        _fail(f"cannot create unique index {name}; duplicate values exist")
    op.create_index(name, table, list(columns), unique=unique)


def _ensure_foreign_key(bind: Any, table: str, local: str, parent: str, remote: str, ondelete: str) -> None:
    for foreign_key in sa.inspect(bind).get_foreign_keys(table):
        if tuple(foreign_key.get("constrained_columns") or ()) != (local,):
            continue
        actual_delete = str((foreign_key.get("options") or {}).get("ondelete") or "").upper()
        if foreign_key.get("referred_table") == parent and tuple(foreign_key.get("referred_columns") or ()) == (remote,) and actual_delete == ondelete:
            return
        _fail(f"foreign key on {table}.{local} is incompatible")
    orphans = _count(bind, table, f'child WHERE child."{local}" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM "{parent}" parent WHERE parent."{remote}" = child."{local}")')
    if orphans:
        _fail(f"cannot add foreign key on {table}.{local}; {orphans} orphan row(s) exist")
    if bind.dialect.name == "sqlite":
        _fail(f"foreign key on {table}.{local} is missing and cannot be added safely on SQLite")
    op.create_foreign_key(None, table, parent, [local], [remote], ondelete=ondelete)


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    for table, factory in _TABLES:
        if table not in existing:
            op.create_table(table, *[item() for item in factory().values()])
            existing.add(table)
        _ensure_columns(bind, table, factory())
        for foreign_key in _FOREIGN_KEYS.get(table, ()):
            _ensure_foreign_key(bind, table, *foreign_key)
        for name, (columns, unique) in _INDEXES[table].items():
            _ensure_index(bind, table, name, columns, unique)


def downgrade() -> None:
    op.drop_table("freelancer_project_artifacts")
    op.drop_table("freelancer_chat_messages")
    op.drop_table("freelancer_conversations")
