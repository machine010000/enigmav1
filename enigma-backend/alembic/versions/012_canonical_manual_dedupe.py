"""Normalize manual dedupe keys to the runtime canonical representation.

Revision ID: 012_canonical_manual_dedupe
Revises: 011_manual_intake_safety
"""
from alembic import op

revision = "012_canonical_manual_dedupe"
down_revision = "011_manual_intake_safety"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("uq_marketplace_jobs_manual_dedupe", table_name="marketplace_jobs")
    op.execute("""
        UPDATE marketplace_jobs
        SET manual_dedupe_key = md5(
            lower(trim(platform)) || '|' ||
            COALESCE(NULLIF(url, ''), NULLIF(lower(trim(platform_job_id)), ''), identity_fingerprint)
        )
        WHERE ingestion_source = 'manual'
    """)
    op.execute("""
        WITH ranked AS (
            SELECT id, row_number() OVER (
                PARTITION BY profile_id, manual_dedupe_key ORDER BY id
            ) AS duplicate_rank
            FROM marketplace_jobs
            WHERE ingestion_source = 'manual' AND manual_dedupe_key IS NOT NULL
        )
        UPDATE marketplace_jobs AS job SET manual_dedupe_key = NULL
        FROM ranked WHERE job.id = ranked.id AND ranked.duplicate_rank > 1
    """)
    op.create_index(
        "uq_marketplace_jobs_manual_dedupe", "marketplace_jobs",
        ["profile_id", "manual_dedupe_key"], unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_marketplace_jobs_manual_dedupe", table_name="marketplace_jobs")
    op.execute("""
        UPDATE marketplace_jobs SET manual_dedupe_key = identity_fingerprint
        WHERE ingestion_source = 'manual'
    """)
    op.execute("""
        WITH ranked AS (
            SELECT id, row_number() OVER (
                PARTITION BY profile_id, manual_dedupe_key ORDER BY id
            ) AS duplicate_rank
            FROM marketplace_jobs
            WHERE ingestion_source = 'manual' AND manual_dedupe_key IS NOT NULL
        )
        UPDATE marketplace_jobs AS job SET manual_dedupe_key = NULL
        FROM ranked WHERE job.id = ranked.id AND ranked.duplicate_rank > 1
    """)
    op.create_index(
        "uq_marketplace_jobs_manual_dedupe", "marketplace_jobs",
        ["profile_id", "manual_dedupe_key"], unique=True,
    )
