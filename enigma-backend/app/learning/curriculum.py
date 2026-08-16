"""Structured, bounded training for the keyword_research capability."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.master_brain.orchestrator import MasterBrain, master_brain
from app.engine.contracts import WorkerStatus
from app.learning.observation import ExecutionObservation, ObservationStatus
from app.learning.revalidation import CapabilityRevalidationPolicy, EvidenceFreshness
from app.learning.promotion_service import CapabilityEvidencePromotionService
from app.models.enigma_profile import CapabilityStatus, KnowledgeProgress
from app.models.execution import WorkerExecution


@dataclass(frozen=True)
class CurriculumTask:
    level: int
    name: str
    task_id: str
    topic: str
    seed_keywords: List[str]
    market: str
    goal: str
    audience: str
    business_model: str
    minimum_keywords: int
    required_intents: List[str] = field(default_factory=list)

    def execution_input(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "seed_keywords": list(self.seed_keywords),
            "market": self.market,
            "goal": self.goal,
            "audience": self.audience,
            "business_model": self.business_model,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {**self.execution_input(), "level": self.level, "name": self.name,
                "task_id": self.task_id, "minimum_keywords": self.minimum_keywords,
                "required_intents": list(self.required_intents)}


@dataclass(frozen=True)
class CurriculumLevel:
    level: int
    name: str
    tasks: List[CurriculumTask]
    required_passes: int = 1


@dataclass(frozen=True)
class TrainingEvaluation:
    passed: bool
    score: float
    criteria: Dict[str, float]
    issues: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"passed": self.passed, "score": self.score,
                "criteria": dict(self.criteria), "issues": list(self.issues)}


@dataclass(frozen=True)
class TrainingRunResult:
    action: str
    task: Optional[CurriculumTask] = None
    execution_id: Optional[str] = None
    evaluation: Optional[TrainingEvaluation] = None
    capability_status: Optional[str] = None
    attempts_run: int = 0
    reason: Optional[str] = None


class TrainingMode(str, Enum):
    QUALIFICATION = "qualification_training"
    ADVANCED = "advanced_training"
    REVALIDATION = "revalidation_training"


class KeywordResearchCurriculum:
    """Deterministic fixtures spanning the current worker's real contract."""

    capability = "keyword_research"

    def __init__(self) -> None:
        definitions = [
            (1, "basic_discovery", [
                ("artisan coffee subscription", ["coffee subscription"], "global", "informational", "home coffee drinkers", "B2C"),
                ("cloud bookkeeping software", ["online bookkeeping"], "global", "commercial", "small businesses", "B2B"),
            ], 2, []),
            (2, "intent_classification", [
                ("eco friendly running shoes", ["sustainable trainers"], "US", "mixed", "environment-conscious runners", "B2C"),
                ("cybersecurity consulting", ["security audit service"], "UK", "transactional", "technology leaders", "B2B"),
            ], 3, ["informational", "commercial", "transactional", "navigational"]),
            (3, "prioritization", [
                ("meal planning application", ["weekly meal planner"], "global", "commercial", "busy families", "B2C"),
                ("warehouse inventory platform", ["inventory management system"], "US", "transactional", "operations managers", "B2B"),
            ], 4, []),
            (4, "business_context", [
                ("Arabic online mathematics tutoring", ["math tutor online"], "Egypt", "transactional", "parents of secondary students", "B2C"),
                ("GDPR compliance training", ["GDPR staff course"], "EU", "commercial", "HR and compliance teams", "B2B"),
            ], 4, []),
            (5, "strategic_mix", [
                ("premium organic skincare launch", ["organic face serum", "natural skincare"], "UK", "mixed", "quality-conscious adults", "B2C"),
                ("AI customer support platform", ["AI helpdesk", "support automation"], "global", "mixed", "SaaS support leaders", "B2B"),
            ], 5, []),
        ]
        self.levels: List[CurriculumLevel] = []
        for number, name, fixtures, minimum, intents in definitions:
            tasks = [CurriculumTask(number, name, f"kr-l{number}-v{index + 1}",
                                    *fixture, minimum, intents)
                     for index, fixture in enumerate(fixtures)]
            self.levels.append(CurriculumLevel(number, name, tasks))

    def select_task(self, attempts: List[Dict[str, Any]]) -> Optional[CurriculumTask]:
        for level in self.levels:
            level_attempts = [a for a in attempts if a.get("level") == level.level]
            passes = sum(bool(a.get("evaluation", {}).get("passed")) for a in level_attempts)
            if passes < level.required_passes:
                return level.tasks[len(level_attempts) % len(level.tasks)]
        return None


