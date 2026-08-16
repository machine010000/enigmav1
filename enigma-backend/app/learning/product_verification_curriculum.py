"""Controlled product-verification training through the shared runner boundary."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.master_brain.models import BrainAction, BrainDecision
from app.ai.master_brain.orchestrator import MasterBrain, master_brain
from app.engine.contracts import WorkerStatus
from app.learning.curriculum import TrainingEvaluation, TrainingMode, TrainingRunResult
from app.learning.observation import ExecutionObservation
from app.learning.promotion_service import CapabilityEvidencePromotionService
from app.models.enigma_profile import CapabilityStatus, KnowledgeProgress
from app.models.execution import WorkerExecution


class ProductVerificationTrainingRunner:
    capability = "product_verification"
    mode = TrainingMode.QUALIFICATION

    def __init__(self, *, mode: TrainingMode = TrainingMode.QUALIFICATION,
                 target_id: Optional[str] = None, plan_id: Optional[str] = None,
                 brain: Optional[MasterBrain] = None,
                 promotion_service: Optional[CapabilityEvidencePromotionService] = None) -> None:
        self.mode = TrainingMode(mode)
        self.target_id = target_id
        self.plan_id = plan_id
        self.brain = brain or master_brain
        self.promotion_service = promotion_service or CapabilityEvidencePromotionService()

    async def load_attempt_history(self, db: AsyncSession, user_id: str):
        rows = (await db.scalars(select(WorkerExecution).where(
            WorkerExecution.user_id == user_id,
            WorkerExecution.worker_name == self.capability,
        ).order_by(WorkerExecution.created_at))).all()
        return [row.result.get("_training") for row in rows
                if isinstance(row.result, dict) and row.result.get("_training")]

    async def _status(self, db: AsyncSession) -> str:
        row = await db.scalar(select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile",
            KnowledgeProgress.domain == self.capability,
        ))
        return row.capability_status if row else CapabilityStatus.UNKNOWN.value

    async def _replay(self, db: AsyncSession, user_id: str) -> Optional[TrainingRunResult]:
        if not self.plan_id:
            return None
        rows = (await db.scalars(select(WorkerExecution).where(
            WorkerExecution.user_id == user_id,
            WorkerExecution.worker_name == self.capability,
        ))).all()
        for row in rows:
            training = row.result.get("_training") if isinstance(row.result, dict) else None
            if isinstance(training, dict) and training.get("development_plan_id") == self.plan_id:
                return TrainingRunResult(
                    action="already_executed", execution_id=str(row.id),
                    capability_status=await self._status(db), attempts_run=0,
                    reason="development plan already executed",
                )
        return None

    @staticmethod
    def _evaluate(payload: Dict[str, Any]) -> TrainingEvaluation:
        result = payload.get("result") or {}
        evidence = payload.get("evidence") or []
        criteria = {
            "worker_success": 1.0 if payload.get("status") == WorkerStatus.SUCCESS.value else 0.0,
            "required_output": 1.0 if result.get("verified_name") and result.get("category") else 0.0,
            "evidence_present": 1.0 if evidence else 0.0,
            "quality": min(1.0, float(payload.get("confidence") or 0.0) / 0.65),
        }
        score = round(sum(criteria.values()) / len(criteria), 4)
        issues = [name for name, value in criteria.items() if value < 1.0]
        passed = all(value >= 1.0 for value in criteria.values())
        return TrainingEvaluation(passed=passed, score=score, criteria=criteria, issues=issues)

    async def run_next(self, db: AsyncSession, user_id: str,
                       mode: Optional[TrainingMode] = None) -> TrainingRunResult:
        selected_mode = TrainingMode(mode or self.mode)
        status = await self._status(db)
        replay = await self._replay(db, user_id)
        if replay:
            return replay
        if not self.target_id:
            return TrainingRunResult("blocked", capability_status=status,
                                     reason="owned target is required")
        if selected_mode == TrainingMode.ADVANCED and status != CapabilityStatus.QUALIFIED.value:
            return TrainingRunResult("requires_qualification", capability_status=status,
                                     reason="advanced training requires a qualified capability")
        if selected_mode == TrainingMode.REVALIDATION and status != CapabilityStatus.PROVEN.value:
            return TrainingRunResult("requires_proven", capability_status=status,
                                     reason="revalidation requires a proven capability")

        decision = BrainDecision(
            action=BrainAction.EXECUTE_CAPABILITY,
            intent=self.capability,
            capability=self.capability,
            target=self.target_id,
            reasoning_summary="Controlled product verification training",
            execution_required=True,
            execution_input={},
            confidence=1.0,
        )
        execution = await self.brain.execute_decision(decision, db=db, user_id=user_id)
        payload = execution.get("result") or {}
        evaluation = self._evaluate(payload)
        if not execution.get("execution_id") or not execution.get("worker_name"):
            return TrainingRunResult(
                action="retry", evaluation=evaluation,
                capability_status=status, attempts_run=1,
                reason="execution failed before a persisted worker result was created",
            )
        observation_payload = dict(payload)
        observation_payload["status"] = (
            WorkerStatus.SUCCESS.value if evaluation.passed else WorkerStatus.FAILED.value
        )
        observation_payload["confidence"] = evaluation.score
        observation = ExecutionObservation.from_worker_result(
            execution_id=execution.get("execution_id"), user_id=user_id,
            capability=self.capability, worker=execution.get("worker_name"),
            worker_result=observation_payload, target_id=self.target_id,
        )
        await self.brain.evidence_mapper.persist_observation(observation, db)
        await self.promotion_service.submit(
            observation, db, source="deterministic_product_verification_evaluator",
            training_mode=selected_mode.value, evaluation=evaluation,
        )
        record = await db.scalar(select(WorkerExecution).where(
            WorkerExecution.id == execution.get("execution_id")
        ))
        if record:
            stored = dict(record.result or {})
            stored["_training"] = {
                "capability": self.capability,
                "mode": selected_mode.value,
                "development_plan_id": self.plan_id,
                "target_id": self.target_id,
                "evaluation": evaluation.to_dict(),
                "recorded_at": datetime.utcnow().isoformat(),
            }
            record.result = stored
            await db.commit()
        return TrainingRunResult(
            action="advance" if evaluation.passed else "retry",
            execution_id=execution.get("execution_id"), evaluation=evaluation,
            capability_status=await self._status(db), attempts_run=1,
        )

    async def run(self, db: AsyncSession, user_id: str, max_attempts: int = 1,
                  mode: Optional[TrainingMode] = None):
        return [await self.run_next(db, user_id, mode=mode)]
