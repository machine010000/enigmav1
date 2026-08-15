"""Add system capability progress and evidence contribution ledger.

Revision ID: 004_cap_promotion
Revises: 003_capability_intelligence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_cap_promotion"
down_revision = "003_capability_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_capability_progress",
        sa.Column("capability_id", sa.String(100), primary_key=True),
        sa.Column("knowledge_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("execution_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("readiness", sa.Float(), nullable=False, server_default="0"),
        sa.Column("capability_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("freelance_readiness_threshold", sa.Float(), nullable=False, server_default="0.65"),
        sa.Column("last_verified", sa.DateTime(), nullable=True),
        sa.Column("freshness", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("concepts", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("policy_version", sa.String(50), nullable=False, server_default="capability-promotion-v1"),
        sa.Column("aggregate_source", sa.String(50), nullable=False, server_default="legacy_backfill"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "capability_evidence_contributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("worker_executions.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("capability_id", sa.String(100), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("training_mode", sa.String(50), nullable=True),
        sa.Column("observation_status", sa.String(30), nullable=False),
        sa.Column("evaluation_score", sa.Float(), nullable=True),
        sa.Column("evidence_digest", sa.String(64), nullable=False),
        sa.Column("evidence_reference", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("eligibility_state", sa.String(30), nullable=False),
        sa.Column("decision_state", sa.String(30), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("promoted_at", sa.DateTime(), nullable=True),
        sa.Column("promoted_by", sa.String(100), nullable=True),
        sa.Column("progress_applied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_capability_contribution_capability_decision",
                    "capability_evidence_contributions", ["capability_id", "decision_state"])
    op.create_index("ix_capability_contribution_user_created",
                    "capability_evidence_contributions", ["user_id", "created_at"])

    # Preserve deployed global state exactly; historical execution lineage is
    # intentionally not fabricated.
    op.execute("""
        INSERT INTO system_capability_progress (
          capability_id, knowledge_score, execution_score, evidence_score,
          confidence, readiness, capability_status, evidence_count,
          successful_execution_count, failed_execution_count, last_success_at,
          freelance_readiness_threshold, last_verified, freshness, concepts,
          policy_version, aggregate_source, version, created_at, updated_at
        )
        SELECT domain, COALESCE(knowledge_score,0), COALESCE(execution_score,0),
          COALESCE(evidence_score,0), COALESCE(confidence,0), COALESCE(readiness,0),
          COALESCE(capability_status,'unknown'), COALESCE(evidence_count,0),
          COALESCE(successful_execution_count,0), COALESCE(failed_execution_count,0),
          last_success_at, COALESCE(freelance_readiness_threshold,0.65), last_verified,
          COALESCE(freshness,'unknown'), COALESCE(concepts,'{}'::json),
          'capability-promotion-v1', 'legacy_backfill', 1,
          COALESCE(created_at, now()), COALESCE(updated_at, now())
        FROM knowledge_progress WHERE profile_id = 'enigma_profile'
        ON CONFLICT (capability_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index("ix_capability_contribution_user_created", table_name="capability_evidence_contributions")
    op.drop_index("ix_capability_contribution_capability_decision", table_name="capability_evidence_contributions")
    op.drop_table("capability_evidence_contributions")
    op.drop_table("system_capability_progress")
