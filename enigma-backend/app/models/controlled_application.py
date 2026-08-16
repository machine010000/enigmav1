"""
Controlled Application Package DB Model — TASK-051

Dedicated persistence model for controlled review-cycle packages.

Semantic separation from MarketplaceApplication:
  - MarketplaceApplication  → tracks real external platform submissions
                               (has platform_job_id, platform_application_id,
                               submitted_at, bid_amount)
  - ControlledApplicationPackageRecord → tracks internal human-review drafts
                               (no external IDs, no submitted_at, no bid)

State machine (TASK-051):
  READY_FOR_HUMAN_APPROVAL → APPROVED
  READY_FOR_HUMAN_APPROVAL → REJECTED
  No further transitions in TASK-051.
  SUBMITTED is NOT a valid state in this table.

Ownership:
  Every record has user_id (FK users.id).
  All reads/writes are filtered by user_id.
  Cross-user access returns 404 (not 403) per project non-disclosure policy.

Learning isolation:
  This table is never written by any training/evidence path.
  Writing this table never increments KnowledgeProgress.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ControlledApplicationPackageRecord(Base):
    """
    Durable record for a controlled evidence-backed application package.

    Created by POST /api/freelancing/opportunities/application-package.
    Reviewed by POST /api/freelancing/application-packages/{id}/review.
    Read    by GET  /api/freelancing/application-packages/{id}
             and GET  /api/freelancing/application-packages  (user-scoped list).

    Never connected to MarketplaceAdapter or any external submission path.
    """

    __tablename__ = "controlled_application_packages"

    # --- Identity ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # Human-readable string ID returned to callers (e.g. "pkg_<hex16>")
    application_id = Column(String(64), nullable=False, unique=True, index=True)

    # --- Ownership ---
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Opportunity identity ---
    opportunity_id = Column(String(200), nullable=False)
    opportunity_title = Column(String(500), nullable=False)
    platform = Column(String(100), nullable=False)

    # --- Assessment snapshot (server-side at generation time) ---
    readiness_decision = Column(String(50), nullable=False)   # always ready_to_apply
    readiness_score = Column(Float, nullable=False, default=0.0)

    # --- Capability data (JSON snapshots, never mutated after creation) ---
    required_capabilities = Column(JSON, nullable=False, default=list)
    matched_capabilities = Column(JSON, nullable=False, default=list)
    # Full CapabilityClaim dicts — historical snapshot, immutable after write
    capability_claims_snapshot = Column(JSON, nullable=False, default=list)
    # Full EvidenceSummary dicts — historical snapshot, immutable after write
    evidence_summary_snapshot = Column(JSON, nullable=False, default=list)

    # --- Proposal content ---
    proposal_text = Column(Text, nullable=False, default="")
    known_limitations = Column(JSON, nullable=False, default=list)

    # --- Idempotency / fingerprint ---
    # SHA-256 hex of (user_id + opportunity_id + required_capabilities sorted)
    # Used to detect duplicate in-flight drafts.
    opportunity_fingerprint = Column(String(64), nullable=True, index=True)

    # --- State machine ---
    # Valid values: READY_FOR_HUMAN_APPROVAL | APPROVED | REJECTED
    state = Column(String(40), nullable=False, default="READY_FOR_HUMAN_APPROVAL")

    # --- Review fields (populated by /review endpoint) ---
    reviewed_at = Column(DateTime, nullable=True)
    review_decision = Column(String(20), nullable=True)   # "approve" | "reject"
    review_note = Column(Text, nullable=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    # --- Stale-safety flag set on APPROVE if re-assessment showed not-ready ---
    stale_on_approval_attempt = Column(Boolean, nullable=False, default=False)

    # --- Timestamps ---
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Fast lookup: user sees their own packages ordered by time
        Index("ix_cap_pkg_user_created", "user_id", "created_at"),
        # Idempotency: detect duplicate drafts for same user+opportunity
        Index("ix_cap_pkg_user_fingerprint", "user_id", "opportunity_fingerprint"),
    )
