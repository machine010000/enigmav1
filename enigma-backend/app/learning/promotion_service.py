"""Auditable boundary between owned executions and global capability progress."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.learning.observation import ExecutionObservation, ObservationStatus
from app.learning.profile_updater import _derive_capability_status
from app.models.capability_learning import CapabilityEvidenceContribution, SystemCapabilityProgress
from app.models.enigma_profile import EnigmaProfile, KnowledgeProgress
from app.models.execution import WorkerExecution


POLICY_VERSION = "capability-promotion-v1"
CONTROLLED_MODES = {"qualification_training", "advanced_training", "revalidation_training"}
SUCCESS_BOOST_FACTOR = 0.12
FAILURE_PENALTY_FACTOR = 0.08


@dataclass(frozen=True)
class PromotionResult:
    contribution_id: str
    decision_state: str
    eligibility_state: str
    progress_applied: bool
    duplicate: bool
    reason: str


class CapabilityEvidencePromotionService:
    """The only Phase-1 path allowed to mutate SystemCapabilityProgress."""

    async def submit(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
        *,
        source: str,
        training_mode: Optional[str] = None,
        evaluation: Optional[Any] = None,
        promoted_by: str = "promotion_policy",
    ) -> PromotionResult:
        execution_id = uuid.UUID(str(observation.execution_id))
        execution = await db.scalar(select(WorkerExecution).where(
            WorkerExecution.id == execution_id
        ))
        if execution is None:
            raise ValueError("contribution requires a persisted execution")

        owner_id = execution.user_id
        evaluation_data = self._evaluation_dict(evaluation)
        eligibility, decision, reason = self._decide(
            owner_id=owner_id,
            status=observation.status,
            training_mode=training_mode,
            evaluation=evaluation_data,
        )
        digest = self._digest(observation, evaluation_data)
        contribution_id = uuid.uuid4()
        now = datetime.utcnow()
        stmt = insert(CapabilityEvidenceContribution).values(
            id=contribution_id,
            execution_id=execution_id,
            user_id=owner_id,
            capability_id=observation.capability,
            source=source,
            training_mode=training_mode,
            observation_status=observation.status.value,
            evaluation_score=evaluation_data.get("score"),
            evidence_digest=digest,
            evidence_reference={
                "execution_id": str(execution_id),
                "evidence_count": len(observation.evidence),
                "evaluation": evaluation_data,
            },
            eligibility_state=eligibility,
            decision_state=decision,
            policy_version=POLICY_VERSION,
            decision_reason=reason,
            promoted_at=now if decision == "accepted" else None,
            promoted_by=promoted_by if decision == "accepted" else None,
            progress_applied=0,
            created_at=now,
        ).on_conflict_do_nothing(index_elements=["execution_id"]).returning(
            CapabilityEvidenceContribution.id
        )
        inserted_id = (await db.execute(stmt)).scalar_one_or_none()
        if inserted_id is None:
            existing = await db.scalar(select(CapabilityEvidenceContribution).where(
                CapabilityEvidenceContribution.execution_id == execution_id
            ))
            await db.commit()
            return PromotionResult(
                str(existing.id), existing.decision_state, existing.eligibility_state,
                bool(existing.progress_applied), True, existing.decision_reason,
            )

        applied = False
        if decision == "accepted":
            system, legacy = await self._lock_progress(db, observation.capability)
            prior_freshness = legacy.freshness
            self._apply(system, observation)
            self._apply(legacy, observation)
            if training_mode == "revalidation_training" and observation.status == ObservationStatus.FAILURE:
                revalidation_freshness = (
                    prior_freshness if prior_freshness in {"due_for_revalidation", "stale"}
                    else "due_for_revalidation"
                )
                system.freshness = revalidation_freshness
                legacy.freshness = revalidation_freshness
            system.version = (system.version or 0) + 1
            system.policy_version = POLICY_VERSION
            system.aggregate_source = "promotion_ledger"
            contribution = await db.scalar(select(CapabilityEvidenceContribution).where(
                CapabilityEvidenceContribution.id == inserted_id
            ))
            contribution.progress_applied = 1
            applied = True
        await db.commit()
        return PromotionResult(str(inserted_id), decision, eligibility, applied, False, reason)

    @staticmethod
    def _evaluation_dict(evaluation: Optional[Any]) -> Dict[str, Any]:
        if evaluation is None:
            return {}
        if isinstance(evaluation, dict):
            return dict(evaluation)
        if hasattr(evaluation, "to_dict"):
            return evaluation.to_dict()
        return {"passed": bool(getattr(evaluation, "passed", False)),
                "score": getattr(evaluation, "score", None)}

    @staticmethod
    def _decide(*, owner_id: Any, status: ObservationStatus,
                training_mode: Optional[str], evaluation: Dict[str, Any]) -> tuple[str, str, str]:
        if owner_id is None:
            return "ineligible", "rejected", "legacy execution has no attributable owner"
        if training_mode not in CONTROLLED_MODES:
            return "pending", "pending", "ordinary execution requires explicit promotion review"
        passed = evaluation.get("passed") is True
        if status != ObservationStatus.FAILURE and passed:
            return "eligible", "accepted", "controlled evaluation passed"
        if training_mode == "revalidation_training" and status == ObservationStatus.FAILURE:
            return "eligible", "accepted", "formal controlled revalidation failure"
        return "ineligible", "rejected", "controlled evaluation did not pass promotion policy"

    @staticmethod
    def _digest(observation: ExecutionObservation, evaluation: Dict[str, Any]) -> str:
        value = {"execution_id": observation.execution_id, "capability": observation.capability,
                 "status": observation.status.value, "evidence": observation.evidence,
                 "evaluation": evaluation}
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _lock_progress(self, db: AsyncSession, capability: str):
        system = await db.scalar(select(SystemCapabilityProgress).where(
            SystemCapabilityProgress.capability_id == capability
        ).with_for_update())
        legacy = await db.scalar(select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile",
            KnowledgeProgress.domain == capability,
        ).with_for_update())
        if legacy is None:
            profile = await db.scalar(select(EnigmaProfile).where(
                EnigmaProfile.profile_id == "enigma_profile"
            ).with_for_update())
            if profile is None:
                db.add(EnigmaProfile(profile_id="enigma_profile"))
                await db.flush()
            legacy = await db.scalar(select(KnowledgeProgress).where(
                KnowledgeProgress.profile_id == "enigma_profile",
                KnowledgeProgress.domain == capability,
            ).with_for_update())
            if legacy is None:
                legacy = KnowledgeProgress(profile_id="enigma_profile", domain=capability)
                db.add(legacy)
                await db.flush()
        if system is None:
            # Another transaction may have created the system row while this
            # transaction waited for the legacy capability lock.
            system = await db.scalar(select(SystemCapabilityProgress).where(
                SystemCapabilityProgress.capability_id == capability
            ).with_for_update())
        if system is None:
            system = SystemCapabilityProgress(
                capability_id=capability,
                knowledge_score=legacy.knowledge_score or 0.0,
                execution_score=legacy.execution_score or 0.0,
                evidence_score=legacy.evidence_score or 0.0,
                confidence=legacy.confidence or 0.0,
                readiness=legacy.readiness or 0.0,
                capability_status=legacy.capability_status or "unknown",
                evidence_count=legacy.evidence_count or 0,
                successful_execution_count=legacy.successful_execution_count or 0,
                failed_execution_count=legacy.failed_execution_count or 0,
                last_success_at=legacy.last_success_at,
                freelance_readiness_threshold=legacy.freelance_readiness_threshold or 0.65,
                last_verified=legacy.last_verified,
                freshness=legacy.freshness or "unknown",
                concepts=legacy.concepts or {},
                aggregate_source="legacy_runtime_seed",
            )
            db.add(system)
            await db.flush()
        return system, legacy

    @staticmethod
    def _apply(progress: Any, observation: ExecutionObservation) -> None:
        progress.evidence_count = (progress.evidence_count or 0) + 1
        if observation.status == ObservationStatus.FAILURE:
            progress.failed_execution_count = (progress.failed_execution_count or 0) + 1
            current = progress.confidence or 0.0
            progress.confidence = max(0.0, current - current * FAILURE_PENALTY_FACTOR)
            progress.execution_score = max(0.0, (progress.execution_score or 0.0) - 0.05)
            progress.freshness = "aging"
        else:
            progress.successful_execution_count = (progress.successful_execution_count or 0) + 1
            progress.last_success_at = observation.created_at
            current = progress.confidence or 0.0
            progress.confidence = min(1.0, current + (1.0 - current) * SUCCESS_BOOST_FACTOR)
            current_execution = progress.execution_score or 0.0
            progress.execution_score = min(
                1.0, current_execution + (1.0 - current_execution) * SUCCESS_BOOST_FACTOR
            )
            current_evidence = progress.evidence_score or 0.0
            progress.evidence_score = max(
                0.0, min(1.0, current_evidence + (observation.confidence - current_evidence) * 0.10)
            )
            progress.freshness = "fresh"
            progress.last_verified = observation.created_at
        progress.capability_status = _derive_capability_status(
            progress.evidence_count, progress.confidence
        ).value
        progress.readiness = (
            (progress.knowledge_score or 0.0) * 0.30
            + (progress.execution_score or 0.0) * 0.30
            + (progress.evidence_score or 0.0) * 0.25
            + (progress.confidence or 0.0) * 0.15
        )
