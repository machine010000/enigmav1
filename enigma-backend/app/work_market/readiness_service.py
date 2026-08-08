from __future__ import annotations

from typing import Dict, List, Optional

from app.work_market.models import (
    FreelanceJob,
    JobClassification,
    JobEvaluation,
    JobAssessment,
    JobRecommendation,
    ApplicationStatus,
)
from app.work_market.contracts import (
    KnowledgeProvider,
    EvidenceProvider,
    ProfessionProvider,
    ExpertDomainProvider,
)


class FreelancingReadinessService:
    """
    Service to determine if Enigma is ready to apply to a job.
    
    This service evaluates job readiness based on:
    - Profession match
    - Required skills
    - Required capabilities
    - Knowledge maturity (from Knowledge Governance)
    - Knowledge freshness (from Knowledge Governance)
    - Evidence (from Evidence Provider)
    - Previous experience
    - Execution capability
    - Risk assessment
    
    IMPORTANT: This service uses real Cognitive Core infrastructure
    (Knowledge Governance, Expert Domain, Evidence) through contracts.
    """

    def __init__(
        self,
        knowledge_provider: Optional[KnowledgeProvider] = None,
        evidence_provider: Optional[EvidenceProvider] = None,
        profession_provider: Optional[ProfessionProvider] = None,
        expert_domain_provider: Optional[ExpertDomainProvider] = None,
    ) -> None:
        self.knowledge_provider = knowledge_provider
        self.evidence_provider = evidence_provider
        self.profession_provider = profession_provider
        self.expert_domain_provider = expert_domain_provider
        
        # Thresholds for readiness determination
        self._readiness_thresholds = {
            "profession_match": 0.6,
            "skill_match": 0.5,
            "knowledge_match": 0.7,
            "capability_match": 0.7,
            "evidence_match": 0.5,
            "overall_readiness": 0.7,
        }

    def assess_readiness(
        self,
        job: FreelanceJob,
        classification: JobClassification,
        evaluation: JobEvaluation,
    ) -> JobAssessment:
        """
        Assess Enigma's readiness for a job.
        
        Returns a comprehensive readiness assessment with blockers and risks.
        Uses real Cognitive Core infrastructure through contracts.
        """
        # Calculate individual readiness components using real providers
        profession_match = evaluation.profession_match
        capability_match = evaluation.capability_match
        knowledge_readiness = self._assess_knowledge_readiness(classification)
        evidence_readiness = self._assess_evidence_readiness(classification)
        execution_readiness = self._assess_execution_readiness(classification, evaluation)
        
        # Calculate overall readiness
        overall_readiness = (
            profession_match * 0.2 +
            capability_match * 0.3 +
            knowledge_readiness * 0.25 +
            evidence_readiness * 0.15 +
            execution_readiness * 0.1
        )
        
        # Identify blockers
        blockers = self._identify_blockers(
            profession_match,
            capability_match,
            knowledge_readiness,
            evidence_readiness,
            execution_readiness,
            classification,
            evaluation,
        )
        
        # Identify risks
        risks = self._identify_risks(
            evaluation.risk_score,
            evaluation.complexity_score,
            evaluation.effort_score,
            classification,
        )
        
        # Determine recommendation
        recommendation = self._determine_recommendation(
            overall_readiness,
            blockers,
            risks,
            evaluation.missing_knowledge,
            evaluation.missing_capabilities,
        )
        
        return JobAssessment(
            job_id=job.job_id,
            profession_match=profession_match,
            capability_match=capability_match,
            knowledge_readiness=knowledge_readiness,
            evidence_readiness=evidence_readiness,
            execution_readiness=execution_readiness,
            overall_readiness=overall_readiness,
            blockers=blockers,
            risks=risks,
            missing_knowledge=evaluation.missing_knowledge,
            missing_capabilities=evaluation.missing_capabilities,
            recommendation=recommendation,
        )

    def _assess_knowledge_readiness(self, classification: JobClassification) -> float:
        """
        Assess knowledge readiness using Knowledge Governance.
        
        This integrates with Knowledge Governance to check:
        - Knowledge maturity levels
        - Knowledge freshness
        - Knowledge confidence
        """
        if not self.knowledge_provider or not classification.required_knowledge:
            return 0.5  # Default if no provider or no required knowledge
        
        # Calculate average readiness across all required knowledge
        knowledge_scores = []
        for concept in classification.required_knowledge:
            maturity = self.knowledge_provider.get_knowledge_maturity(concept)
            freshness = self.knowledge_provider.get_knowledge_freshness(concept)
            confidence = self.knowledge_provider.get_knowledge_confidence(concept)
            
            # Weighted average of knowledge quality metrics
            knowledge_score = (maturity * 0.4 + freshness * 0.3 + confidence * 0.3)
            knowledge_scores.append(knowledge_score)
        
        if not knowledge_scores:
            return 0.5
        
        return sum(knowledge_scores) / len(knowledge_scores)

    def _assess_evidence_readiness(self, classification: JobClassification) -> float:
        """
        Assess evidence readiness using Evidence Provider.
        
        This checks if there's sufficient evidence for required capabilities.
        """
        if not self.evidence_provider or not classification.required_capabilities:
            return 0.5  # Default if no provider or no required capabilities
        
        # Calculate average evidence readiness across all required capabilities
        evidence_scores = []
        for capability in classification.required_capabilities:
            coverage = self.evidence_provider.get_evidence_coverage(capability)
            quality = self.evidence_provider.get_evidence_quality(capability)
            freshness = self.evidence_provider.get_evidence_freshness(capability)
            
            # Weighted average of evidence quality metrics
            evidence_score = (coverage * 0.4 + quality * 0.4 + freshness * 0.2)
            evidence_scores.append(evidence_score)
        
        if not evidence_scores:
            return 0.5
        
        return sum(evidence_scores) / len(evidence_scores)

    def _assess_execution_readiness(
        self,
        classification: JobClassification,
        evaluation: JobEvaluation,
    ) -> float:
        """
        Assess execution readiness based on complexity and effort.
        
        This checks if Enigma can successfully execute the job given
        its complexity and required effort.
        """
        # Higher complexity and effort reduce execution readiness
        complexity_penalty = evaluation.complexity_score * 0.3
        effort_penalty = evaluation.effort_score * 0.2
        
        base_readiness = 0.8
        execution_readiness = base_readiness - complexity_penalty - effort_penalty
        
        return max(0.0, min(1.0, execution_readiness))

    def _identify_blockers(
        self,
        profession_match: float,
        capability_match: float,
        knowledge_readiness: float,
        evidence_readiness: float,
        execution_readiness: float,
        classification: JobClassification,
        evaluation: JobEvaluation,
    ) -> List[str]:
        """Identify blockers preventing application."""
        blockers = []
        
        # Profession match blocker
        if profession_match < self._readiness_thresholds["profession_match"]:
            blockers.append(f"Low profession match ({profession_match:.2f})")
        
        # Capability match blocker
        if capability_match < self._readiness_thresholds["capability_match"]:
            blockers.append(f"Insufficient capability match ({capability_match:.2f})")
        
        # Knowledge readiness blocker
        if knowledge_readiness < self._readiness_thresholds["knowledge_match"]:
            blockers.append(f"Insufficient knowledge readiness ({knowledge_readiness:.2f})")
        
        # Evidence readiness blocker
        if evidence_readiness < self._readiness_thresholds["evidence_match"]:
            blockers.append(f"Insufficient evidence ({evidence_readiness:.2f})")
        
        # Execution readiness blocker
        if execution_readiness < 0.5:
            blockers.append(f"Execution risk too high ({execution_readiness:.2f})")
        
        # Missing critical knowledge
        if evaluation.missing_knowledge:
            blockers.append(f"Missing critical knowledge: {', '.join(evaluation.missing_knowledge[:3])}")
        
        # Missing critical capabilities
        if evaluation.missing_capabilities:
            blockers.append(f"Missing critical capabilities: {', '.join(evaluation.missing_capabilities[:3])}")
        
        return blockers

    def _identify_risks(
        self,
        risk_score: float,
        complexity_score: float,
        effort_score: float,
        classification: JobClassification,
    ) -> List[str]:
        """Identify risks associated with the job."""
        risks = []
        
        if risk_score > 0.7:
            risks.append("High overall risk score")
        
        if complexity_score > 0.7:
            risks.append("High complexity job")
        
        if effort_score > 0.7:
            risks.append("High effort required")
        
        if classification.complexity == "high":
            risks.append("Complex task requirements")
        
        if classification.estimated_effort == "high":
            risks.append("Significant time investment required")
        
        return risks

    def _determine_recommendation(
        self,
        overall_readiness: float,
        blockers: List[str],
        risks: List[str],
        missing_knowledge: List[str],
        missing_capabilities: List[str],
    ) -> JobRecommendation:
        """
        Determine recommendation based on readiness assessment.
        
        Returns:
            - APPLY: Ready to apply
            - LEARN_FIRST: Need to learn missing knowledge/skills
            - RESEARCH_FIRST: Need to research the job/domain
            - REJECT: Not a good match
        """
        # If there are critical blockers, don't apply
        if blockers and overall_readiness < self._readiness_thresholds["overall_readiness"]:
            if missing_knowledge:
                return JobRecommendation.LEARN_FIRST
            if missing_capabilities:
                return JobRecommendation.LEARN_FIRST
            return JobRecommendation.REJECT
        
        # If high risk but decent readiness, research first
        if risks and overall_readiness > 0.5 and overall_readiness < 0.7:
            return JobRecommendation.RESEARCH_FIRST
        
        # If good readiness, can apply
        if overall_readiness >= self._readiness_thresholds["overall_readiness"]:
            return JobRecommendation.APPLY
        
        # Default to reject
        return JobRecommendation.REJECT

    def can_apply(self, assessment: JobAssessment) -> bool:
        """
        Determine if Enigma can apply to a job based on assessment.
        
        This is a simple check that can be used by the API layer.
        """
        return (
            assessment.recommendation == JobRecommendation.APPLY and
            len(assessment.blockers) == 0
        )

    def get_application_blockers(self, assessment: JobAssessment) -> List[str]:
        """
        Get structured application blockers for display.
        
        Returns a list of blockers that prevent application.
        """
        return assessment.blockers

    def get_required_learning(self, assessment: JobAssessment) -> Dict[str, List[str]]:
        """
        Get required learning based on assessment.
        
        Returns structured learning requirements:
        {
            "knowledge": [...],
            "capabilities": [...],
            "skills": [...]
        }
        """
        return {
            "knowledge": assessment.missing_knowledge,
            "capabilities": assessment.missing_capabilities,
            "skills": [],  # Would come from evaluation
        }