class AdvancedKeywordResearchCurriculum(KeywordResearchCurriculum):
    """Harder, deliberately diverse tasks for QUALIFIED -> PROVEN practice."""

    def __init__(self) -> None:
        fixtures = [
            (6, "ambiguous_product", "kr-adv-ambiguous", "Pulse workspace",
             ["team pulse", "workspace insights"], "global", "mixed",
             "people leaders and distributed teams", "B2B"),
            (7, "narrow_b2b_niche", "kr-adv-niche", "cold-chain sensor calibration service",
             ["cold chain calibration", "temperature sensor compliance"], "EU", "transactional",
             "pharmaceutical logistics quality managers", "B2B"),
            (8, "market_conflict", "kr-adv-market", "Arabic-English legal translation",
             ["legal translation service", "Arabic contract translation"], "Egypt and UK", "mixed",
             "local law firms and international compliance teams", "B2B"),
            (9, "multiple_audiences", "kr-adv-audience", "modular urban balcony garden kit",
             ["balcony garden kit", "small space gardening"], "US", "mixed",
             "first-time renters and experienced urban gardeners", "B2C"),
            (10, "strategic_portfolio", "kr-adv-portfolio", "privacy-first family finance application",
             ["family budget app", "private finance tracker"], "global", "mixed",
             "privacy-conscious parents and young adults", "B2C"),
        ]
        self.levels = [
            CurriculumLevel(level, name, [CurriculumTask(
                level, name, task_id, topic, seeds, market, goal, audience,
                model, 5, ["informational", "commercial", "transactional", "navigational"],
            )])
            for level, name, task_id, topic, seeds, market, goal, audience, model in fixtures
        ]

    @staticmethod
    def diversity_key(task: CurriculumTask) -> tuple:
        return (task.name, task.market, task.business_model, task.audience, task.goal)

    def select_task(self, attempts: List[Dict[str, Any]]) -> Optional[CurriculumTask]:
        passed_keys = {
            (a.get("task", {}).get("name"), a.get("task", {}).get("market"),
             a.get("task", {}).get("business_model"), a.get("task", {}).get("audience"),
             a.get("task", {}).get("goal"))
            for a in attempts
            if a.get("mode") == TrainingMode.ADVANCED.value
            and a.get("evaluation", {}).get("passed")
        }
        for level in self.levels:
            task = level.tasks[0]
            if self.diversity_key(task) not in passed_keys:
                return task
        return None

    def select_revalidation_task(self, attempts: List[Dict[str, Any]]) -> CurriculumTask:
        """Prefer unused diversity, then rotate the least-recently validated task."""
        unused = self.select_task(attempts)
        if unused is not None:
            return unused
        last_used: Dict[str, str] = {}
        for attempt in attempts:
            task_id = attempt.get("task_id")
            if task_id and attempt.get("evaluation", {}).get("passed"):
                last_used[task_id] = max(last_used.get(task_id, ""), attempt.get("recorded_at", ""))
        tasks = [level.tasks[0] for level in self.levels]
        return min(tasks, key=lambda task: last_used.get(task.task_id, ""))


