"""Recompute manual dedupe keys with the authoritative runtime URL normalizer.

Revision ID: 013_runtime_url_canonical_dedupe
Revises: 012_canonical_manual_dedupe
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from typing import Any

from alembic import op
import sqlalchemy as sa

from app.freelancing.manual_dedupe import canonical_dedupe_key, normalize_source_url

revision = "013_runtime_url_canonical_dedupe"
down_revision = "012_canonical_manual_dedupe"
branch_labels = None
depends_on = None

_PREVIOUS_URL = "task_066f_pre_013_source_url"
_CANONICALIZED_BY = "task_066f_canonicalized_by"
_COLLISION_WITH = "task_066f_collision_canonical_job_id"

jobs = sa.table(
    "marketplace_jobs",
    sa.column("id", sa.Integer()),
    sa.column("profile_id", sa.String()),
    sa.column("job_id", sa.String()),
    sa.column("platform", sa.String()),
    sa.column("platform_job_id", sa.String()),
    sa.column("title", sa.String()),
    sa.column("client_info", sa.JSON()),
    sa.column("url", sa.String()),
    sa.column("identity_fingerprint", sa.String()),
    sa.column("manual_dedupe_key", sa.String()),
    sa.column("metadata", sa.JSON()),
    sa.column("ingestion_source", sa.String()),
)


def _upgrade_plan(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build a deterministic plan without deleting colliding records."""
    planned: list[dict[str, Any]] = []
    winners: dict[tuple[str, str], str] = {}
    for source in sorted(rows, key=lambda item: item["id"]):
        row = dict(source)
        normalized_url = normalize_source_url(row.get("url"))
        key = canonical_dedupe_key(
            row["platform"],
            row.get("platform_job_id"),
            row.get("url"),
            row.get("title") or "",
            row.get("client_info") or {},
        )
        metadata = dict(row.get("metadata") or {})
        if row.get("url") and row["url"] != normalized_url:
            metadata.setdefault(_PREVIOUS_URL, row["url"])
        metadata[_CANONICALIZED_BY] = revision
        identity = (row["profile_id"], key)
        canonical_job_id = winners.get(identity)
        if canonical_job_id is None:
            winners[identity] = row["job_id"]
        else:
            metadata[_COLLISION_WITH] = canonical_job_id
            key = None
        planned.append({
            "id": row["id"],
            "url": normalized_url,
            "manual_dedupe_key": key,
            "metadata": metadata,
        })
    return planned


def _v012_key(row: Mapping[str, Any], restored_url: str | None) -> str | None:
    identity = (
        restored_url
        or ((row.get("platform_job_id") or "").strip().lower() or None)
        or row.get("identity_fingerprint")
    )
    if identity is None:
        return None
    return hashlib.md5(
        f"{(row.get('platform') or '').strip().lower()}|{identity}".encode(),
        usedforsecurity=False,
    ).hexdigest()


def _downgrade_plan(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    winners: set[tuple[str, str]] = set()
    for source in sorted(rows, key=lambda item: item["id"]):
        row = dict(source)
        metadata = dict(row.get("metadata") or {})
        restored_url = metadata.pop(_PREVIOUS_URL, row.get("url"))
        metadata.pop(_CANONICALIZED_BY, None)
        metadata.pop(_COLLISION_WITH, None)
        key = _v012_key(row, restored_url)
        if key is not None:
            identity = (row["profile_id"], key)
            if identity in winners:
                key = None
            else:
                winners.add(identity)
        planned.append({
            "id": row["id"],
            "url": restored_url,
            "manual_dedupe_key": key,
            "metadata": metadata,
        })
    return planned


def _manual_rows(bind: sa.engine.Connection) -> list[Mapping[str, Any]]:
    return list(bind.execute(
        sa.select(jobs).where(jobs.c.ingestion_source == "manual").order_by(jobs.c.id)
    ).mappings())


def _apply(bind: sa.engine.Connection, plan: Iterable[Mapping[str, Any]]) -> None:
    for values in plan:
        row_id = values["id"]
        bind.execute(
            sa.update(jobs).where(jobs.c.id == row_id).values(
                url=values["url"],
                manual_dedupe_key=values["manual_dedupe_key"],
                metadata=values["metadata"],
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    op.drop_index("uq_marketplace_jobs_manual_dedupe", table_name="marketplace_jobs")
    _apply(bind, _upgrade_plan(_manual_rows(bind)))
    op.create_index(
        "uq_marketplace_jobs_manual_dedupe",
        "marketplace_jobs",
        ["profile_id", "manual_dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("uq_marketplace_jobs_manual_dedupe", table_name="marketplace_jobs")
    _apply(bind, _downgrade_plan(_manual_rows(bind)))
    op.create_index(
        "uq_marketplace_jobs_manual_dedupe",
        "marketplace_jobs",
        ["profile_id", "manual_dedupe_key"],
        unique=True,
    )
