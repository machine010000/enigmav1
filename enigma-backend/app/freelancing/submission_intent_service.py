"""
Application Submission Intent Service — TASK-052

Implements the safe boundary between a human-APPROVED controlled application
package and any future external platform submission.

Architecture contract:
  - State machine: PENDING_EXTERNAL_SUBMISSION → CANCELLED only (TASK-052).
  - SUBMITTED is intentionally absent — no external call is made here.
  - SubmissionIntentService MUST NOT import or call:
      MarketplaceAdapter.submit_application
      UpworkAdapter (or any concrete adapter)
      Any external HTTP/GraphQL submission
  - external_submission_attempted is always False in TASK-052.
  - Eligibility gate requires: package exists, owned by user, state=APPROVED,
    fresh readiness re-check passes, no conflicting active intent.
  - Replay: same user + same application_id with active PENDING intent → reuse.
  - All reads/writes scoped by (submission_id|application_id, user_id).
  - Learning is never mutated.
  - No platform secrets are stored or returned.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.freelancing.assessment_service import OpportunityAssessmentService
from app.freelancing.contracts import (
    ApplicationMode,
    BrainDecisionType,
    FreelanceOpportunity,
    ReadinessState,
)
from app.models.controlled_application import ControlledApplicationPackageRecord
from app.models.submission_intent import ApplicationSubmissionIntent
from app.models.user import User

logger = get_logger(__name__)
_assessment_service = OpportunityAssessmentService()

# ---------------------------------------------------------------------------
# Recognised platform values (extendable; rejects bogus strings)
# ---------------------------------------------------------------------------
KNOWN_PLATFORMS = {
    "upwork", "fiverr", "freelancer", "mostaql", "khamsat",
    "people_per_hour", "guru", "controlled_internal", "unknown",
}


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class IntentState(str, Enum):
    PENDING_EXTERNAL_SUBMISSION = "PENDING_EXTERNAL_SUBMISSION"
    CANCELLED = "CANCELLED"
    # SUBMITTED is intentionally absent in TASK-052


# ---------------------------------------------------------------------------
# Domain model (in-process, returned to API callers)
# ---------------------------------------------------------------------------

@dataclass
class SubmissionIntent:
    submission_id: str
    application_id: str
    opportunity_id: str
    opportunity_title: str
    platform: str
    state: IntentState
    submission_mode: str
    external_submission_attempted: bool
    external_submission_id: Optional[str]
    failure_reason: Optional[str]
    readiness_snapshot: Dict[str, Any]
    last_validation_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_note: Optional[str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "submission_id": self.submission_id,
            "application_id": self.application_id,
            "opportunity_id": self.opportunity_id,
            "opportunity_title": self.opportunity_title,
            "platform": self.platform,
            "state": self.state.value,
            "submission_mode": self.submission_mode,
            "external_submission_attempted": self.external_submission_attempted,
            "readiness_snapshot": self.readiness_snapshot,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # Safety statement — always present
            "submission_boundary": (
                "Intent recorded. No external platform action has been taken. "
                "APPROVED means human-approved for a future explicit submission step only."
            ),
        }
        if self.external_submission_id:
            d["external_submission_id"] = self.external_submission_id
        if self.failure_reason:
            d["failure_reason"] = self.failure_reason
        if self.last_validation_at:
            d["last_validation_at"] = self.last_validation_at.isoformat()
        if self.cancelled_at:
            d["cancelled_at"] = self.cancelled_at.isoformat()
        if self.cancellation_note:
            d["cancellation_note"] = self.cancellation_note
        return d


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class IntentNotFoundError(Exception):
    """Raised when an intent is not found or belongs to another user."""


class IntentEligibilityError(Exception):
    """Raised when the application package does not qualify for an intent."""
    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


class IntentStateError(Exception):
    """Raised when a state transition is not permitted."""


class IntentStaleReadinessError(Exception):
    """Raised when fresh re-check shows the opportunity is no longer ready."""
    def __init__(self, message: str, current_decision: str):
        super().__init__(message)
        self.current_decision = current_decision


# ---------------------------------------------------------------------------
# Record → domain model hydration
# ---------------------------------------------------------------------------

def _record_to_intent(record: ApplicationSubmissionIntent) -> SubmissionIntent:
    return SubmissionIntent(
        submission_id=record.submission_id,
        application_id=record.application_id,
        opportunity_id=record.opportunity_id,
        opportunity_title=record.opportunity_title,
        platform=record.platform,
        state=IntentState(record.state),
        submission_mode=record.submission_mode,
        external_submission_attempted=bool(record.external_submission_attempted),
        external_submission_id=record.external_submission_id,
        failure_reason=record.failure_reason,
        readiness_snapshot=record.readiness_snapshot or {},
        last_validation_at=record.last_validation_at,
        cancelled_at=record.cancelled_at,
        cancellation_note=record.cancellation_note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class SubmissionIntentRepository:
    """User-scoped DB repository for ApplicationSubmissionIntent."""

    async def get_by_submission_id(
        self, db: AsyncSession, submission_id: str, user_id: str
    ) -> Optional[ApplicationSubmissionIntent]:
        result = await db.execute(
            select(ApplicationSubmissionIntent).where(
                ApplicationSubmissionIntent.submission_id == submission_id,
                ApplicationSubmissionIntent.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_application(
        self, db: AsyncSession, user_id: str, application_id: str
    ) -> Optional[ApplicationSubmissionIntent]:
        """Return existing PENDING_EXTERNAL_SUBMISSION intent for this application."""
        result = await db.execute(
            select(ApplicationSubmissionIntent).where(
                ApplicationSubmissionIntent.user_id == user_id,
                ApplicationSubmissionIntent.application_id == application_id,
                ApplicationSubmissionIntent.state
                == IntentState.PENDING_EXTERNAL_SUBMISSION.value,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ApplicationSubmissionIntent]:
        result = await db.execute(
            select(ApplicationSubmissionIntent)
            .where(ApplicationSubmissionIntent.user_id == user_id)
            .order_by(ApplicationSubmissionIntent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def save(
        self, db: AsyncSession, record: ApplicationSubmissionIntent
    ) -> None:
        db.add(record)
        await db.flush()


_repo = SubmissionIntentRepository()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class SubmissionIntentService:
    """
    Manages ApplicationSubmissionIntent records.

    HARD SEPARATION:
      This service MUST NOT import or call:
        - MarketplaceAdapter.submit_application
        - UpworkAdapter or any concrete marketplace adapter
        - external HTTP clients (httpx.post, requests.post, etc.)
        - GraphQL mutation endpoints

    Any future external execution belongs to a SEPARATE task (TASK-053+).
    """

    def __init__(self) -> None:
        self._assessment_service = _assessment_service
        self._repo = _repo

    async def create_intent(
        self,
        *,
        user: User,
        application_id: str,
        db: AsyncSession,
    ) -> SubmissionIntent:
        """
        Create or reuse a PENDING_EXTERNAL_SUBMISSION intent.

        Eligibility gate (all must pass):
          1. Package exists and belongs to user.
          2. Package state == APPROVED.
          3. Fresh authoritative readiness re-check passes.
          4. Platform is recognised.
          5. No conflicting active intent (replay → reuse existing).

        external_submission_attempted is always False.
        No external call is made.

        Raises:
            IntentEligibilityError  — package not found, wrong state, or unknown platform
            IntentStaleReadinessError — fresh re-check shows not ready
        """
        user_id = str(user.id)

        # --- Step 1: Load approved package (ownership-scoped) ---
        pkg_result = await db.execute(
            select(ControlledApplicationPackageRecord).where(
                ControlledApplicationPackageRecord.application_id == application_id,
                ControlledApplicationPackageRecord.user_id == user.id,
            )
        )
        pkg = pkg_result.scalar_one_or_none()

        if pkg is None:
            raise IntentEligibilityError(
                f"Application package '{application_id}' not found.",
                reason="not_found",
            )

        # --- Step 2: Package must be APPROVED ---
        if pkg.state != "APPROVED":
            raise IntentEligibilityError(
                f"Package '{application_id}' is in state '{pkg.state}'. "
                "Only APPROVED packages can create a submission intent.",
                reason="wrong_package_state",
            )

        # --- Step 3: Validate platform ---
        platform_lower = (pkg.platform or "unknown").lower()
        if platform_lower not in KNOWN_PLATFORMS:
            raise IntentEligibilityError(
                f"Platform '{pkg.platform}' is not recognised.",
                reason="unknown_platform",
            )

        # --- Step 4: Verify claim snapshot is present ---
        claims = pkg.capability_claims_snapshot or []
        if not claims:
            raise IntentEligibilityError(
                "Package has no capability claims snapshot — cannot verify.",
                reason="missing_claims",
            )

        # --- Step 5: Fresh readiness re-check ---
        readiness_snapshot, stale_decision = await self._recheck_readiness(
            db=db,
            user_id=user_id,
            opportunity_title=pkg.opportunity_title,
            opportunity_id=pkg.opportunity_id,
            platform=pkg.platform,
            required_capabilities=list(pkg.required_capabilities or []),
        )
        if stale_decision is not None:
            raise IntentStaleReadinessError(
                f"Opportunity is no longer ready_to_apply (current: {stale_decision}). "
                "Cannot create submission intent.",
                current_decision=stale_decision,
            )

        # --- Step 6: Replay — reuse existing active intent ---
        existing = await self._repo.get_active_for_application(db, user_id, application_id)
        if existing is not None:
            logger.info(
                "submission_intent_reused",
                extra={
                    "submission_id": existing.submission_id,
                    "user_id": user_id,
                    "application_id": application_id,
                },
            )
            return _record_to_intent(existing)

        # --- Step 7: Create new intent ---
        submission_id = f"intent_{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()

        record = ApplicationSubmissionIntent(
            submission_id=submission_id,
            user_id=user.id,
            application_id=application_id,
            opportunity_id=pkg.opportunity_id,
            opportunity_title=pkg.opportunity_title,
            platform=pkg.platform,
            state=IntentState.PENDING_EXTERNAL_SUBMISSION.value,
            submission_mode="manual",
            external_submission_attempted=False,
            readiness_snapshot=readiness_snapshot,
            last_validation_at=now,
            created_at=now,
            updated_at=now,
        )
        await self._repo.save(db, record)

        logger.info(
            "submission_intent_created",
            extra={
                "submission_id": submission_id,
                "user_id": user_id,
                "application_id": application_id,
                "platform": pkg.platform,
            },
        )

        return _record_to_intent(record)

    async def cancel_intent(
        self,
        *,
        user: User,
        submission_id: str,
        note: Optional[str],
        db: AsyncSession,
    ) -> SubmissionIntent:
        """
        Cancel a PENDING_EXTERNAL_SUBMISSION intent.

        Only PENDING_EXTERNAL_SUBMISSION can be cancelled.
        Already-CANCELLED raises IntentStateError.
        Cross-user raises IntentNotFoundError.

        Does NOT mutate the linked application package.
        Does NOT contact any external platform.
        """
        user_id = str(user.id)
        record = await self._repo.get_by_submission_id(db, submission_id, user_id)
        if record is None:
            raise IntentNotFoundError(f"Submission intent '{submission_id}' not found.")

        if record.state != IntentState.PENDING_EXTERNAL_SUBMISSION.value:
            raise IntentStateError(
                f"Intent '{submission_id}' is in state '{record.state}' "
                "and cannot be cancelled."
            )

        now = datetime.utcnow()
        record.state = IntentState.CANCELLED.value
        record.cancelled_at = now
        record.cancellation_note = note
        record.updated_at = now
        await db.flush()

        logger.info(
            "submission_intent_cancelled",
            extra={"submission_id": submission_id, "user_id": user_id},
        )
        return _record_to_intent(record)

    async def get_by_id(
        self,
        *,
        user: User,
        submission_id: str,
        db: AsyncSession,
    ) -> SubmissionIntent:
        user_id = str(user.id)
        record = await self._repo.get_by_submission_id(db, submission_id, user_id)
        if record is None:
            raise IntentNotFoundError(f"Submission intent '{submission_id}' not found.")
        return _record_to_intent(record)

    async def list_for_user(
        self,
        *,
        user: User,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SubmissionIntent]:
        records = await self._repo.list_for_user(
            db, str(user.id), limit=limit, offset=offset
        )
        return [_record_to_intent(r) for r in records]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _recheck_readiness(
        self,
        db: AsyncSession,
        user_id: str,
        opportunity_title: str,
        opportunity_id: str,
        platform: str,
        required_capabilities: List[str],
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Run a fresh authoritative assessment.

        Returns (snapshot_dict, None) if still ready_to_apply.
        Returns (snapshot_dict, blocking_decision_str) if not ready.
        """
        try:
            opp = FreelanceOpportunity(
                opportunity_id=opportunity_id,
                platform=platform,
                external_id=opportunity_id,
                title=opportunity_title,
                description=opportunity_title,  # title as fallback — enough for gap check
                required_skills=required_capabilities,
                application_mode=ApplicationMode.UNKNOWN,
                user_id=user_id,
            )
            _, assessment, decision = await self._assessment_service.assess(
                opportunity=opp, db=db
            )
            is_ready = (
                decision.decision == BrainDecisionType.READY_TO_APPLY
                or assessment.readiness
                in (ReadinessState.READY_TO_APPLY, ReadinessState.HIGH_CONFIDENCE)
            )
            snapshot: Dict[str, Any] = {
                "readiness_score": round(assessment.overall_score, 4),
                "readiness": assessment.readiness.value,
                "decision": decision.decision.value,
                "blocking_capability": decision.blocking_capability,
                "checked_at": datetime.utcnow().isoformat(),
            }
            return snapshot, (None if is_ready else decision.decision.value)
        except Exception as exc:
            logger.warning("intent_recheck_failed", extra={"error": str(exc)})
            # Conservative: treat re-check failure as stale to prevent unsafe intents
            return {
                "error": str(exc),
                "checked_at": datetime.utcnow().isoformat(),
            }, "assessment_error"
