"""Policy-controlled bridge from opportunity gaps to existing training runners."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.capabilities import capability_registry
from app.engine.capability_catalog import CapabilityCatalog, capability_catalog
from app.freelancing.contracts import BrainReadinessDecision, OpportunityAssessment
from app.learning.curriculum import TrainingMode
from app.learning.runner_registry import (
    CapabilityRunnerRegistry,
    RunnerNotRegisteredError,
    capability_runner_registry,
)
from app.models.enigma_profile import CapabilityStatus, KnowledgeProgress
from app.models.product import Product


@dataclass(frozen=True)
class DevelopmentPlan:
    plan_id: str
    opportunity_id: str
    capability_id: str
    reason: str
    current_status: str
    current_confidence: float
    evidence_count: int
    required_threshold: float
    execution_available: bool
    recommended_training_mode: Optional[str]
    state: str
    current_freshness: str = "unknown"
    target_id: Optional[str] = None
    readiness_gap: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class DevelopmentPlanError(ValueError):
    pass


class StaleDevelopmentPlanError(DevelopmentPlanError):
    pass


class OpportunityDevelopmentBridge:
    TARGET_REQUIRED = {"product_verification"}

    def __init__(self, *, catalog: Optional[CapabilityCatalog] = None,
                 runners: Optional[CapabilityRunnerRegistry] = None) -> None:
        self.catalog = catalog or capability_catalog
        self.runners = runners or capability_runner_registry

    @staticmethod
    def _training_mode(status: str, freshness: str) -> Optional[TrainingMode]:
        if status in {
            CapabilityStatus.UNKNOWN.value,
            CapabilityStatus.LEARNING.value,
            CapabilityStatus.PRACTICING.value,
        }:
            return TrainingMode.QUALIFICATION
        if status == CapabilityStatus.QUALIFIED.value:
            return TrainingMode.ADVANCED
        if status == CapabilityStatus.PROVEN.value and freshness in {
            "due_for_revalidation", "stale"
        }:
            return TrainingMode.REVALIDATION
        return None

    async def generate(
        self, *, assessment: OpportunityAssessment,
        decision: BrainReadinessDecision, db: AsyncSession, user_id: str,
        target_id: Optional[str] = None,
    ) -> List[DevelopmentPlan]:
        blocking = decision.blocking_capability
        if not blocking or (
            blocking not in assessment.weak_capabilities
            and blocking not in assessment.missing_capabilities
        ):
            return []
        match = next((item for item in assessment.capability_matches
                      if item.required and item.capability == blocking and item.gap), None)
        if match is None:
            return []
        entry = self.catalog.get(blocking)
        if entry is None:
            return [self._blocked(assessment.opportunity_id, blocking,
                                  "Capability is not in the catalog")]
        progress = await db.scalar(select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile",
            KnowledgeProgress.domain == blocking,
        ))
        status = progress.capability_status if progress else CapabilityStatus.UNKNOWN.value
        confidence = float(progress.confidence or 0.0) if progress else 0.0
        evidence_count = int(progress.evidence_count or 0) if progress else 0
        freshness = str(progress.freshness or "unknown") if progress else "unknown"
        if confidence >= entry.freelance_readiness_threshold:
            return []

        resolution = capability_registry.resolve_capability(blocking)
        executable = bool(entry.execution_available and resolution)
        try:
            self.runners.resolve(blocking)
        except RunnerNotRegisteredError:
            executable = False

        owned_target = None
        reason = decision.reasoning
        if blocking in self.TARGET_REQUIRED:
            if not target_id:
                executable = False
                reason = "An authenticated-user-owned target is required"
            else:
                product = await db.scalar(select(Product).where(
                    Product.id == target_id, Product.user_id == user_id,
                ))
                if product is None:
                    raise DevelopmentPlanError("owned target not found")
                owned_target = str(product.id)

        mode = self._training_mode(status, freshness) if executable else None
        state = "executable" if mode else "blocked"
        if executable and mode is None:
            reason = "Lifecycle policy does not allow training in the current state"
        plan_id = self._plan_id(
            assessment.opportunity_id, user_id, blocking, owned_target,
            status, confidence, evidence_count, mode,
        )
        return [DevelopmentPlan(
            plan_id=plan_id, opportunity_id=assessment.opportunity_id,
            capability_id=blocking, reason=reason,
            current_status=status, current_confidence=confidence,
            evidence_count=evidence_count,
            required_threshold=entry.freelance_readiness_threshold,
            execution_available=bool(executable and mode),
            recommended_training_mode=mode.value if mode else None,
            state=state, current_freshness=freshness, target_id=owned_target,
            readiness_gap=round(max(0.0, entry.freelance_readiness_threshold - confidence), 4),
        )]

    async def execute(self, plan: DevelopmentPlan, *, db: AsyncSession,
                      user_id: str):
        if plan.state != "executable" or not plan.recommended_training_mode:
            raise DevelopmentPlanError("development plan is not executable")
        if plan.capability_id in self.TARGET_REQUIRED:
            product = await db.scalar(select(Product).where(
                Product.id == plan.target_id, Product.user_id == user_id,
            ))
            if product is None:
                raise DevelopmentPlanError("owned target not found")
        progress = await db.scalar(select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile",
            KnowledgeProgress.domain == plan.capability_id,
        ))
        current = (
            progress.capability_status if progress else CapabilityStatus.UNKNOWN.value,
            round(float(progress.confidence or 0.0), 10) if progress else 0.0,
            int(progress.evidence_count or 0) if progress else 0,
            str(progress.freshness or "unknown") if progress else "unknown",
        )
        expected = (
            plan.current_status, round(plan.current_confidence, 10),
            plan.evidence_count, plan.current_freshness,
        )
        if current != expected:
            raise StaleDevelopmentPlanError("capability profile changed; regenerate plan")
        runner = self.runners.resolve(
            plan.capability_id,
            mode=TrainingMode(plan.recommended_training_mode),
            target_id=plan.target_id,
            plan_id=plan.plan_id,
        )
        return await runner.run_next(
            db, user_id, mode=TrainingMode(plan.recommended_training_mode)
        )

    @staticmethod
    def _plan_id(opportunity_id: str, user_id: str, capability_id: str,
                 target_id: Optional[str], status: str, confidence: float,
                 evidence_count: int, mode: Optional[TrainingMode]) -> str:
        raw = "|".join(map(str, (
            opportunity_id, user_id, capability_id, target_id or "", status,
            round(confidence, 10), evidence_count, mode.value if mode else "blocked",
        )))
        return "dev_" + hashlib.sha256(raw.encode()).hexdigest()[:24]

    @staticmethod
    def _blocked(opportunity_id: str, capability_id: str,
                 reason: str) -> DevelopmentPlan:
        return DevelopmentPlan(
            plan_id="dev_" + hashlib.sha256(
                f"{opportunity_id}|{capability_id}|blocked".encode()
            ).hexdigest()[:24],
            opportunity_id=opportunity_id, capability_id=capability_id,
            reason=reason, current_status=CapabilityStatus.UNKNOWN.value,
            current_confidence=0.0, evidence_count=0, required_threshold=0.65,
            execution_available=False, recommended_training_mode=None,
            state="blocked",
        )
