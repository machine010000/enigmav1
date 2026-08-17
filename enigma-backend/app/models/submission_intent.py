"""
Application Submission Intent DB Model — TASK-052

Represents the intent to submit an APPROVED controlled application package
to an external platform. This is a safety boundary:

  APPROVED (controlled_application_packages)
    → PENDING_EXTERNAL_SUBMISSION (this table)
    → [future task: actual external submission]

Semantic contract:
  - This table records INTENT only. No external call is made here.
  - external_submission_attempted is always False in TASK-052.
  - SUBMITTED is NOT a valid state_value in this table in TASK-052.
  - The linked controlled_application_packages record is never mutated.
  - Learning evidence is never created from this table.

State machine (TASK-052):
  PENDING_EXTERNAL_SUBMISSION → CANCELLED

Ownership:
  All reads/writes are scoped by (submission_id, user_id).
  Cross-user access returns 404 (non-disclosure policy).

Replay policy:
  Same user + same application_id with active PENDING_EXTERNAL_SUBMISSION
  → return existing intent, no duplicate created.
  After CANCELLED → a new intent may be created if eligibility passes.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ApplicationSubmissionIntent(Base):
    """
    Durable record of intent to submit an approved application package.

    Created by: POST /api/freelancing/application-packages/{id}/submission-intent
    Read by:    GET  /api/freelancing/submission-intents/{submission_id}
                GET  /api/freelancing/submission-intents
    Cancelled:  POST /api/freelancing/submission-intents/{submission_id}/cancel

    Never connected to MarketplaceAdapter.submit_application in TASK-052.
    """

    __tablename__ = "application_submission_intents"

    # --- Identity ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submission_id = Column(String(64), nullable=False, unique=True, index=True)

    # --- Ownership ---
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Linked package ---
    application_id = Column(String(64), nullable=False, index=True)

    # --- Opportunity context (snapshot from approved package) ---
    opportunity_id = Column(String(200), nullable=False)
    opportunity_title = Column(String(500), nullable=False)

    # --- Platform ---
    # Recorded as-is from the approved package; validated against known platforms.
    platform = Column(String(100), nullable=False)

    # --- State machine ---
    # Valid values: PENDING_EXTERNAL_SUBMISSION | CANCELLED
    # SUBMITTED is intentionally absent in TASK-052.
    state = Column(
        String(40),
        nullable=False,
        default="PENDING_EXTERNAL_SUBMISSION",
    )

    # --- Submission mode (future: manual | api | queued) ---
    submission_mode = Column(String(40), nullable=False, default="manual")

    # --- Safety flags ---
    # Always False in TASK-052. Set True only when future task actually submits.
    external_submission_attempted = Column(Boolean, nullable=False, default=False)
    external_submission_id = Column(String(200), nullable=True)  # platform-assigned ID (future)
    failure_reason = Column(Text, nullable=True)

    # --- Readiness snapshot at intent creation ---
    # Summarises the fresh re-check result so reviewers know what was validated.
    readiness_snapshot = Column(JSON, nullable=False, default=dict)

    # --- Review audit ---
    last_validation_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_note = Column(Text, nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Fast lookup: user's intents newest first
        Index("ix_submission_intent_user_created", "user_id", "created_at"),
        # Idempotency: one active intent per user+application
        Index("ix_submission_intent_user_application", "user_id", "application_id"),
    )
