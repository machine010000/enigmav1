from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import ReadinessScore
from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.job_analyzer import JobAnalysisResult, RiskLevel, DifficultyLevel


class ReadinessComponent(str, Enum):
    """Components of job readiness."""
    KNOWLEDGE = "knowledge"
    EXECUTION = "execution"
    EVIDENCE = "evidence"
    CAPABILITY = "capability"
    EXPERIENCE = "experience"


@dataclass
class KnowledgeReadinessAssessment:
    """Assessment of knowledge readiness for a job."""
    required_knowledge: List[str]
    available_knowledge: List[str]
    missing_knowledge: List[str]
    knowledge_coverage: float  # 0.0 to 1.0
    knowledge_confidence: float  # 0.0 to 1.0
    knowledge_maturity: Dict[str, str] = field(default_factory=dict)


@dataclass
class EvidenceReadinessAssessment:
    """Assessment of evidence readiness for a job."""
    required_evidence: List[str]
    available_evidence: List[str]
    missing_evidence: List[str]
    evidence_coverage: float  # 0.0 to 1.0
    evidence_quality: float  # 0.0 to 1.0
    evidence_freshness: Dict[str, str] = field(default_factory=dict)


@dataclass
class CapabilityReadinessAssessment:
    """Assessment of capability readiness for a job."""
    required_capabilities: List[str]
    available_capabilities: List[str]
    missing_capabilities: List[str]
    capability_coverage: float  # 0.0 to 1.0
    capability_proficiency: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionReadinessAssessment:
    """Assessment of execution readiness for a job."""
    required_tasks: List[str]
    executable_tasks: List[str]
    non_executable_tasks: List[str]
    execution_coverage: float  # 0.0 to 1.0
    resource_availability: str  # "high", "medium", "low"
    execution_complexity: str  # "simple", "moderate", "complex"


@dataclass
class ExperienceReadinessAssessment:
    """Assessment of experience readiness for a job."""
    relevant_experience: List[str]
    experience_level: str  # "beginner", "intermediate", "advanced", "expert"
    similar_jobs_completed: int = 0
    success_rate: float = 0.0


@dataclass
class JobReadinessResult:
    """Comprehensive job readiness result."""
    work_id: str
    knowledge_readiness: KnowledgeReadinessAssessment
    evidence_readiness: EvidenceReadinessAssessment
    capability_readiness: CapabilityReadinessAssessment
    execution_readiness: ExecutionReadinessAssessment
    experience_readiness: ExperienceReadinessAssessment
    overall_readiness: ReadinessScore
    blockers: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    assessed_at: datetime = field(default_factory=datetime.utcnow)


class JobReadinessCalculator(ABC):
    """Contract for calculating job readiness."""

    @abstractmethod
    def calculate_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> JobReadinessResult:
        """
        Calculate comprehensive job readiness.

        Integrates:
        - Domain readiness from SEO Expert
        - Job-specific knowledge requirements
        - Evidence requirements
        - Capability requirements
        - Execution complexity
        - Experience level

        Returns comprehensive readiness assessment.
        """
        pass


