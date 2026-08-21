"""Add durable project-aware Freelancer Chat persistence.

Revision ID: 014_project_aware_freelancer_chat
Revises: 013_runtime_url_canonical_dedupe
"""
from alembic import op
import sqlalchemy as sa

revision = "014_project_aware_freelancer_chat"
down_revision = "013_runtime_url_canonical_dedupe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "freelancer_conversations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("active_project_id", sa.String(64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_freelancer_conversations_user_updated", "freelancer_conversations", ["user_id", "updated_at"])
    op.create_index("ix_freelancer_conversations_profile", "freelancer_conversations", ["profile_id"])

    op.create_table(
        "freelancer_chat_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("freelancer_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(64), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_freelancer_messages_conversation_created", "freelancer_chat_messages", ["conversation_id", "created_at"])
    op.create_index("uq_freelancer_messages_conversation_sequence", "freelancer_chat_messages", ["conversation_id", "sequence"], unique=True)
    op.create_index("ix_freelancer_messages_user_project", "freelancer_chat_messages", ["user_id", "project_id"])

    op.create_table(
        "freelancer_project_artifacts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(64), nullable=True),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("visibility", sa.String(30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("source_message_id", sa.String(64), sa.ForeignKey("freelancer_chat_messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_freelancer_artifacts_user_project_type", "freelancer_project_artifacts", ["user_id", "project_id", "artifact_type"])
    op.create_index("ix_freelancer_artifacts_visibility_type", "freelancer_project_artifacts", ["user_id", "visibility", "artifact_type"])
    op.create_index(
        "uq_freelancer_artifact_version", "freelancer_project_artifacts",
        ["user_id", "project_id", "artifact_type", "version"], unique=True,
    )


def downgrade() -> None:
    op.drop_table("freelancer_project_artifacts")
    op.drop_table("freelancer_chat_messages")
    op.drop_table("freelancer_conversations")
