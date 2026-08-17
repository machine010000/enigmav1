"""Add application_submission_intents table for safe submission boundary.

Revision ID: 007_submission_intents
Revises: 006_controlled_app_packages
Create Date: 2026-08-16

TASK-052 — Safe boundary between APPROVED controlled application packages
and future external platform submission.

Semantic:
  application_submission_intents → records INTENT to submit only.
  No external call is made by any code touching this table in TASK-052.
  external_submission_attempted is always False in TASK-052.
  SUBMITTED is intentionally absent from the state machine in TASK-052.

State machine (enforced at application layer):
  PENDING_EXTERNAL_SUBMISSION → CANCELLED

Safety:
  - Additive migration only.
  - Does NOT modify any existing table.
  - Idempotent: checks table existence before creating.
  - No data backfill required.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_submission_intents"
down_revision = "006_controlled_app_packages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect

    inspector = inspect(conn)

    def table_exists(name: str) -> bool:
        return name in inspector.get_table_names()

    def index_exists(table: str, name: str) -> bool:
        try:
            return any(
                idx.get("name") == name for idx in inspector.get_indexes(table)
            )
        except Exception:
            return False

    if table_exists("application_submission_intents"):
        return  # Idempotent

    op.create_table(
        "application_submission_intents",
        # --- Identity ---
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("submission_id", sa.String(64), nullable=False, unique=True),

        # --- Ownership ---
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # --- Linked package ---
        sa.Column("application_id", sa.String(64), nullable=False),

        # --- Opportunity context ---
        sa.Column("opportunity_id", sa.String(200), nullable=False),
        sa.Column("opportunity_title", sa.String(500), nullable=False),
        sa.Column("platform", sa.String(100), nullable=False),

        # --- State machine ---
        sa.Column(
            "state",
            sa.String(40),
            nullable=False,
            server_default="PENDING_EXTERNAL_SUBMISSION",
        ),

        # --- Submission mode ---
        sa.Column(
            "submission_mode",
            sa.String(40),
            nullable=False,
            server_default="manual",
        ),

        # --- Safety flags ---
        sa.Column(
            "external_submission_attempted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("external_submission_id", sa.String(200), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),

        # --- Readiness snapshot ---
        sa.Column(
            "readiness_snapshot",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),

        # --- Audit ---
        sa.Column("last_validation_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("cancellation_note", sa.Text(), nullable=True),

        # --- Timestamps ---
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    if not index_exists(
        "application_submission_intents", "ix_submission_intent_submission_id"
    ):
        op.create_index(
            "ix_submission_intent_submission_id",
            "application_submission_intents",
            ["submission_id"],
            unique=True,
        )
    if not index_exists(
        "application_submission_intents", "ix_submission_intent_user_id"
    ):
        op.create_index(
            "ix_submission_intent_user_id",
            "application_submission_intents",
            ["user_id"],
        )
    if not index_exists(
        "application_submission_intents", "ix_submission_intent_user_created"
    ):
        op.create_index(
            "ix_submission_intent_user_created",
            "application_submission_intents",
            ["user_id", "created_at"],
        )
    if not index_exists(
        "application_submission_intents", "ix_submission_intent_user_application"
    ):
        op.create_index(
            "ix_submission_intent_user_application",
            "application_submission_intents",
            ["user_id", "application_id"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_submission_intent_user_application",
        table_name="application_submission_intents",
    )
    op.drop_index(
        "ix_submission_intent_user_created",
        table_name="application_submission_intents",
    )
    op.drop_index(
        "ix_submission_intent_user_id",
        table_name="application_submission_intents",
    )
    op.drop_index(
        "ix_submission_intent_submission_id",
        table_name="application_submission_intents",
    )
    op.drop_table("application_submission_intents")
