"""Add durable manual opportunity intake and submission tracking.

Revision ID: 010_manual_opportunity_intake
Revises: 009_durable_opportunity_pipeline
"""
from alembic import op
import sqlalchemy as sa

revision = "010_manual_opportunity_intake"
down_revision = "009_durable_opportunity_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, type_ in (
        ("original_text", sa.Text()),
        ("normalized_requirements", sa.JSON()),
        ("source_language", sa.String(10)),
        ("customer_preferred_language", sa.String(10)),
        ("proposal_language", sa.String(10)),
        ("translation_metadata", sa.JSON()),
        ("created_by_user_id", sa.String(64)),
    ):
        op.add_column("marketplace_jobs", sa.Column(name, type_, nullable=True))
    op.create_index("ix_marketplace_jobs_created_by_user_id", "marketplace_jobs", ["created_by_user_id"])

    op.create_table(
        "manual_opportunity_submissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("created_by_user_id", sa.String(64), nullable=False),
        sa.Column("marketplace_proposal_id", sa.String(200), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("proposal_text_snapshot", sa.Text(), nullable=False),
        sa.Column("submitted_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("delivery_estimate", sa.String(200), nullable=True),
        sa.Column("outcome_status", sa.String(40), nullable=False, server_default="manually_submitted"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_manual_opportunity_submissions_profile_id", "manual_opportunity_submissions", ["profile_id"])
    op.create_index("ix_manual_opportunity_submissions_job_id", "manual_opportunity_submissions", ["job_id"], unique=True)
    op.create_index("ix_manual_opportunity_submissions_created_by_user_id", "manual_opportunity_submissions", ["created_by_user_id"])
    op.create_index("ix_manual_submission_profile_job", "manual_opportunity_submissions", ["profile_id", "job_id"], unique=True)


def downgrade() -> None:
    op.drop_table("manual_opportunity_submissions")
    op.drop_index("ix_marketplace_jobs_created_by_user_id", table_name="marketplace_jobs")
    for name in ("created_by_user_id", "translation_metadata", "proposal_language", "customer_preferred_language", "source_language", "normalized_requirements", "original_text"):
        op.drop_column("marketplace_jobs", name)
