"""Add capability intelligence columns to knowledge_progress

TASK-017: Evidence-based confidence policy.

Adds to knowledge_progress:
  - capability_status: VARCHAR derived from evidence (UNKNOWN/LEARNING/PRACTICING/QUALIFIED/PROVEN)
  - evidence_count: total execution observations
  - successful_execution_count: successful executions
  - failed_execution_count: failed executions
  - last_success_at: timestamp of most recent success
  - freelance_readiness_threshold: per-capability minimum confidence for READY_TO_APPLY

Revision ID: 003_capability_intelligence
Revises: 002_execution_ownership
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = '003_capability_intelligence'
down_revision = '002_execution_ownership'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Capability status — nullable, will be computed on next ProfileUpdater run
    op.add_column(
        'knowledge_progress',
        sa.Column('capability_status', sa.String(50), nullable=True, server_default='unknown'),
    )
    # Evidence counters — default 0 (backward compatible)
    op.add_column(
        'knowledge_progress',
        sa.Column('evidence_count', sa.Integer(), nullable=True, server_default='0'),
    )
    op.add_column(
        'knowledge_progress',
        sa.Column('successful_execution_count', sa.Integer(), nullable=True, server_default='0'),
    )
    op.add_column(
        'knowledge_progress',
        sa.Column('failed_execution_count', sa.Integer(), nullable=True, server_default='0'),
    )
    op.add_column(
        'knowledge_progress',
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
    )
    # Freelance readiness threshold — default 0.65
    op.add_column(
        'knowledge_progress',
        sa.Column(
            'freelance_readiness_threshold',
            sa.Float(),
            nullable=True,
            server_default='0.65',
        ),
    )

    # Index for capability_status lookups (e.g. "find all QUALIFIED capabilities")
    op.create_index(
        'ix_knowledge_progress_capability_status',
        'knowledge_progress',
        ['profile_id', 'capability_status'],
    )


def downgrade() -> None:
    op.drop_index('ix_knowledge_progress_capability_status', table_name='knowledge_progress')
    op.drop_column('knowledge_progress', 'freelance_readiness_threshold')
    op.drop_column('knowledge_progress', 'last_success_at')
    op.drop_column('knowledge_progress', 'failed_execution_count')
    op.drop_column('knowledge_progress', 'successful_execution_count')
    op.drop_column('knowledge_progress', 'evidence_count')
    op.drop_column('knowledge_progress', 'capability_status')
