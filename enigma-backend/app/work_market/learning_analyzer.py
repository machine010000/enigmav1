from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from app.work_market.models import JobEvaluation, LearningRequirement


class LearningAnalyzer:
    """Analyzes job evaluation to create learning requirements."""

    def create_learning_requirement(self, evaluation: JobEvaluation) -> LearningRequirement:
        """Create learning requirement from job evaluation."""
        research_tasks = self._generate_research_tasks(evaluation.missing_knowledge)
        academy_modules = self._suggest_academy_modules(evaluation.missing_knowledge)
        priority = self._determine_priority(evaluation)
        effort = self._determine_effort(evaluation)

        return LearningRequirement(
            job_id=evaluation.job_id,
            missing_knowledge=evaluation.missing_knowledge,
            missing_skills=evaluation.missing_skills,
            missing_capabilities=evaluation.missing_capabilities,
            research_tasks=research_tasks,
            academy_modules=academy_modules,
            priority=priority,
            estimated_learning_effort=effort,
        )

    def _generate_research_tasks(self, missing_knowledge: List[str]) -> List[str]:
        """Generate research tasks for missing knowledge."""
        tasks = []
        for knowledge in missing_knowledge:
            tasks.append(f"Research {knowledge}")
            tasks.append(f"Find best practices for {knowledge}")
        return tasks

    def _suggest_academy_modules(self, missing_knowledge: List[str]) -> List[str]:
        """Suggest academy modules for missing knowledge."""
        modules = []
        for knowledge in missing_knowledge:
            modules.append(f"{knowledge} Fundamentals")
            modules.append(f"Advanced {knowledge}")
        return modules

    def _determine_priority(self, evaluation: JobEvaluation) -> str:
        """Determine learning priority based on evaluation."""
        if evaluation.success_probability > 0.7:
            return "low"
        elif evaluation.success_probability > 0.5:
            return "medium"
        return "high"

    def _determine_effort(self, evaluation: JobEvaluation) -> str:
        """Determine estimated learning effort."""
        if evaluation.missing_knowledge:
            return "high"
        elif evaluation.missing_skills:
            return "medium"
        return "low"
