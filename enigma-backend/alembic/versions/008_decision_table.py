"""Add decisions and worker_event_logs tables

Revision ID: 008_decision_table
Revises: 007_submission_intents
Create Date: 2026-08-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_decision_table'
down_revision = '007_submission_intents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)

    def table_exists(name: str) -> bool:
        return name in inspector.get_table_names()

    # Create decisions table
    if not table_exists('decisions'):
        op.create_table(
            'decisions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('decision_id', sa.String(255), nullable=True, index=True),
            sa.Column('parent_decision_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('goal', sa.Text(), nullable=False, server_default=''),
            sa.Column('context', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('constraints', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('selected_capability', sa.String(255), nullable=True),
            sa.Column('selected_worker', sa.String(255), nullable=True),
            sa.Column('evidence', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('assumptions', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('risks', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('execution_strategy', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('reasoning', sa.Text(), nullable=True),
            sa.Column('decision_reason', sa.Text(), nullable=True),
            sa.Column('evidence_ids', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('concept_ids', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('rejected_alternatives', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('expected_outcome', sa.Text(), nullable=True),
            sa.Column('success_criteria', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('execution_result', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('feedback', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('next_action', sa.Text(), nullable=True),
            sa.Column('memory_hits', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('similar_episodes', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('selected_strategy', sa.String(255), nullable=True),
            sa.Column('pattern_matches', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column('status', sa.String(50), nullable=False, server_default='planned'),
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('source_research_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('validated', sa.Boolean(), nullable=False, server_default='False'),
            sa.Column('validation_data', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        # Create index on decision_id
        op.create_index('ix_decisions_decision_id', 'decisions', ['decision_id'])
        # Note: product_id FK skipped - products table not in migration history yet

    # Create worker_event_logs table
    if not table_exists('worker_event_logs'):
        op.create_table(
            'worker_event_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column('worker_name', sa.String(255), nullable=False, index=True),
            sa.Column('event_type', sa.String(100), nullable=False, index=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('data', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('timestamp', sa.DateTime(), nullable=True, server_default='now()', index=True),
        )
        # Create foreign key to worker_executions
        op.create_foreign_key(
            'fk_worker_event_logs_execution_id',
            'worker_event_logs',
            'worker_executions',
            ['execution_id'],
            ['id']
        )


def downgrade() -> None:
    op.drop_constraint('fk_worker_event_logs_execution_id', 'worker_event_logs', type_='foreignkey')
    op.drop_table('worker_event_logs')
    op.drop_index('ix_decisions_decision_id', table_name='decisions')
    op.drop_table('decisions')
