"""Service boundary for capability freshness and explicit revalidation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.capability_catalog import capability_catalog
from app.learning.curriculum import TrainingMode
from app.learning.revalidation import CapabilityRevalidationPolicy
from app.learning.runner_registry import (
    CapabilityRunnerRegistry,
    RunnerNotRegisteredError,
    capability_runner_registry,
)
from app.models.enigma_profile import CapabilityStatus, KnowledgeProgress


class CapabilityNotFoundError(LookupError):
    pass


class CapabilityNotProvenError(ValueError):
    pass


class RevalidationPersistenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class CapabilityFreshnessView:
    capability: str
    status: str
    freshness: str
    last_success_at: Optional[str]
    last_verified: Optional[str]
    revalidation_interval_days: int
    stale_horizon_days: int
    advanced_diversity: int
    required_diversity: int
    revalidation_required: bool

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class RevalidationResponseData:
    capability: str
    status_before: str
    freshness_before: str
    action: str
    attempts_run: int
    success: bool
    evaluation_score: Optional[float]
    status_after: str
    freshness_after: str
    confidence: float
    evidence_count: int
    stop_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


class CapabilityRevalidationService:
    def __init__(self, registry: Optional[CapabilityRunnerRegistry] = None) -> None:
        self.registry = registry or capability_runner_registry
        self.policy = CapabilityRevalidationPolicy()

    def _runner_for(self, capability: str):
        try:
            return self.registry.resolve(capability, mode=TrainingMode.REVALIDATION)
        except RunnerNotRegisteredError:
            raise CapabilityNotFoundError(capability)

    async def _load_progress(self, db: AsyncSession, capability: str) -> KnowledgeProgress:
        entry = capability_catalog.get(capability)
        if (entry is None or not entry.execution_available
                or entry.revalidation_interval_days is None):
            raise CapabilityNotFoundError(capability)
        progress = await db.scalar(select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile",
            KnowledgeProgress.domain == capability,
        ))
        if progress is None:
            raise CapabilityNotFoundError(capability)
        return progress

    async def get_freshness(self, db: AsyncSession, user_id: str,
                            capability: str) -> CapabilityFreshnessView:
        progress = await self._load_progress(db, capability)
        attempts = await self._runner_for(capability).load_attempt_history(db, user_id)
        assessment = self.policy.assess(capability, progress, attempts)
        return CapabilityFreshnessView(
            capability=capability,
            status=progress.capability_status,
            freshness=assessment.state.value,
            last_success_at=progress.last_success_at.isoformat() if progress.last_success_at else None,
            last_verified=progress.last_verified.isoformat() if progress.last_verified else None,
            revalidation_interval_days=assessment.interval_days,
            stale_horizon_days=assessment.interval_days * 2,
            advanced_diversity=assessment.diversity_count,
            required_diversity=assessment.required_diversity,
            revalidation_required=assessment.state.value != "fresh",
        )

    async def request_revalidation(self, db: AsyncSession, user_id: str,
                                   capability: str) -> RevalidationResponseData:
        before = await self.get_freshness(db, user_id, capability)
        if before.status != CapabilityStatus.PROVEN.value:
            raise CapabilityNotProvenError(capability)

        try:
            result = await self._runner_for(capability).run_next(
                db, user_id, mode=TrainingMode.REVALIDATION
            )
        except (CapabilityNotFoundError, CapabilityNotProvenError):
            raise
        except Exception as exc:
            await db.rollback()
            raise RevalidationPersistenceError("revalidation could not be completed") from exc

        progress = await self._load_progress(db, capability)
        after = await self.get_freshness(db, user_id, capability)
        evaluation_score = result.evaluation.score if result.evaluation else None
        success = result.action in {"fresh_no_action", "advance", "stop_proven"}
        return RevalidationResponseData(
            capability=capability,
            status_before=before.status,
            freshness_before=before.freshness,
            action=result.action,
            attempts_run=result.attempts_run,
            success=success,
            evaluation_score=evaluation_score,
            status_after=progress.capability_status,
            freshness_after=after.freshness,
            confidence=float(progress.confidence or 0.0),
            evidence_count=int(progress.evidence_count or 0),
            stop_reason=result.reason,
        )
