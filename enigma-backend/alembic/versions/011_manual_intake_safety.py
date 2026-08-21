"""Harden manual opportunity provenance, dedupe, and approval linkage.

Revision ID: 011_manual_intake_safety
Revises: 010_manual_opportunity_intake
"""
from alembic import op
import sqlalchemy as sa

revision = "011_manual_intake_safety"
down_revision = "010_manual_opportunity_intake"
branch_labels = None
depends_on = None


def _ensure_nullable_string(bind, table_name: str, name: str, length: int) -> None:
    columns = {column["name"]: column for column in sa.inspect(bind).get_columns(table_name)}
    existing = columns.get(name)
    if existing is None:
        op.add_column(table_name, sa.Column(name, sa.String(length), nullable=True))
        return
    actual = existing["type"]
    compatible = isinstance(actual, sa.String) and (
        actual.length is None or actual.length >= length
    )
    if not compatible or not existing.get("nullable", True):
        raise RuntimeError(
            f"Migration 011 schema drift is incompatible: {table_name}.{name} "
            f"must be nullable String({length})"
        )


def _ensure_manual_dedupe_index(bind) -> None:
    name = "uq_marketplace_jobs_manual_dedupe"
    indexes = {
        index["name"]: index
        for index in sa.inspect(bind).get_indexes("marketplace_jobs")
    }
    existing = indexes.get(name)
    if existing is None:
        op.create_index(
            name, "marketplace_jobs", ["profile_id", "manual_dedupe_key"],
            unique=True,
        )
        return
    if (
        tuple(existing.get("column_names") or ()) != ("profile_id", "manual_dedupe_key")
        or not existing.get("unique")
    ):
        raise RuntimeError(
            f"Migration 011 schema drift is incompatible: index {name} has "
            f"columns={existing.get('column_names')} unique={bool(existing.get('unique'))}"
        )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_nullable_string(bind, "marketplace_jobs", "manual_dedupe_key", 64)
    _ensure_nullable_string(bind, "marketplace_jobs", "proposal_application_id", 64)
    op.execute("""
        UPDATE marketplace_jobs AS job SET manual_dedupe_key = job.identity_fingerprint
        WHERE job.ingestion_source = 'manual' AND job.identity_fingerprint IS NOT NULL
          AND job.id = (SELECT MIN(candidate.id) FROM marketplace_jobs AS candidate
              WHERE candidate.profile_id = job.profile_id AND candidate.ingestion_source = 'manual'
                AND candidate.identity_fingerprint = job.identity_fingerprint)
    """)
    _ensure_manual_dedupe_index(bind)
    _ensure_nullable_string(bind, "manual_opportunity_submissions", "application_id", 64)
    _ensure_nullable_string(bind, "manual_opportunity_submissions", "submission_intent_id", 64)
    # Existing snapshots remain readable. New writes require both links in application code.


def downgrade() -> None:
    op.drop_column("manual_opportunity_submissions", "submission_intent_id")
    op.drop_column("manual_opportunity_submissions", "application_id")
    op.drop_index("uq_marketplace_jobs_manual_dedupe", table_name="marketplace_jobs")
    op.drop_column("marketplace_jobs", "proposal_application_id")
    op.drop_column("marketplace_jobs", "manual_dedupe_key")
