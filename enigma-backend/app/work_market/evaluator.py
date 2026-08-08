from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.work_market.models import (
    FreelanceJob,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
    LearningRequirement,
    ApplicationDraft,
)


class JobEvaluator:
    """Evaluates job suitability and produces explainable recommendations."""

    def __init__(self) -> None:
        self._skill_weights = {
            "SEO Specialist": ["Technical SEO", "Keyword Research", "Competitor Analysis"],
            "Content Writer": ["Content Writing", "SEO Writing", "Copywriting"],
            "Web Developer": ["HTML", "CSS", "JavaScript", "Responsive Design"],
            "Social Media Manager": ["Social Media", "Content Creation", "Analytics"],
            "Digital Marketer": ["Marketing", "Advertising", "Analytics"],
        }

    def evaluate(self, job: FreelanceJob, classification: JobClassification) -> JobEvaluation:
        """Evaluate a job's suitability."""
        profession_match = self._calculate_profession_match(classification)
        skill_match = self._calculate_skill_match(job, classification)
        knowledge_match = self._calculate_knowledge_match(classification)
        capability_match = self._calculate_capability_match(classification)
        complexity_score = self._calculate_complexity_score(classification)
        effort_score = self._calculate_effort_score(classification)
        earning_score = self._calculate_earning_score(job)
        success_probability = self._calculate_success_probability(
            profession_match, skill_match, knowledge_match, capability_match
        )
        risk_score = self._calculate_risk_score(job, classification)
        confidence = self._calculate_overall_confidence(
            profession_match, skill_match, knowledge_match, capability_match
        )

        missing_knowledge = self._identify_missing_knowledge(classification)
        missing_skills = self._identify_missing_skills(job, classification)
        missing_capabilities = self._identify_missing_capabilities(classification)

        recommendation, reason = self._determine_recommendation(
            profession_match, skill_match, knowledge_match, capability_match,
            success_probability, risk_score, missing_knowledge, missing_skills, missing_capabilities
        )

        return JobEvaluation(
            job_id=job.job_id,
            profession_match=profession_match,
            skill_match=skill_match,
            knowledge_match=knowledge_match,
            capability_match=capability_match,
            complexity_score=complexity_score,
            effort_score=effort_score,
            earning_score=earning_score,
            success_probability=success_probability,
            risk_score=risk_score,
            confidence=confidence,
            missing_knowledge=missing_knowledge,
            missing_skills=missing_skills,
            missing_capabilities=missing_capabilities,
            recommendation=recommendation,
            reason=reason,
        )

    def _calculate_profession_match(self, classification: JobClassification) -> float:
        """Calculate how well the job matches available professions."""
        if classification.profession == "UNKNOWN_PROFESSION":
            return 0.0
        return 0.8 if classification.confidence > 0.7 else 0.5

    def _calculate_skill_match(self, job: FreelanceJob, classification: JobClassification) -> float:
        """Calculate skill match percentage."""
        if not classification.required_skills:
            return 0.5

        matching_skills = set(job.skills) & set(classification.required_skills)
        return len(matching_skills) / len(classification.required_skills)

    def _calculate_knowledge_match(self, classification: JobClassification) -> float:
        """Calculate knowledge match percentage."""
        # For now, assume 0.5 as we don't track knowledge yet
        return 0.5

    def _calculate_capability_match(self, classification: JobClassification) -> float:
        """Calculate capability match percentage."""
        # For now, assume 0.5 as we don't track capabilities yet
        return 0.5

    def _calculate_complexity_score(self, classification: JobClassification) -> float:
        """Calculate complexity score (0-1)."""
        complexity_map = {"low": 0.3, "medium": 0.5, "high": 0.8}
        return complexity_map.get(classification.complexity, 0.5)

    def _calculate_effort_score(self, classification: JobClassification) -> float:
        """Calculate effort score (0-1)."""
        effort_map = {"low": 0.7, "medium": 0.5, "high": 0.3}
        return effort_map.get(classification.estimated_effort, 0.5)

    def _calculate_earning_score(self, job: FreelanceJob) -> float:
        """Calculate earning score based on budget."""
        if not job.budget:
            return 0.5

        # Normalize budget (0-1 for $0-$5000)
        return min(job.budget / 5000.0, 1.0)

    def _calculate_success_probability(
        self, profession_match: float, skill_match: float,
        knowledge_match: float, capability_match: float
    ) -> float:
        """Calculate overall success probability."""
        return (profession_match + skill_match + knowledge_match + capability_match) / 4

    def _calculate_risk_score(self, job: FreelanceJob, classification: JobClassification) -> float:
        """Calculate risk score (0-1, higher is riskier)."""
        risk = 0.3  # Base risk

        if classification.complexity == "high":
            risk += 0.3
        elif classification.complexity == "medium":
            risk += 0.2

        if classification.estimated_effort == "high":
            risk += 0.2

        return min(risk, 1.0)

    def _calculate_overall_confidence(
        self, profession_match: float, skill_match: float,
        knowledge_match: float, capability_match: float
    ) -> float:
        """Calculate overall confidence in evaluation."""
        return (profession_match + skill_match + knowledge_match + capability_match) / 4

    def _identify_missing_knowledge(self, classification: JobClassification) -> List[str]:
        """Identify missing knowledge areas."""
        # For now, return all required knowledge as missing
        return classification.required_knowledge

    def _identify_missing_skills(self, job: FreelanceJob, classification: JobClassification) -> List[str]:
        """Identify missing skills."""
        if not classification.required_skills:
            return []

        job_skills_lower = [s.lower() for s in job.skills]
        required_skills_lower = [s.lower() for s in classification.required_skills]

        missing = [skill for skill in required_skills_lower if skill not in job_skills_lower]
        return list(set(missing))

    def _identify_missing_capabilities(self, classification: JobClassification) -> List[str]:
        """Identify missing capabilities."""
        # For now, return all required capabilities as missing
        return classification.required_capabilities

    def _determine_recommendation(
        self, profession_match: float, skill_match: float,
        knowledge_match: float, capability_match: float,
        success_probability: float, risk_score: float,
        missing_knowledge: List[str], missing_skills: List[str],
        missing_capabilities: List[str]
    ) -> tuple[JobRecommendation, str]:
        """Determine recommendation with explanation."""
        # If missing critical knowledge or skills
        if missing_knowledge and success_probability < 0.6:
            return JobRecommendation.LEARN_FIRST, (
                f"Missing critical knowledge: {', '.join(missing_knowledge[:3])}. "
                f"Learn these before applying to increase success probability."
            )

        if missing_skills and skill_match < 0.5:
            return JobRecommendation.LEARN_FIRST, (
                f"Missing required skills: {', '.join(missing_skills[:3])}. "
                f"Acquire these skills to improve match."
            )

        # If high risk and low confidence
        if risk_score > 0.7 and success_probability < 0.5:
            return JobRecommendation.RESEARCH_FIRST, (
                f"High risk job with low confidence. Research similar projects "
                f"and gain more experience before applying."
            )

        # If good match
        if success_probability > 0.7 and risk_score < 0.5:
            return JobRecommendation.APPLY, (
                f"Good match with high success probability ({success_probability:.2f}) "
                f"and acceptable risk ({risk_score:.2f}). Consider applying."
            )

        # Default to reject
        return JobRecommendation.REJECT, (
            f"Low success probability ({success_probability:.2f}) or high risk ({risk_score:.2f}). "
            f"Consider gaining more experience or learning required skills first."
        )
