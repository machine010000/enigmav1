"""Add user capability contexts and explicitly owned memory episodes.

Revision ID: 005_user_context
Revises: 004_cap_promotion
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_user_context"
down_revision = "004_cap_promotion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_capability_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capability_id", sa.String(100), nullable=False),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_execution_at", sa.DateTime(), nullable=True),
        sa.Column("recent_outcomes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("private_context", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("preference_references", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("constraint_references", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_capability_context_owner_capability", "user_capability_contexts",
                    ["user_id", "capability_id"], unique=True)
    op.create_table(
        "memory_episodes",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("worker_executions.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("owner_scope", sa.String(20), nullable=False),
        sa.Column("product_id", sa.String(100), nullable=True),
        sa.Column("capability_id", sa.String(100), nullable=True),
        sa.Column("worker", sa.String(255), nullable=False),
        sa.Column("goal", sa.String(255), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("outputs", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("execution_time", sa.Float(), nullable=False, server_default="0"),
        sa.Column("llm_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(owner_scope = 'user' AND user_id IS NOT NULL) OR "
            "(owner_scope IN ('system','legacy') AND user_id IS NULL)",
            name="ck_memory_episode_owner_scope",
        ),
    )
    op.create_index("ix_memory_episode_user_created", "memory_episodes", ["user_id", "created_at"])
    op.create_index("ix_memory_episode_scope_capability", "memory_episodes", ["owner_scope", "capability_id"])

    # Ownership is unambiguous only where WorkerExecution.user_id is present.
    op.execute("""
      INSERT INTO user_capability_contexts (
        id, user_id, capability_id, execution_count, successful_execution_count,
        failed_execution_count, last_execution_at, recent_outcomes, private_context,
        preference_references, constraint_references, created_at, updated_at
      )
      SELECT gen_random_uuid(), user_id, worker_name, count(*),
        count(*) FILTER (WHERE status='success'),
        count(*) FILTER (WHERE status='failed'), max(created_at),
        '[]'::json, '{"backfill":"owned_execution_aggregate"}'::json,
        '[]'::json, '[]'::json, now(), now()
      FROM worker_executions WHERE user_id IS NOT NULL
      GROUP BY user_id, worker_name
      ON CONFLICT (user_id, capability_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index("ix_memory_episode_scope_capability", table_name="memory_episodes")
    op.drop_index("ix_memory_episode_user_created", table_name="memory_episodes")
    op.drop_table("memory_episodes")
    op.drop_index("ix_user_capability_context_owner_capability", table_name="user_capability_contexts")
    op.drop_table("user_capability_contexts")
