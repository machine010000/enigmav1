from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.work_market.models import (
    FreelanceJob,
    JobClassification,
    JobEvaluation,
    ApplicationDraft,
)


class ApplicationDraftGenerator:
    """Generates application drafts for evaluated jobs."""

    def generate_draft(self, job: FreelanceJob, classification: JobClassification, evaluation: JobEvaluation) -> ApplicationDraft:
        """Generate an application draft."""
        understanding = self._generate_understanding(job, classification)
        approach = self._generate_approach(job, classification)
        capabilities = self._identify_capabilities(classification)
        experience = self._identify_experience(classification)
        deliverables = classification.expected_deliverables
        timeline = self._estimate_timeline(classification)
        questions = self._generate_questions(job, classification)
        confidence = evaluation.success_probability
        risks = self._identify_risks(evaluation)

        return ApplicationDraft(
            job_id=job.job_id,
            profession=classification.profession,
            understanding_of_task=understanding,
            proposed_approach=approach,
            relevant_capabilities=capabilities,
            relevant_experience=experience,
            deliverables=deliverables,
            estimated_timeline=timeline,
            questions_for_client=questions,
            confidence=confidence,
            risks=risks,
        )

    def _generate_understanding(self, job: FreelanceJob, classification: JobClassification) -> str:
        """Generate understanding of the task."""
        return (
            f"The client needs a {classification.task} in the {classification.profession} domain. "
            f"Key requirements include: {', '.join(classification.required_skills[:3])}. "
            f"Expected deliverables: {', '.join(classification.expected_deliverables[:3])}."
        )

    def _generate_approach(self, job: FreelanceJob, classification: JobClassification) -> str:
        """Generate proposed approach."""
        return (
            f"I will approach this {classification.task} by first analyzing the requirements, "
            f"then applying my {classification.profession} expertise to deliver high-quality results. "
            f"Key focus areas: {', '.join(classification.required_capabilities[:3])}."
        )

    def _identify_capabilities(self, classification: JobClassification) -> List[str]:
        """Identify relevant capabilities."""
        return classification.required_capabilities

    def _identify_experience(self, classification: JobClassification) -> List[str]:
        """Identify relevant experience."""
        # For now, return empty as we don't track experience yet
        return []

    def _estimate_timeline(self, classification: JobClassification) -> str:
        """Estimate timeline based on complexity and effort."""
        if classification.estimated_effort == "high":
            return "2-4 weeks"
        elif classification.estimated_effort == "medium":
            return "1-2 weeks"
        return "3-7 days"

    def _generate_questions(self, job: FreelanceJob, classification: JobClassification) -> List[str]:
        """Generate questions for the client."""
        questions = [
            "What is the target audience for this project?",
            "Are there any specific tools or platforms you prefer?",
            "What is your expected timeline for this project?",
            "Do you have any existing materials or assets to work with?",
        ]
        return questions

    def _identify_risks(self, evaluation: JobEvaluation) -> List[str]:
        """Identify potential risks."""
        risks = []

        if evaluation.risk_score > 0.6:
            risks.append("Project complexity may lead to scope creep")

        if evaluation.skill_match < 0.5:
            risks.append("Missing required skills may impact quality")

        if evaluation.knowledge_match < 0.5:
            risks.append("Missing domain knowledge may require additional research")

        return risks