class SEOJobReadinessCalculator(JobReadinessCalculator):
    """
    Calculates SEO job readiness using real domain knowledge and evidence.

    Integrates with SEO Expert's readiness evolution system.
    """

    def __init__(self) -> None:
        self._knowledge_maturity_levels = {
            "expert": 5,
            "advanced": 4,
            "intermediate": 3,
            "beginner": 2,
            "none": 1,
        }

    def calculate_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> JobReadinessResult:
        """Calculate comprehensive job readiness."""
        # Assess knowledge readiness
        knowledge_assessment = self._assess_knowledge_readiness(work_spec, job_analysis, domain_readiness)
        
        # Assess evidence readiness
        evidence_assessment = self._assess_evidence_readiness(work_spec, job_analysis, domain_readiness)
        
        # Assess capability readiness
        capability_assessment = self._assess_capability_readiness(work_spec, job_analysis, domain_readiness)
        
        # Assess execution readiness
        execution_assessment = self._assess_execution_readiness(work_spec, job_analysis, domain_readiness)
        
        # Assess experience readiness
        experience_assessment = self._assess_experience_readiness(work_spec, job_analysis)
        
        # Calculate overall readiness
        overall_readiness = self._calculate_overall_readiness(
            knowledge_assessment,
            evidence_assessment,
            capability_assessment,
            execution_assessment,
            experience_assessment,
            domain_readiness,
        )
        
        # Identify blockers
        blockers = self._identify_blockers(
            knowledge_assessment,
            evidence_assessment,
            capability_assessment,
            execution_assessment,
            job_analysis,
        )
        
        # Identify risks
        risks = self._identify_risks(job_analysis, overall_readiness)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            knowledge_assessment,
            evidence_assessment,
            capability_assessment,
            execution_assessment,
            blockers,
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            knowledge_assessment,
            evidence_assessment,
            capability_assessment,
            execution_assessment,
        )
        
        return JobReadinessResult(
            work_id=work_spec.work_id,
            knowledge_readiness=knowledge_assessment,
            evidence_readiness=evidence_assessment,
            capability_readiness=capability_assessment,
            execution_readiness=execution_assessment,
            experience_readiness=experience_assessment,
            overall_readiness=overall_readiness,
            blockers=blockers,
            risks=risks,
            recommendations=recommendations,
            confidence=confidence,
        )

    def _assess_knowledge_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> KnowledgeReadinessAssessment:
        """Assess knowledge readiness for the job."""
        required_knowledge = job_analysis.knowledge_requirements
        
        # Simulate available knowledge from domain
        # In production, this would query the SEO Expert's knowledge structure
        available_knowledge = self._get_available_knowledge(work_spec)
        
        # Identify missing knowledge
        missing_knowledge = [k for k in required_knowledge if k not in available_knowledge]
        
        # Calculate coverage
        knowledge_coverage = len(available_knowledge) / len(required_knowledge) if required_knowledge else 1.0
        
        # Knowledge confidence from domain readiness
        knowledge_confidence = domain_readiness.knowledge_readiness
        
        # Knowledge maturity levels
        knowledge_maturity = self._get_knowledge_maturity(available_knowledge)
        
        return KnowledgeReadinessAssessment(
            required_knowledge=required_knowledge,
            available_knowledge=available_knowledge,
            missing_knowledge=missing_knowledge,
            knowledge_coverage=knowledge_coverage,
            knowledge_confidence=knowledge_confidence,
            knowledge_maturity=knowledge_maturity,
        )

    def _get_available_knowledge(self, work_spec: WorkSpecification) -> List[str]:
        """Get available knowledge from SEO Expert."""
        # In production, this would query the SEO Expert's knowledge structure
        # For now, simulate based on required capabilities
        capability_to_knowledge = {
            "technical_seo_audit": "Technical SEO knowledge",
            "keyword_research": "Keyword research methodologies",
            "on_page_optimization": "On-page SEO best practices",
            "link_building": "Link building strategies",
            "content_optimization": "Content optimization techniques",
            "site_speed_optimization": "Performance optimization",
            "mobile_optimization": "Mobile-first indexing",
            "schema_markup": "Structured data implementation",
        }
        
        available = []
        for capability in work_spec.required_capabilities:
            knowledge = capability_to_knowledge.get(capability)
            if knowledge:
                available.append(knowledge)
        
        return available

    def _get_knowledge_maturity(self, knowledge: List[str]) -> Dict[str, str]:
        """Get maturity levels for available knowledge."""
        # In production, this would query actual maturity from SEO Expert
        maturity = {}
        for k in knowledge:
            # Simulate maturity levels
            if "technical" in k.lower() or "audit" in k.lower():
                maturity[k] = "advanced"
            elif "keyword" in k.lower():
                maturity[k] = "expert"
            elif "optimization" in k.lower():
                maturity[k] = "intermediate"
            else:
                maturity[k] = "intermediate"
        return maturity

    def _assess_evidence_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> EvidenceReadinessAssessment:
        """Assess evidence readiness for the job."""
        required_evidence = job_analysis.evidence_requirements
        
        # Simulate available evidence from domain
        available_evidence = self._get_available_evidence(work_spec)
        
        # Identify missing evidence
        missing_evidence = [e for e in required_evidence if e not in available_evidence]
        
        # Calculate coverage
        evidence_coverage = len(available_evidence) / len(required_evidence) if required_evidence else 1.0
        
        # Evidence quality from domain readiness
        evidence_quality = domain_readiness.evidence_readiness
        
        # Evidence freshness
        evidence_freshness = self._get_evidence_freshness(available_evidence)
        
        return EvidenceReadinessAssessment(
            required_evidence=required_evidence,
            available_evidence=available_evidence,
            missing_evidence=missing_evidence,
            evidence_coverage=evidence_coverage,
            evidence_quality=evidence_quality,
            evidence_freshness=evidence_freshness,
        )

    def _get_available_evidence(self, work_spec: WorkSpecification) -> List[str]:
        """Get available evidence from SEO Expert."""
        # In production, this would query the SEO Expert's evidence store
        capability_to_evidence = {
            "technical_seo_audit": "Technical audit reports, performance metrics",
            "keyword_research": "Keyword data, search volume metrics",
            "on_page_optimization": "On-page optimization case studies",
            "link_building": "Backlink analysis, successful link building examples",
            "content_optimization": "Content performance data",
        }
        
        available = []
        for capability in work_spec.required_capabilities:
            evidence = capability_to_evidence.get(capability)
            if evidence:
                available.append(evidence)
        
        return available

    def _get_evidence_freshness(self, evidence: List[str]) -> Dict[str, str]:
        """Get freshness levels for available evidence."""
        # In production, this would query actual freshness from SEO Expert
        freshness = {}
        for e in evidence:
            # Simulate freshness levels
            if "audit" in e.lower() or "metrics" in e.lower():
                freshness[e] = "fresh"
            elif "case study" in e.lower():
                freshness[e] = "aging"
            else:
                freshness[e] = "fresh"
        return freshness

    def _assess_capability_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> CapabilityReadinessAssessment:
        """Assess capability readiness for the job."""
        required_capabilities = work_spec.required_capabilities
        available_capabilities = work_spec.required_capabilities  # Assume all required are available
        
        # Identify missing capabilities
        missing_capabilities = []
        
        # Calculate coverage
        capability_coverage = len(available_capabilities) / len(required_capabilities) if required_capabilities else 1.0
        
        # Capability proficiency
        capability_proficiency = self._get_capability_proficiency(available_capabilities)
        
        return CapabilityReadinessAssessment(
            required_capabilities=required_capabilities,
            available_capabilities=available_capabilities,
            missing_capabilities=missing_capabilities,
            capability_coverage=capability_coverage,
            capability_proficiency=capability_proficiency,
        )

    def _get_capability_proficiency(self, capabilities: List[str]) -> Dict[str, str]:
        """Get proficiency levels for capabilities."""
        proficiency = {}
        for cap in capabilities:
            # Simulate proficiency levels
            if "audit" in cap.lower():
                proficiency[cap] = "advanced"
            elif "research" in cap.lower():
                proficiency[cap] = "expert"
            elif "optimization" in cap.lower():
                proficiency[cap] = "intermediate"
            else:
                proficiency[cap] = "intermediate"
        return proficiency

    def _assess_execution_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> ExecutionReadinessAssessment:
        """Assess execution readiness for the job."""
        required_tasks = work_spec.required_tasks
        executable_tasks = required_tasks  # Assume all are executable
        non_executable_tasks = []
        
        # Calculate coverage
        execution_coverage = len(executable_tasks) / len(required_tasks) if required_tasks else 1.0
        
        # Resource availability based on complexity
        resource_availability = self._assess_resource_availability(job_analysis)
        
        # Execution complexity
        execution_complexity = job_analysis.execution_complexity
        
        return ExecutionReadinessAssessment(
            required_tasks=required_tasks,
            executable_tasks=executable_tasks,
            non_executable_tasks=non_executable_tasks,
            execution_coverage=execution_coverage,
            resource_availability=resource_availability,
            execution_complexity=execution_complexity,
        )

    def _assess_resource_availability(self, job_analysis: JobAnalysisResult) -> str:
        """Assess resource availability."""
        if job_analysis.difficulty_analysis.overall_difficulty in ["very_hard", "hard"]:
            return "low"
        elif job_analysis.difficulty_analysis.overall_difficulty == "moderate":
            return "medium"
        else:
            return "high"

    def _assess_experience_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
    ) -> ExperienceReadinessAssessment:
        """Assess experience readiness for the job."""
        # Relevant experience based on category
        category = work_spec.metadata.get("category", "seo_audit")
        relevant_experience = [f"Experience in {category}"]
        
        # Experience level based on domain readiness
        if job_analysis.difficulty_analysis.overall_difficulty == "very_hard":
            experience_level = "expert"
        elif job_analysis.difficulty_analysis.overall_difficulty == "hard":
            experience_level = "advanced"
        elif job_analysis.difficulty_analysis.overall_difficulty == "moderate":
            experience_level = "intermediate"
        else:
            experience_level = "beginner"
        
        # Simulate similar jobs completed
        similar_jobs_completed = 5 if experience_level in ["expert", "advanced"] else 2
        
        # Success rate
        success_rate = 0.85 if experience_level == "expert" else 0.75 if experience_level == "advanced" else 0.65
        
        return ExperienceReadinessAssessment(
            relevant_experience=relevant_experience,
            experience_level=experience_level,
            similar_jobs_completed=similar_jobs_completed,
            success_rate=success_rate,
        )

    def _calculate_overall_readiness(
        self,
        knowledge_assessment: KnowledgeReadinessAssessment,
        evidence_assessment: EvidenceReadinessAssessment,
        capability_assessment: CapabilityReadinessAssessment,
        execution_assessment: ExecutionReadinessAssessment,
        experience_assessment: ExperienceReadinessAssessment,
        domain_readiness: ReadinessScore,
    ) -> ReadinessScore:
        """Calculate overall readiness score."""
        # Component weights
        weights = {
            "knowledge": 0.25,
            "evidence": 0.20,
            "capability": 0.25,
            "execution": 0.20,
            "experience": 0.10,
        }
        
        # Calculate component scores
        knowledge_score = (
            knowledge_assessment.knowledge_coverage * 0.6
            + knowledge_assessment.knowledge_confidence * 0.4
        )
        
        evidence_score = (
            evidence_assessment.evidence_coverage * 0.5
            + evidence_assessment.evidence_quality * 0.5
        )
        
        capability_score = capability_assessment.capability_coverage
        
        execution_score = (
            execution_assessment.execution_coverage * 0.6
            + (0.8 if execution_assessment.resource_availability == "high" else 0.5 if execution_assessment.resource_availability == "medium" else 0.3) * 0.4
        )
        
        experience_score = (
            0.9 if experience_assessment.experience_level == "expert"
            else 0.75 if experience_assessment.experience_level == "advanced"
            else 0.6 if experience_assessment.experience_level == "intermediate"
            else 0.4
        )
        
        # Calculate weighted overall
        overall = (
            knowledge_score * weights["knowledge"]
            + evidence_score * weights["evidence"]
            + capability_score * weights["capability"]
            + execution_score * weights["execution"]
            + experience_score * weights["experience"]
        )
        
        # Blend with domain readiness
        blended_overall = (overall + domain_readiness.overall_readiness) / 2
        
        return ReadinessScore(
            domain_id="seo",
            knowledge_readiness=knowledge_score,
            execution_readiness=execution_score,
            evidence_readiness=evidence_score,
            learning_readiness=domain_readiness.learning_readiness,
            overall_readiness=blended_overall,
        )

    def _identify_blockers(
        self,
        knowledge_assessment: KnowledgeReadinessAssessment,
        evidence_assessment: EvidenceReadinessAssessment,
        capability_assessment: CapabilityReadinessAssessment,
        execution_assessment: ExecutionReadinessAssessment,
        job_analysis: JobAnalysisResult,
    ) -> List[str]:
        """Identify blockers to job acceptance."""
        blockers = []
        
        # Knowledge blockers
        if knowledge_assessment.knowledge_coverage < 0.7:
            blockers.append(f"Insufficient knowledge coverage: {knowledge_assessment.knowledge_coverage:.0%}")
        
        # Evidence blockers
        if evidence_assessment.evidence_coverage < 0.7:
            blockers.append(f"Insufficient evidence coverage: {evidence_assessment.evidence_coverage:.0%}")
        
        # Capability blockers
        if capability_assessment.capability_coverage < 0.8:
            blockers.append(f"Missing required capabilities: {', '.join(capability_assessment.missing_capabilities[:3])}")
        
        # Execution blockers
        if execution_assessment.resource_availability == "low":
            blockers.append("Low resource availability for execution")
        
        # Risk blockers
        if job_analysis.risk_analysis.overall_risk == RiskLevel.CRITICAL:
            blockers.append("Critical risk level exceeds acceptable threshold")
        
        # Timeline blockers
        if job_analysis.timeline_analysis.deadline_feasibility == "impossible":
            blockers.append("Timeline is not feasible")
        
        return blockers

    def _identify_risks(self, job_analysis: JobAnalysisResult, overall_readiness: ReadinessScore) -> List[str]:
        """Identify risks for job execution."""
        risks = []
        
        # Low readiness risk
        if overall_readiness.overall_readiness < 0.6:
            risks.append("Low overall readiness may impact success probability")
        
        # High complexity risk
        if job_analysis.difficulty_analysis.overall_difficulty == "very_hard":
            risks.append("Very high difficulty increases execution risk")
        
        # Budget risk
        if job_analysis.budget_analysis.budget_adequacy == "insufficient":
            risks.append("Budget may be insufficient for required scope")
        
        # Timeline risk
        if job_analysis.timeline_analysis.deadline_feasibility == "tight":
            risks.append("Tight timeline may require additional resources")
        
        return risks

    def _generate_recommendations(
        self,
        knowledge_assessment: KnowledgeReadinessAssessment,
        evidence_assessment: EvidenceReadinessAssessment,
        capability_assessment: CapabilityReadinessAssessment,
        execution_assessment: ExecutionReadinessAssessment,
        blockers: List[str],
    ) -> List[str]:
        """Generate recommendations to improve readiness."""
        recommendations = []
        
        # Knowledge recommendations
        if knowledge_assessment.missing_knowledge:
            recommendations.append(f"Acquire missing knowledge: {', '.join(knowledge_assessment.missing_knowledge[:2])}")
        
        # Evidence recommendations
        if evidence_assessment.missing_evidence:
            recommendations.append(f"Gather missing evidence: {', '.join(evidence_assessment.missing_evidence[:2])}")
        
        # Capability recommendations
        if capability_assessment.missing_capabilities:
            recommendations.append(f"Develop missing capabilities: {', '.join(capability_assessment.missing_capabilities[:2])}")
        
        # Execution recommendations
        if execution_assessment.resource_availability == "low":
            recommendations.append("Allocate additional resources for execution")
        
        # Blocker-specific recommendations
        if blockers:
            recommendations.append("Address critical blockers before proceeding")
        
        return recommendations

    def _calculate_confidence(
        self,
        knowledge_assessment: KnowledgeReadinessAssessment,
        evidence_assessment: EvidenceReadinessAssessment,
        capability_assessment: CapabilityReadinessAssessment,
        execution_assessment: ExecutionReadinessAssessment,
    ) -> float:
        """Calculate confidence in the readiness assessment."""
        confidence = 0.7
        
        # Increase if all coverages are high
        if all([
            knowledge_assessment.knowledge_coverage > 0.8,
            evidence_assessment.evidence_coverage > 0.8,
            capability_assessment.capability_coverage > 0.8,
            execution_assessment.execution_coverage > 0.8,
        ]):
            confidence += 0.2
        
        # Decrease if any coverage is low
        if any([
            knowledge_assessment.knowledge_coverage < 0.5,
            evidence_assessment.evidence_coverage < 0.5,
            capability_assessment.capability_coverage < 0.5,
            execution_assessment.execution_coverage < 0.5,
        ]):
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))


class JobReadinessOrchestrator:
    """
    Orchestrates job readiness calculation.
    """

    def __init__(self) -> None:
        self._calculator = SEOJobReadinessCalculator()

    def calculate_readiness(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        domain_readiness: ReadinessScore,
    ) -> JobReadinessResult:
        """Calculate comprehensive job readiness."""
        return self._calculator.calculate_readiness(work_spec, job_analysis, domain_readiness)
