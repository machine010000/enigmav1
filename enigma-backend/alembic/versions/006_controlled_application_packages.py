"""Add controlled_application_packages table for human-review lifecycle.

Revision ID: 006_controlled_app_packages
Revises: 005_user_context
Create Date: 2026-08-16

TASK-051 — Durable persistence for evidence-backed application packages.

Semantic: This table is DISTINCT from marketplace_applications.
  marketplace_applications  → external platform submissions
  controlled_application_packages → internal human-review drafts only
                                    (no external IDs, no submitted_at, no bid)

State machine (enforced at application layer, not DB constraint):
  READY_FOR_HUMAN_APPROVAL → APPROVED
  READY_FOR_HUMAN_APPROVAL → REJECTED
  SUBMITTED is intentionally absent.

Safety:
  - Additive migration only.
  - Does NOT modify any existing table.
  - Idempotent: checks table existence before creating.
  - No data backfill required (no prior records exist).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_controlled_app_packages"
down_revision = "005_user_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect, text
    inspector = inspect(conn)

    def table_exists(name: str) -> bool:
        return name in inspector.get_table_names()

    def index_exists(table: str, name: str) -> bool:
        try:
            return any(idx.get("name") == name for idx in inspector.get_indexes(table))
        except Exception:
            return False

    if table_exists("controlled_application_packages"):
        return  # Idempotent — already applied

    op.create_table(
        "controlled_application_packages",
        # --- Identity ---
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("application_id", sa.String(64), nullable=False, unique=True),

        # --- Ownership ---
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # --- Opportunity ---
        sa.Column("opportunity_id", sa.String(200), nullable=False),
        sa.Column("opportunity_title", sa.String(500), nullable=False),
        sa.Column("platform", sa.String(100), nullable=False),

        # --- Assessment snapshot ---
        sa.Column("readiness_decision", sa.String(50), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False, server_default="0.0"),

        # --- Capability snapshots (immutable after creation) ---
        sa.Column(
            "required_capabilities",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "matched_capabilities",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "capability_claims_snapshot",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "evidence_summary_snapshot",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),

        # --- Proposal content ---
        sa.Column("proposal_text", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "known_limitations",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),

        # --- Idempotency ---
        sa.Column("opportunity_fingerprint", sa.String(64), nullable=True),

        # --- State machine ---
        sa.Column(
            "state",
            sa.String(40),
            nullable=False,
            server_default="READY_FOR_HUMAN_APPROVAL",
        ),

        # --- Review fields ---
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_decision", sa.String(20), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),

        # --- Stale-safety flag ---
        sa.Column(
            "stale_on_approval_attempt",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

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

    if not index_exists("controlled_application_packages", "ix_cap_pkg_application_id"):
        op.create_index(
            "ix_cap_pkg_application_id",
            "controlled_application_packages",
            ["application_id"],
            unique=True,
        )
    if not index_exists("controlled_application_packages", "ix_cap_pkg_user_id"):
        op.create_index(
            "ix_cap_pkg_user_id",
            "controlled_application_packages",
            ["user_id"],
        )
    if not index_exists("controlled_application_packages", "ix_cap_pkg_user_created"):
        op.create_index(
            "ix_cap_pkg_user_created",
            "controlled_application_packages",
            ["user_id", "created_at"],
        )
    if not index_exists(
        "controlled_application_packages", "ix_cap_pkg_user_fingerprint"
    ):
        op.create_index(
            "ix_cap_pkg_user_fingerprint",
            "controlled_application_packages",
            ["user_id", "opportunity_fingerprint"],
        )


def downgrade() -> None:
    op.drop_index("ix_cap_pkg_user_fingerprint", table_name="controlled_application_packages")
    op.drop_index("ix_cap_pkg_user_created", table_name="controlled_application_packages")
    op.drop_index("ix_cap_pkg_user_id", table_name="controlled_application_packages")
    op.drop_index("ix_cap_pkg_application_id", table_name="controlled_application_packages")
    op.drop_table("controlled_application_packages")
