from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import ReadinessScore
from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.models import FreelanceJob
from app.work_market.job_analyzer import JobAnalysisResult, RiskLevel, DifficultyLevel
from app.work_market.job_readiness import JobReadinessResult


class JobRecommendation(str, Enum):
    """Job recommendation decisions."""
    ACCEPT = "accept"
    ACCEPT_WITH_CONDITIONS = "accept_with_conditions"
    NEED_RESEARCH = "need_research"
    NEED_LEARNING = "need_learning"
    REJECT = "reject"


class RecommendationReason(str, Enum):
    """Reasons for job recommendations."""
    HIGH_READINESS = "high_readiness"
    MODERATE_READINESS = "moderate_readiness"
    LOW_READINESS = "low_readiness"
    CRITICAL_RISK = "critical_risk"
    INSUFFICIENT_BUDGET = "insufficient_budget"
    IMPOSSIBLE_TIMELINE = "impossible_timeline"
    MISSING_KNOWLEDGE = "missing_knowledge"
    MISSING_EVIDENCE = "missing_evidence"
    MISSING_CAPABILITIES = "missing_capabilities"
    HIGH_COMPETITION = "high_competition"
    GOOD_VALUE = "good_value"
    STRATEGIC_OPPORTUNITY = "strategic_opportunity"
    EXPERIENCE_GAP = "experience_gap"
    RESOURCE_CONSTRAINT = "resource_constraint"


@dataclass
class RecommendationCondition:
    """Condition for conditional acceptance."""
    condition_type: str  # "budget", "timeline", "scope", "learning"
    description: str
    required_action: str
    impact: str  # "low", "medium", "high"


@dataclass
class JobRecommendationResult:
    """Comprehensive job recommendation result."""
    work_id: str
    recommendation: JobRecommendation
    confidence: float  # 0.0 to 1.0
    primary_reason: RecommendationReason
    secondary_reasons: List[RecommendationReason] = field(default_factory=list)
    reasoning: str = ""
    conditions: List[RecommendationCondition] = field(default_factory=list)
    research_requirements: List[str] = field(default_factory=list)
    learning_requirements: List[str] = field(default_factory=list)
    success_probability: float = 0.0
    risk_level: str = ""
    value_score: float = 0.0
    recommended_at: datetime = field(default_factory=datetime.utcnow)


