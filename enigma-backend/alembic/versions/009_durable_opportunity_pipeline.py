"""Add durable opportunity lifecycle and structured assessment evidence.

Revision ID: 009_durable_opportunity_pipeline
Revises: 008_decision_table
"""
from alembic import op
import sqlalchemy as sa

revision = "009_durable_opportunity_pipeline"
down_revision = "008_decision_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The original migration created this identity index without unique=True.
    # Replace it with the database-enforced canonical dedupe key.
    op.drop_index("ix_marketplace_jobs_profile_platform_job_id", table_name="marketplace_jobs")
    op.create_index("ix_marketplace_jobs_profile_platform_job_id", "marketplace_jobs", ["profile_id", "platform", "platform_job_id"], unique=True)
    op.add_column("marketplace_jobs", sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="verification_pending"))
    op.add_column("marketplace_jobs", sa.Column("identity_fingerprint", sa.String(64), nullable=True))
    op.add_column("marketplace_jobs", sa.Column("first_seen_at", sa.DateTime(), nullable=True))
    op.add_column("marketplace_jobs", sa.Column("last_seen_at", sa.DateTime(), nullable=True))
    op.add_column("marketplace_jobs", sa.Column("ingestion_source", sa.String(100), nullable=True))
    op.execute("UPDATE marketplace_jobs SET first_seen_at = COALESCE(created_at, CURRENT_TIMESTAMP), last_seen_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP) WHERE first_seen_at IS NULL OR last_seen_at IS NULL")
    op.alter_column("marketplace_jobs", "first_seen_at", nullable=False, server_default=sa.text("now()"))
    op.alter_column("marketplace_jobs", "last_seen_at", nullable=False, server_default=sa.text("now()"))
    op.create_index("ix_marketplace_jobs_lifecycle_status", "marketplace_jobs", ["lifecycle_status"])
    op.create_index("ix_marketplace_jobs_identity_fingerprint", "marketplace_jobs", ["identity_fingerprint"])

    assessment_columns = [
        ("readiness", sa.String(50)), ("decision", sa.String(50)),
        ("required_capabilities", sa.JSON(),), ("missing_capabilities", sa.JSON(),),
        ("weak_capabilities", sa.JSON(),), ("unmapped_skills", sa.JSON(),),
        ("risk_flags", sa.JSON(),), ("reasoning_summary", sa.Text(),),
        ("blocking_capability", sa.String(255)),
        ("execution_available_for_blocking", sa.Boolean()),
    ]
    for name, column_type in assessment_columns:
        op.add_column("marketplace_job_assessments", sa.Column(name, column_type, nullable=True))


def downgrade() -> None:
    for name in ("execution_available_for_blocking", "blocking_capability", "reasoning_summary", "risk_flags", "unmapped_skills", "weak_capabilities", "missing_capabilities", "required_capabilities", "decision", "readiness"):
        op.drop_column("marketplace_job_assessments", name)
    op.drop_index("ix_marketplace_jobs_identity_fingerprint", table_name="marketplace_jobs")
    op.drop_index("ix_marketplace_jobs_lifecycle_status", table_name="marketplace_jobs")
    op.drop_column("marketplace_jobs", "ingestion_source")
    op.drop_column("marketplace_jobs", "last_seen_at")
    op.drop_column("marketplace_jobs", "first_seen_at")
    op.drop_column("marketplace_jobs", "identity_fingerprint")
    op.drop_column("marketplace_jobs", "lifecycle_status")
    op.drop_index("ix_marketplace_jobs_profile_platform_job_id", table_name="marketplace_jobs")
    op.create_index("ix_marketplace_jobs_profile_platform_job_id", "marketplace_jobs", ["profile_id", "platform", "platform_job_id"])