class KeywordResearchTrainingEvaluator:
    """Scores worker output against capability-relevant deterministic criteria."""

    pass_threshold = 0.65

    advanced_pass_threshold = 0.78

    def evaluate(self, task: CurriculumTask, result: Dict[str, Any], *, advanced: bool = False) -> TrainingEvaluation:
        primary = result.get("primary_keywords") or []
        secondary = result.get("secondary_keywords") or []
        keywords = primary + secondary
        intents = {str(k.get("intent", "")).lower() for k in keywords}
        relevance_values = [float(k.get("relevance", 0.0)) for k in keywords]

        criteria = {
            "relevance": min(1.0, sum(relevance_values) / len(relevance_values)) if relevance_values else 0.0,
            "intent_classification": (
                len(intents.intersection(task.required_intents)) / len(task.required_intents)
                if task.required_intents else (1.0 if intents and intents != {"unknown"} else 0.0)
            ),
            "prioritization": 1.0 if primary and all(k.get("priority") for k in keywords) else 0.0,
            "completeness": min(1.0, len(keywords) / task.minimum_keywords),
            "business_context": sum([
                result.get("topic") == task.topic,
                result.get("market") == task.market,
                result.get("goal") == task.goal,
            ]) / 3.0,
            "useful_structure": 1.0 if all(
                key in result for key in ("primary_keywords", "secondary_keywords", "intent_summary", "confidence")
            ) else 0.0,
        }
        score = round(sum(criteria.values()) / len(criteria), 4)
        issues = [name for name, value in criteria.items() if value < 0.5]
        threshold = self.advanced_pass_threshold if advanced else self.pass_threshold
        if advanced and criteria["intent_classification"] < 0.75:
            issues.append("advanced_intent_diversity")
        passed = score >= threshold and (not advanced or criteria["intent_classification"] >= 0.75)
        return TrainingEvaluation(passed, score, criteria, issues)