class JobRecommender(ABC):
    """Contract for job recommendation."""

    @abstractmethod
    def recommend(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> JobRecommendationResult:
        """
        Generate job recommendation.

        Analyzes:
        - Readiness score
        - Risk level
        - Budget adequacy
        - Timeline feasibility
        - Knowledge gaps
        - Evidence gaps
        - Capability gaps
        - Competition
        - Value proposition

        Returns recommendation with reasoning and conditions.
        """
        pass


class SEOJobRecommender(JobRecommender):
    """
    Generates SEO job recommendations.

    Uses comprehensive analysis to make ACCEPT/REJECT decisions.
    """

    def __init__(self) -> None:
        self._readiness_thresholds = {
            "accept": 0.8,
            "accept_with_conditions": 0.6,
            "need_learning": 0.4,
            "reject": 0.0,
        }

    def recommend(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> JobRecommendationResult:
        """Generate job recommendation."""
        # Calculate value score
        value_score = self._calculate_value_score(job, job_analysis, job_readiness)
        
        # Determine recommendation
        recommendation, primary_reason = self._determine_recommendation(
            job,
            job_analysis,
            job_readiness,
            value_score,
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            recommendation,
            primary_reason,
            job_analysis,
            job_readiness,
        )
        
        # Generate conditions if conditional acceptance
        conditions = self._generate_conditions(
            recommendation,
            job_analysis,
            job_readiness,
        )
        
        # Generate research requirements
        research_requirements = self._generate_research_requirements(
            job_analysis,
            job_readiness,
        )
        
        # Generate learning requirements
        learning_requirements = self._generate_learning_requirements(
            job_readiness,
        )
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            job_readiness,
            job_analysis,
        )
        
        # Determine risk level
        risk_level = job_analysis.risk_analysis.overall_risk.value
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            job_readiness,
            job_analysis,
        )
        
        # Identify secondary reasons
        secondary_reasons = self._identify_secondary_reasons(
            job_analysis,
            job_readiness,
        )
        
        return JobRecommendationResult(
            work_id=work_spec.work_id,
            recommendation=recommendation,
            confidence=confidence,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            reasoning=reasoning,
            conditions=conditions,
            research_requirements=research_requirements,
            learning_requirements=learning_requirements,
            success_probability=success_probability,
            risk_level=risk_level,
            value_score=value_score,
        )

    def _calculate_value_score(
        self,
        job: FreelanceJob,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> float:
        """Calculate value score for the job."""
        score = 0.0
        
        # Budget value
        if job.budget:
            if job.budget > 3000:
                score += 0.3
            elif job.budget > 1000:
                score += 0.2
            else:
                score += 0.1
        
        # Strategic value
        if job_analysis.competition_analysis.differentiation_opportunities:
            score += 0.2
        
        # Learning value
        if job_readiness.knowledge_readiness.missing_knowledge:
            score += 0.15  # Learning opportunity
        
        # Experience value
        if job_readiness.experience_readiness.experience_level in ["beginner", "intermediate"]:
            score += 0.15  # Experience building
        
        # Low competition value
        if job_analysis.competition_analysis.competition_level == "low":
            score += 0.2
        
        return min(1.0, score)

    def _determine_recommendation(
        self,
        job: FreelanceJob,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
        value_score: float,
    ) -> tuple[JobRecommendation, RecommendationReason]:
        """Determine the recommendation."""
        overall_readiness = job_readiness.overall_readiness.overall_readiness
        risk_level = job_analysis.risk_analysis.overall_risk
        
        # Check for immediate rejection criteria
        if job_analysis.timeline_analysis.deadline_feasibility == "impossible":
            return JobRecommendation.REJECT, RecommendationReason.IMPOSSIBLE_TIMELINE
        
        if job_analysis.budget_analysis.budget_adequacy == "insufficient" and job.budget and job.budget < 200:
            return JobRecommendation.REJECT, RecommendationReason.INSUFFICIENT_BUDGET
        
        if risk_level == RiskLevel.CRITICAL and overall_readiness < 0.5:
            return JobRecommendation.REJECT, RecommendationReason.CRITICAL_RISK
        
        # Check for need learning
        if overall_readiness < self._readiness_thresholds["need_learning"]:
            if job_readiness.knowledge_readiness.knowledge_coverage < 0.5:
                return JobRecommendation.NEED_LEARNING, RecommendationReason.MISSING_KNOWLEDGE
            elif job_readiness.evidence_readiness.evidence_coverage < 0.5:
                return JobRecommendation.NEED_LEARNING, RecommendationReason.MISSING_EVIDENCE
            else:
                return JobRecommendation.NEED_LEARNING, RecommendationReason.LOW_READINESS
        
        # Check for need research
        if overall_readiness < self._readiness_thresholds["accept_with_conditions"]:
            if job_readiness.knowledge_readiness.missing_knowledge:
                return JobRecommendation.NEED_RESEARCH, RecommendationReason.MISSING_KNOWLEDGE
            elif job_readiness.evidence_readiness.missing_evidence:
                return JobRecommendation.NEED_RESEARCH, RecommendationReason.MISSING_EVIDENCE
            else:
                return JobRecommendation.NEED_RESEARCH, RecommendationReason.MODERATE_READINESS
        
        # Check for conditional acceptance
        if overall_readiness < self._readiness_thresholds["accept"]:
            if job_analysis.timeline_analysis.deadline_feasibility == "tight":
                return JobRecommendation.ACCEPT_WITH_CONDITIONS, RecommendationReason.IMPOSSIBLE_TIMELINE
            elif job_analysis.budget_analysis.budget_adequacy == "insufficient":
                return JobRecommendation.ACCEPT_WITH_CONDITIONS, RecommendationReason.INSUFFICIENT_BUDGET
            elif job_readiness.capability_readiness.missing_capabilities:
                return JobRecommendation.ACCEPT_WITH_CONDITIONS, RecommendationReason.MISSING_CAPABILITIES
            else:
                return JobRecommendation.ACCEPT_WITH_CONDITIONS, RecommendationReason.MODERATE_READINESS
        
        # High readiness - accept
        if overall_readiness >= self._readiness_thresholds["accept"]:
            if value_score > 0.7:
                return JobRecommendation.ACCEPT, RecommendationReason.STRATEGIC_OPPORTUNITY
            else:
                return JobRecommendation.ACCEPT, RecommendationReason.HIGH_READINESS
        
        # Default
        return JobRecommendation.NEED_RESEARCH, RecommendationReason.MODERATE_READINESS

    def _generate_reasoning(
        self,
        recommendation: JobRecommendation,
        primary_reason: RecommendationReason,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> str:
        """Generate reasoning for the recommendation."""
        overall_readiness = job_readiness.overall_readiness.overall_readiness
        
        reasoning_parts = []
        
        # Readiness statement
        reasoning_parts.append(f"Overall readiness: {overall_readiness:.0%}")
        
        # Primary reason explanation
        reason_explanations = {
            RecommendationReason.HIGH_READINESS: "Domain readiness is sufficient for successful execution",
            RecommendationReason.MODERATE_READINESS: "Domain readiness is moderate - may require additional preparation",
            RecommendationReason.LOW_READINESS: "Domain readiness is low - significant gaps exist",
            RecommendationReason.CRITICAL_RISK: "Risk level exceeds acceptable threshold",
            RecommendationReason.INSUFFICIENT_BUDGET: "Budget is insufficient for required scope",
            RecommendationReason.IMPOSSIBLE_TIMELINE: "Timeline cannot be met with current scope",
            RecommendationReason.MISSING_KNOWLEDGE: "Critical knowledge gaps prevent execution",
            RecommendationReason.MISSING_EVIDENCE: "Insufficient evidence to support approach",
            RecommendationReason.MISSING_CAPABILITIES: "Required capabilities are not available",
            RecommendationReason.HIGH_COMPETITION: "High competition reduces success probability",
            RecommendationReason.GOOD_VALUE: "Job offers good value proposition",
            RecommendationReason.STRATEGIC_OPPORTUNITY: "Strategic opportunity for growth",
            RecommendationReason.EXPERIENCE_GAP: "Experience gap increases risk",
            RecommendationReason.RESOURCE_CONSTRAINT: "Resource constraints limit execution",
        }
        
        reasoning_parts.append(reason_explanations.get(primary_reason, ""))
        
        # Add context based on recommendation
        if recommendation == JobRecommendation.ACCEPT:
            reasoning_parts.append("Job can be accepted with high confidence of success")
        elif recommendation == JobRecommendation.ACCEPT_WITH_CONDITIONS:
            reasoning_parts.append("Job can be accepted with specific conditions")
        elif recommendation == JobRecommendation.NEED_RESEARCH:
            reasoning_parts.append("Additional research is required before decision")
        elif recommendation == JobRecommendation.NEED_LEARNING:
            reasoning_parts.append("Learning is required before job can be accepted")
        elif recommendation == JobRecommendation.REJECT:
            reasoning_parts.append("Job should be rejected due to critical issues")
        
        return ". ".join(reasoning_parts)

    def _generate_conditions(
        self,
        recommendation: JobRecommendation,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> List[RecommendationCondition]:
        """Generate conditions for conditional acceptance."""
        if recommendation != JobRecommendation.ACCEPT_WITH_CONDITIONS:
            return []
        
        conditions = []
        
        # Timeline condition
        if job_analysis.timeline_analysis.deadline_feasibility == "tight":
            conditions.append(RecommendationCondition(
                condition_type="timeline",
                description="Timeline is tight and may require additional resources",
                required_action="Negotiate extended deadline or allocate additional resources",
                impact="high",
            ))
        
        # Budget condition
        if job_analysis.budget_analysis.budget_adequacy == "insufficient":
            conditions.append(RecommendationCondition(
                condition_type="budget",
                description="Budget may be insufficient for full scope",
                required_action="Negotiate increased budget or reduce scope",
                impact="high",
            ))
        
        # Capability condition
        if job_readiness.capability_readiness.missing_capabilities:
            conditions.append(RecommendationCondition(
                condition_type="capability",
                description=f"Missing capabilities: {', '.join(job_readiness.capability_readiness.missing_capabilities[:2])}",
                required_action="Develop or acquire missing capabilities",
                impact="medium",
            ))
        
        # Knowledge condition
        if job_readiness.knowledge_readiness.missing_knowledge:
            conditions.append(RecommendationCondition(
                condition_type="learning",
                description=f"Missing knowledge: {', '.join(job_readiness.knowledge_readiness.missing_knowledge[:2])}",
                required_action="Acquire missing knowledge through research",
                impact="medium",
            ))
        
        return conditions

    def _generate_research_requirements(
        self,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> List[str]:
        """Generate research requirements."""
        requirements = []
        
        # Knowledge research
        for knowledge in job_readiness.knowledge_readiness.missing_knowledge[:3]:
            requirements.append(f"Research: {knowledge}")
        
        # Evidence research
        for evidence in job_readiness.evidence_readiness.missing_evidence[:3]:
            requirements.append(f"Gather evidence: {evidence}")
        
        # Competition research
        if job_analysis.competition_analysis.competition_level == "high":
            requirements.append("Research competitive landscape and differentiation strategies")
        
        # Industry research
        if job_analysis.competition_analysis.market_saturation == "high":
            requirements.append(f"Research {job_analysis.competition_analysis.market_saturation} market saturation in {job_analysis.competition_analysis.market_saturation}")
        
        return requirements

    def _generate_learning_requirements(
        self,
        job_readiness: JobReadinessResult,
    ) -> List[str]:
        """Generate learning requirements."""
        requirements = []
        
        # Knowledge learning
        for knowledge in job_readiness.knowledge_readiness.missing_knowledge[:3]:
            requirements.append(f"Learn: {knowledge}")
        
        # Capability development
        for capability in job_readiness.capability_readiness.missing_capabilities[:3]:
            requirements.append(f"Develop capability: {capability}")
        
        # Experience building
        if job_readiness.experience_readiness.experience_level == "beginner":
            requirements.append("Build experience through smaller similar projects")
        
        return requirements

    def _calculate_success_probability(
        self,
        job_readiness: JobReadinessResult,
        job_analysis: JobAnalysisResult,
    ) -> float:
        """Calculate probability of success."""
        probability = job_readiness.overall_readiness.overall_readiness
        
        # Adjust for risk
        if job_analysis.risk_analysis.overall_risk == RiskLevel.CRITICAL:
            probability -= 0.3
        elif job_analysis.risk_analysis.overall_risk == RiskLevel.HIGH:
            probability -= 0.15
        
        # Adjust for difficulty
        if job_analysis.difficulty_analysis.overall_difficulty == "very_hard":
            probability -= 0.2
        elif job_analysis.difficulty_analysis.overall_difficulty == "hard":
            probability -= 0.1
        
        # Adjust for experience
        if job_readiness.experience_readiness.experience_level == "expert":
            probability += 0.1
        elif job_readiness.experience_readiness.experience_level == "advanced":
            probability += 0.05
        
        return min(1.0, max(0.0, probability))

    def _calculate_confidence(
        self,
        job_readiness: JobReadinessResult,
        job_analysis: JobAnalysisResult,
    ) -> float:
        """Calculate confidence in the recommendation."""
        confidence = 0.7
        
        # Increase if readiness is clear
        if job_readiness.overall_readiness.overall_readiness > 0.8 or job_readiness.overall_readiness.overall_readiness < 0.3:
            confidence += 0.2
        
        # Increase if risk is clear
        if job_analysis.risk_analysis.overall_risk in [RiskLevel.LOW, RiskLevel.CRITICAL]:
            confidence += 0.1
        
        # Decrease if moderate readiness
        if 0.4 <= job_readiness.overall_readiness.overall_readiness <= 0.7:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))

    def _identify_secondary_reasons(
        self,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> List[RecommendationReason]:
        """Identify secondary reasons for the recommendation."""
        reasons = []
        
        # Budget consideration
        if job_analysis.budget_analysis.budget_adequacy == "insufficient":
            reasons.append(RecommendationReason.INSUFFICIENT_BUDGET)
        
        # Timeline consideration
        if job_analysis.timeline_analysis.deadline_feasibility == "tight":
            reasons.append(RecommendationReason.IMPOSSIBLE_TIMELINE)
        
        # Knowledge gaps
        if job_readiness.knowledge_readiness.missing_knowledge:
            reasons.append(RecommendationReason.MISSING_KNOWLEDGE)
        
        # Evidence gaps
        if job_readiness.evidence_readiness.missing_evidence:
            reasons.append(RecommendationReason.MISSING_EVIDENCE)
        
        # Capability gaps
        if job_readiness.capability_readiness.missing_capabilities:
            reasons.append(RecommendationReason.MISSING_CAPABILITIES)
        
        # Competition
        if job_analysis.competition_analysis.competition_level == "high":
            reasons.append(RecommendationReason.HIGH_COMPETITION)
        
        # Experience
        if job_readiness.experience_readiness.experience_level == "beginner":
            reasons.append(RecommendationReason.EXPERIENCE_GAP)
        
        return reasons[:3]


class JobRecommendationOrchestrator:
    """
    Orchestrates job recommendation generation.
    """

    def __init__(self) -> None:
        self._recommender = SEOJobRecommender()

    def recommend_job(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> JobRecommendationResult:
        """Generate job recommendation."""
        return self._recommender.recommend(job, work_spec, job_analysis, job_readiness)
