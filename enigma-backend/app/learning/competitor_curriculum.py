"""Competitor-research curricula using the existing bounded training lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.ai.master_brain.orchestrator import MasterBrain, master_brain
from app.learning.curriculum import (
    CurriculumLevel, KeywordResearchTrainingRunner, TrainingEvaluation, TrainingMode,
)
from app.learning.revalidation import CapabilityRevalidationPolicy
from app.learning.promotion_service import CapabilityEvidencePromotionService


@dataclass(frozen=True)
class CompetitorCurriculumTask:
    level: int
    name: str
    task_id: str
    business: str
    industry: str
    market: str
    audience: str
    goal: str
    business_model: str
    competitors: List[Dict[str, Any]]
    minimum_competitors: int = 2

    def execution_input(self) -> Dict[str, Any]:
        return {"business": self.business, "industry": self.industry, "market": self.market,
                "audience": self.audience, "goal": self.goal,
                "business_model": self.business_model,
                "competitors": [dict(item) for item in self.competitors]}

    def to_dict(self) -> Dict[str, Any]:
        return {**self.execution_input(), "level": self.level, "name": self.name,
                "task_id": self.task_id, "minimum_competitors": self.minimum_competitors}


def _competitors(prefix: str, count: int = 2) -> List[Dict[str, Any]]:
    return [{
        "name": f"{prefix} {index + 1}",
        "positioning": "specialist" if index % 2 == 0 else "accessible generalist",
        "offer": "managed service" if index % 2 == 0 else "self-service product",
        "audience": "focused buyer segment",
        "strengths": ["clear offer", "established distribution"],
        "weaknesses": [f"limited segment coverage {index + 1}", "generic onboarding"],
        "differentiators": [f"delivery model {index + 1}", "category expertise"],
    } for index in range(count)]


class CompetitorResearchCurriculum:
    capability = "competitor_research"

    def __init__(self) -> None:
        fixtures = [
            (1, "identify_competitors", "artisan coffee membership", "food retail", "Egypt", "home brewers", "identify alternatives", "B2C"),
            (2, "compare_positioning", "cloud bookkeeping platform", "fintech SaaS", "UK", "small firms", "compare offers", "B2B"),
            (3, "swot_differentiation", "sustainable running shoe", "consumer footwear", "US", "eco-conscious runners", "find differentiation", "B2C"),
            (4, "market_context", "cold-chain compliance service", "pharma logistics", "EU", "quality leaders", "assess market context", "B2B"),
            (5, "strategic_analysis", "Arabic mathematics tutoring", "education", "Egypt", "secondary-school parents", "shape launch strategy", "B2C"),
        ]
        self.levels = []
        for level, name, business, industry, market, audience, goal, model in fixtures:
            tasks = [CompetitorCurriculumTask(
                level, name, f"cr-l{level}-v{variant}", business, industry, market,
                audience, goal, model, _competitors(f"{name.title()} Controlled", 2 + (level >= 3)), 2,
            ) for variant in (1, 2)]
            self.levels.append(CurriculumLevel(level, name, tasks, required_passes=2))

    def select_task(self, attempts: List[Dict[str, Any]]) -> Optional[CompetitorCurriculumTask]:
        for level in self.levels:
            level_attempts = [a for a in attempts if a.get("level") == level.level]
            passes = sum(bool(a.get("evaluation", {}).get("passed")) for a in level_attempts)
            if passes < level.required_passes:
                return level.tasks[len(level_attempts) % len(level.tasks)]
        return None


class AdvancedCompetitorResearchCurriculum(CompetitorResearchCurriculum):
    def __init__(self) -> None:
        fixtures = [
            (6, "ambiguous_category", "Pulse collaboration workspace", "work technology", "global", "people leaders and teams", "resolve category ambiguity", "B2B"),
            (7, "narrow_regulated_niche", "sensor calibration advisory", "pharma logistics", "EU", "quality managers", "find defensible positioning", "B2B"),
            (8, "multi_market", "Arabic-English legal translation", "professional services", "Egypt and UK", "law and compliance teams", "compare market-specific rivals", "B2B"),
            (9, "multiple_audiences", "urban balcony garden kit", "home gardening", "US", "renters and experienced gardeners", "separate competitive sets", "B2C"),
            (10, "strategic_portfolio", "privacy-first family finance app", "consumer fintech", "global", "parents and young adults", "recommend portfolio strategy", "B2C"),
        ]
        self.levels = [CurriculumLevel(level, name, [CompetitorCurriculumTask(
            level, name, f"cr-adv-{level}", business, industry, market, audience, goal,
            model, _competitors(f"{name.title()} Controlled", 4), 3,
        )]) for level, name, business, industry, market, audience, goal, model in fixtures]

    @staticmethod
    def diversity_key(task: CompetitorCurriculumTask) -> tuple:
        return task.name, task.market, task.business_model, task.audience, task.goal

    def select_task(self, attempts: List[Dict[str, Any]]) -> Optional[CompetitorCurriculumTask]:
        passed = {a.get("task_id") for a in attempts
                  if a.get("mode") == TrainingMode.ADVANCED.value
                  and a.get("evaluation", {}).get("passed")}
        return next((level.tasks[0] for level in self.levels if level.tasks[0].task_id not in passed), None)

    def select_revalidation_task(self, attempts: List[Dict[str, Any]]) -> CompetitorCurriculumTask:
        unused = self.select_task(attempts)
        if unused:
            return unused
        latest = {a.get("task_id"): a.get("recorded_at", "") for a in attempts
                  if a.get("evaluation", {}).get("passed")}
        return min((level.tasks[0] for level in self.levels), key=lambda task: latest.get(task.task_id, ""))


class CompetitorResearchTrainingEvaluator:
    pass_threshold = 0.65
    advanced_pass_threshold = 0.78

    def evaluate(self, task: CompetitorCurriculumTask, result: Dict[str, Any], *, advanced: bool = False) -> TrainingEvaluation:
        competitors = result.get("competitors") or []
        names = [str(item.get("name", "")).strip().lower() for item in competitors]
        complete = [item for item in competitors if all(key in item for key in
                    ("positioning", "offer", "strengths", "weaknesses", "differentiators"))]
        implications = result.get("strategic_implications") or []
        criteria = {
            "competitor_relevance": min(1.0, len(competitors) / task.minimum_competitors),
            "factual_internal_consistency": 1.0 if names and len(names) == len(set(names))
                and all(item.get("source") == "caller_supplied_controlled_context" for item in competitors) else 0.0,
            "completeness": len(complete) / len(competitors) if competitors else 0.0,
            "comparison_quality": min(1.0, len(result.get("comparison") or []) / max(1, len(competitors))),
            "business_context": sum((result.get("business") == task.business,
                                      result.get("market") == task.market,
                                      result.get("goal") == task.goal)) / 3.0,
            "strategic_output": min(1.0, len(implications) / 3),
            "useful_structure": 1.0 if all(key in result for key in
                ("competitors", "comparison", "market_observations", "strategic_implications", "research_scope")) else 0.0,
        }
        score = round(sum(criteria.values()) / len(criteria), 4)
        issues = [name for name, value in criteria.items() if value < 0.5]
        threshold = self.advanced_pass_threshold if advanced else self.pass_threshold
        passed = score >= threshold and (not advanced or criteria["strategic_output"] >= 0.75)
        return TrainingEvaluation(passed, score, criteria, issues)


class CompetitorResearchTrainingRunner(KeywordResearchTrainingRunner):
    capability = "competitor_research"
    training_request = "perform competitor research training"

    def __init__(self, brain: Optional[MasterBrain] = None,
                 mode: TrainingMode = TrainingMode.QUALIFICATION,
                 promotion_service: Optional[CapabilityEvidencePromotionService] = None) -> None:
        self.brain = brain or master_brain
        self.mode = TrainingMode(mode)
        self.curriculum = CompetitorResearchCurriculum()
        self.advanced_curriculum = AdvancedCompetitorResearchCurriculum()
        self.evaluator = CompetitorResearchTrainingEvaluator()
        self.revalidation_policy = CapabilityRevalidationPolicy()
        self.promotion_service = promotion_service or CapabilityEvidencePromotionService()
