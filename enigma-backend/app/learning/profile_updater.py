"""
Profile / Business State Updater

Updates ENIGMA's capability profile based on execution observations.

TASK-017: Evidence-based confidence policy.
Confidence is derived deterministically from evidence counts and execution
outcomes.  The LLM cannot directly overwrite canonical confidence values.

Policy (CapabilityStatus thresholds):
  UNKNOWN    → evidence_count == 0
  LEARNING   → evidence_count < 3  OR  confidence < 0.40
  PRACTICING → evidence_count >= 3 AND confidence >= 0.40
  QUALIFIED  → evidence_count >= 5 AND confidence >= 0.65
  PROVEN     → evidence_count >= 10 AND confidence >= 0.80

Confidence update rules:
  SUCCESS: confidence += (1.0 - confidence) * BOOST_FACTOR
  FAILURE: confidence -= confidence * PENALTY_FACTOR (floor: 0.0)

Success/failure counts are always incremented.
Positive profile evidence (product, knowledge) is only created on SUCCESS
(enforced in EvidenceMapper — TASK-016 transaction safety retained).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.learning.observation import ExecutionObservation, ObservationStatus
from app.models.enigma_profile import EnigmaProfile, KnowledgeProgress, CapabilityStatus

# Deterministic confidence update factors
_SUCCESS_BOOST_FACTOR = 0.12      # Increase confidence toward 1.0 by 12% of remaining gap
_FAILURE_PENALTY_FACTOR = 0.08    # Decrease confidence by 8% of current value
_CONFIDENCE_FLOOR = 0.0
_CONFIDENCE_CEILING = 1.0

# Evidence-based CapabilityStatus thresholds (TASK-017)
_STATUS_THRESHOLDS = [
    # (min_evidence, min_confidence, status)
    (10, 0.80, CapabilityStatus.PROVEN),
    (5,  0.65, CapabilityStatus.QUALIFIED),
    (3,  0.40, CapabilityStatus.PRACTICING),
    (1,  0.0,  CapabilityStatus.LEARNING),
]


def _derive_capability_status(evidence_count: int, confidence: float) -> CapabilityStatus:
    """
    Derive capability status deterministically from evidence counts and confidence.

    This function is the sole source of truth for CapabilityStatus —
    no external code (including the LLM) may set status directly.
    """
    if evidence_count == 0:
        return CapabilityStatus.UNKNOWN
    for min_ev, min_conf, status in _STATUS_THRESHOLDS:
        if evidence_count >= min_ev and confidence >= min_conf:
            return status
    return CapabilityStatus.LEARNING


class ProfileUpdater:
    """
    Updates ENIGMA's capability profile based on execution observations.

    TASK-017 compliance:
    - Confidence is derived from execution evidence, never from LLM output.
    - CapabilityStatus is computed deterministically.
    - Failure evidence is recorded but does not increase confidence.
    - Evidence counts (total, success, failure) are maintained.
    """

    async def update_capability_profile(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """
        Update ENIGMA's capability profile based on observation.

        Args:
            observation: ExecutionObservation from the learning loop
            db: Database session

        Returns:
            bool indicating success
        """
        if observation.status == ObservationStatus.FAILURE:
            return await self._record_failure(observation, db)
        return await self._record_success(observation, db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_or_create_knowledge_progress(
        self,
        db: AsyncSession,
        capability: str,
    ) -> KnowledgeProgress:
        """Get or create KnowledgeProgress for a capability."""
        # Ensure the global EnigmaProfile row exists
        result = await db.execute(
            select(EnigmaProfile).where(EnigmaProfile.profile_id == "enigma_profile")
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = EnigmaProfile(profile_id="enigma_profile")
            db.add(profile)
            await db.flush()

        result = await db.execute(
            select(KnowledgeProgress).where(
                KnowledgeProgress.profile_id == "enigma_profile",
                KnowledgeProgress.domain == capability,
            )
        )
        kp = result.scalar_one_or_none()
        if not kp:
            kp = KnowledgeProgress(
                profile_id="enigma_profile",
                domain=capability,
                capability_status=CapabilityStatus.UNKNOWN.value,
                evidence_count=0,
                successful_execution_count=0,
                failed_execution_count=0,
            )
            db.add(kp)
            await db.flush()
        return kp

    def _recompute_readiness(self, kp: KnowledgeProgress) -> None:
        """Recompute readiness as a weighted average of available scores."""
        kp.readiness = (
            (kp.knowledge_score or 0.0) * 0.30
            + (kp.execution_score or 0.0) * 0.30
            + (kp.evidence_score or 0.0) * 0.25
            + (kp.confidence or 0.0) * 0.15
        )

    async def _record_success(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """Record a successful capability execution."""
        try:
            kp = await self._get_or_create_knowledge_progress(db, observation.capability)

            # Increment evidence counters
            kp.evidence_count = (kp.evidence_count or 0) + 1
            kp.successful_execution_count = (kp.successful_execution_count or 0) + 1
            kp.last_success_at = observation.created_at

            # Evidence-based confidence boost
            current = kp.confidence or 0.0
            kp.confidence = min(
                _CONFIDENCE_CEILING,
                current + (1.0 - current) * _SUCCESS_BOOST_FACTOR,
            )

            # Update execution score (rolling toward observation quality)
            cur_exec = kp.execution_score or 0.0
            kp.execution_score = min(
                _CONFIDENCE_CEILING,
                cur_exec + (1.0 - cur_exec) * _SUCCESS_BOOST_FACTOR,
            )

            # Update evidence score based on observation confidence
            cur_ev = kp.evidence_score or 0.0
            delta = (observation.confidence - cur_ev) * 0.10
            kp.evidence_score = max(0.0, min(_CONFIDENCE_CEILING, cur_ev + delta))

            # Derive status deterministically — LLM cannot override this
            kp.capability_status = _derive_capability_status(
                kp.evidence_count, kp.confidence
            ).value

            self._recompute_readiness(kp)
            kp.freshness = "fresh"
            kp.last_verified = observation.created_at

            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False

    async def _record_failure(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """
        Record a failed capability execution.

        Failures increment evidence_count and failed_execution_count.
        Confidence is penalised slightly.
        CapabilityStatus is re-derived from updated values.
        Positive profile evidence is NOT written (TASK-016 / TASK-017 policy).
        """
        try:
            kp = await self._get_or_create_knowledge_progress(db, observation.capability)

            # Increment evidence counters
            kp.evidence_count = (kp.evidence_count or 0) + 1
            kp.failed_execution_count = (kp.failed_execution_count or 0) + 1

            # Confidence penalty on failure — floor at 0.0
            current = kp.confidence or 0.0
            kp.confidence = max(
                _CONFIDENCE_FLOOR,
                current - current * _FAILURE_PENALTY_FACTOR,
            )

            # Execution score decreases
            cur_exec = kp.execution_score or 0.0
            kp.execution_score = max(0.0, cur_exec - 0.05)

            # Re-derive status after penalty
            kp.capability_status = _derive_capability_status(
                kp.evidence_count, kp.confidence
            ).value

            self._recompute_readiness(kp)
            kp.freshness = "aging"

            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False