class KeywordResearchTrainingRunner:
    """Runs evaluated curriculum attempts through Brain -> Engine -> Registry."""

    capability = "keyword_research"
    training_request = "perform keyword research training"
    max_attempts_per_run = 3
    max_failures_per_level = 2

    def __init__(self, brain: Optional[MasterBrain] = None,
                 mode: TrainingMode = TrainingMode.QUALIFICATION,
                 promotion_service: Optional[CapabilityEvidencePromotionService] = None) -> None:
        self.brain = brain or master_brain
        self.mode = TrainingMode(mode)
        self.curriculum = KeywordResearchCurriculum()
        self.advanced_curriculum = AdvancedKeywordResearchCurriculum()
        self.evaluator = KeywordResearchTrainingEvaluator()
        self.revalidation_policy = CapabilityRevalidationPolicy()
        self.promotion_service = promotion_service or CapabilityEvidencePromotionService()

    async def _attempt_history(self, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        rows = (await db.execute(
            select(WorkerExecution).where(
                WorkerExecution.user_id == user_id,
                WorkerExecution.worker_name == self.capability,
            ).order_by(WorkerExecution.created_at)
        )).scalars().all()
        return [row.result.get("_training") for row in rows
                if isinstance(row.result, dict) and isinstance(row.result.get("_training"), dict)]

    async def load_attempt_history(self, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """Public read boundary used by freshness/revalidation services."""
        return await self._attempt_history(db, user_id)

    async def _status(self, db: AsyncSession) -> Optional[str]:
        row = await db.scalar(select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile",
            KnowledgeProgress.domain == self.capability,
        ))
        return row.capability_status if row else CapabilityStatus.UNKNOWN.value

    async def run_next(self, db: AsyncSession, user_id: str,
                       mode: Optional[TrainingMode] = None) -> TrainingRunResult:
        selected_mode = TrainingMode(mode or self.mode)
        status = await self._status(db)
        if selected_mode == TrainingMode.QUALIFICATION and status in {
            CapabilityStatus.QUALIFIED.value, CapabilityStatus.PROVEN.value
        }:
            return TrainingRunResult("stop_qualified", capability_status=status,
                                     reason="existing evidence already satisfies qualification")
        if selected_mode == TrainingMode.ADVANCED and status == CapabilityStatus.PROVEN.value:
            return TrainingRunResult("stop_proven", capability_status=status,
                                     reason="existing evidence already satisfies proven status")
        if selected_mode == TrainingMode.ADVANCED and status != CapabilityStatus.QUALIFIED.value:
            return TrainingRunResult("requires_qualification", capability_status=status,
                                     reason="advanced training requires a qualified capability")

        attempts = await self._attempt_history(db, user_id)
        if selected_mode == TrainingMode.REVALIDATION:
            if status != CapabilityStatus.PROVEN.value:
                return TrainingRunResult("requires_proven", capability_status=status,
                                         reason="revalidation requires a proven capability")
            progress = await db.scalar(select(KnowledgeProgress).where(
                KnowledgeProgress.profile_id == "enigma_profile",
                KnowledgeProgress.domain == self.capability,
            ))
            freshness = self.revalidation_policy.assess(self.capability, progress, attempts)
            if freshness.state == EvidenceFreshness.FRESH:
                return TrainingRunResult("fresh_no_action", capability_status=status,
                                         reason=freshness.reason)

        curriculum = self.advanced_curriculum if selected_mode in {
            TrainingMode.ADVANCED, TrainingMode.REVALIDATION
        } else self.curriculum
        history_modes = ({TrainingMode.ADVANCED.value, TrainingMode.REVALIDATION.value}
                         if selected_mode == TrainingMode.REVALIDATION else {selected_mode.value})
        mode_attempts = [a for a in attempts if a.get(
            "mode", TrainingMode.QUALIFICATION.value) in history_modes]
        task = (curriculum.select_revalidation_task(mode_attempts)
                if selected_mode == TrainingMode.REVALIDATION
                else curriculum.select_task(mode_attempts))
        if task is None:
            return TrainingRunResult("curriculum_complete", capability_status=status,
                                     reason="all curriculum levels passed")

        failures = sum(1 for a in attempts if a.get("level") == task.level
                       and not a.get("evaluation", {}).get("passed", False))
        if failures >= self.max_failures_per_level:
            return TrainingRunResult("intervention_required", task=task,
                                     capability_status=status,
                                     reason="repeated evaluation failures at this level")

        decision = self.brain.decide_capability(self.training_request, context=task.execution_input())
        execution = await self.brain.execute_decision(decision, db=db, user_id=user_id)
        payload = execution.get("result", {})
        worker_output = payload.get("result", {})
        evaluation = self.evaluator.evaluate(
            task, worker_output, advanced=selected_mode == TrainingMode.ADVANCED
        )

        observation_payload = dict(payload)
        observation_payload["status"] = (
            WorkerStatus.SUCCESS.value if evaluation.passed else WorkerStatus.FAILED.value
        )
        evaluation_evidence = {
            "worker": self.capability,
            "field": "curriculum_evaluation",
            "value": evaluation.to_dict(),
            "source": "deterministic_curriculum_evaluator",
            "confidence": evaluation.score,
            "timestamp": datetime.utcnow().isoformat(),
            "curriculum_level": task.level,
            "task_id": task.task_id,
        }
        observation_payload["evidence"] = list(payload.get("evidence") or []) + [evaluation_evidence]
        observation_payload["confidence"] = evaluation.score
        observation = ExecutionObservation.from_worker_result(
            execution_id=execution.get("execution_id"), user_id=user_id,
            capability=self.capability, worker=execution.get("worker_name"),
            worker_result=observation_payload,
        )

        await self.brain.evidence_mapper.persist_observation(observation, db)
        await self.promotion_service.submit(
            observation,
            db,
            source="deterministic_curriculum_evaluator",
            training_mode=selected_mode.value,
            evaluation=evaluation,
        )

        record = await db.scalar(select(WorkerExecution).where(
            WorkerExecution.id == execution.get("execution_id")))
        if record:
            stored_result = dict(record.result or {})
            stored_result["_training"] = {
                "capability": self.capability,
                "mode": selected_mode.value,
                "level": task.level,
                "task_id": task.task_id,
                "task": task.to_dict(),
                "evaluation": evaluation.to_dict(),
                "worker_status": payload.get("status"),
                "recorded_at": datetime.utcnow().isoformat(),
            }
            record.result = stored_result
            await db.commit()

        updated_status = await self._status(db)
        return TrainingRunResult(
            "advance" if evaluation.passed else "retry",
            task=task, execution_id=execution.get("execution_id"),
            evaluation=evaluation, capability_status=updated_status, attempts_run=1,
        )

    async def run(self, db: AsyncSession, user_id: str,
                  max_attempts: int = max_attempts_per_run,
                  mode: Optional[TrainingMode] = None) -> List[TrainingRunResult]:
        limit = max(1, min(max_attempts, self.max_attempts_per_run))
        results: List[TrainingRunResult] = []
        for _ in range(limit):
            result = await self.run_next(db, user_id, mode=mode)
            results.append(result)
            if result.action in {"stop_qualified", "stop_proven", "requires_qualification",
                                 "requires_proven", "fresh_no_action", "curriculum_complete",
                                 "intervention_required", "retry"}:
                break
        return results
