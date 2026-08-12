"""Add user_id ownership column to worker_executions

TASK-016: Execution Ownership — every WorkerExecution must carry the
requesting user_id so cross-user access can be denied at the DB layer.

Revision ID: 002_execution_ownership
Revises: 001_initial
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_execution_ownership'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to worker_executions (nullable so existing rows survive)
    op.add_column(
        'worker_executions',
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    # Index for per-user execution queries
    op.create_index(
        'ix_worker_executions_user_id',
        'worker_executions',
        ['user_id'],
    )
    # Composite index: user_id + created_at for ordered per-user lookups
    op.create_index(
        'ix_worker_executions_user_created',
        'worker_executions',
        ['user_id', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_worker_executions_user_created', table_name='worker_executions')
    op.drop_index('ix_worker_executions_user_id', table_name='worker_executions')
    op.drop_column('worker_executions', 'user_id')
