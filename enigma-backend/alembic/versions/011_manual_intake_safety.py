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


def upgrade() -> None:
    op.add_column("marketplace_jobs", sa.Column("manual_dedupe_key", sa.String(64), nullable=True))
    op.add_column("marketplace_jobs", sa.Column("proposal_application_id", sa.String(64), nullable=True))
    op.execute("""
        UPDATE marketplace_jobs AS job SET manual_dedupe_key = job.identity_fingerprint
        WHERE job.ingestion_source = 'manual' AND job.identity_fingerprint IS NOT NULL
          AND job.id = (SELECT MIN(candidate.id) FROM marketplace_jobs AS candidate
              WHERE candidate.profile_id = job.profile_id AND candidate.ingestion_source = 'manual'
                AND candidate.identity_fingerprint = job.identity_fingerprint)
    """)
    op.create_index("uq_marketplace_jobs_manual_dedupe", "marketplace_jobs", ["profile_id", "manual_dedupe_key"], unique=True)
    op.add_column("manual_opportunity_submissions", sa.Column("application_id", sa.String(64), nullable=True))
    op.add_column("manual_opportunity_submissions", sa.Column("submission_intent_id", sa.String(64), nullable=True))
    # Existing snapshots remain readable. New writes require both links in application code.


def downgrade() -> None:
    op.drop_column("manual_opportunity_submissions", "submission_intent_id")
    op.drop_column("manual_opportunity_submissions", "application_id")
    op.drop_index("uq_marketplace_jobs_manual_dedupe", table_name="marketplace_jobs")
    op.drop_column("marketplace_jobs", "proposal_application_id")
    op.drop_column("marketplace_jobs", "manual_dedupe_key")
