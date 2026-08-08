from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.knowledge_governance import GovernedKnowledge
from app.expert_domains.contracts import ReadinessScore
from app.work_market.job_readiness import (
    JobReadinessCalculator,
    JobReadinessResult,
    KnowledgeReadinessAssessment,
    EvidenceReadinessAssessment,
    CapabilityReadinessAssessment,
    ExecutionReadinessAssessment,
    ExperienceReadinessAssessment,
)
from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.job_analyzer import JobAnalysisResult


@dataclass
class ReadinessChange:
    """A change in readiness due to knowledge update."""
    component: str  # "knowledge", "evidence", "capability", "execution", "experience"
    previous_value: float
    new_value: float
    delta: float
    reason: str


@dataclass
class ReadinessRecalculationResult:
    """Result of readiness recalculation after knowledge update."""
    job_id: str
    domain_id: str
    previous_readiness: Optional[JobReadinessResult]
    new_readiness: JobReadinessResult
    readiness_changes: List[ReadinessChange] = field(default_factory=list)
    overall_delta: float = 0.0
    readiness_improved: bool = False
    now_ready: bool = False
    previously_ready: bool = False
    new_recommendation: Optional[str] = None
    previous_recommendation: Optional[str] = None
    governed_knowledge_used: List[str] = field(default_factory=list)
    recalculated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReadinessRecalculator:
    """
    Recalculates job readiness after knowledge updates through governance.
    
    Takes new governed knowledge and updates the readiness assessment,
    comparing against the previous readiness to show improvement.
    """

    def __init__(self, readiness_calculator: Optional[JobReadinessCalculator] = None) -> None:
        self._readiness_calculator = readiness_calculator

    def recalculate_readiness(
        self,
        job_id: str,
        domain_id: str,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        previous_readiness: Optional[JobReadinessResult],
        new_governed_knowledge: List[GovernedKnowledge],
        previous_recommendation: Optional[str] = None,
    ) -> ReadinessRecalculationResult:
        """
        Recalculate readiness after knowledge update.
        
        Args:
            job_id: The job identifier
            domain_id: The domain identifier
            work_spec: The work specification
            job_analysis: The job analysis result
            previous_readiness: Previous readiness assessment
            new_governed_knowledge: New governed knowledge from research
            previous_recommendation: Previous recommendation
            
        Returns:
            ReadinessRecalculationResult with updated readiness and changes
        """
        if self._readiness_calculator is None:
            raise ValueError("Readiness calculator not available")
        
        # Get domain readiness
        domain_readiness = self._get_domain_readiness(domain_id)
        
        # Recalculate readiness with new knowledge
        new_readiness = self._readiness_calculator.calculate_readiness(
            work_spec,
            job_analysis,
            domain_readiness,
        )
        
        # Calculate changes
        readiness_changes = self._calculate_readiness_changes(
            previous_readiness,
            new_readiness,
            new_governed_knowledge,
        )
        
        # Calculate overall delta
        overall_delta = 0.0
        if previous_readiness:
            overall_delta = new_readiness.overall_readiness.overall_readiness - previous_readiness.overall_readiness.overall_readiness
        
        # Determine readiness status
        readiness_improved = overall_delta > 0
        now_ready = new_readiness.overall_readiness.overall_readiness >= 0.8
        previously_ready = previous_readiness.overall_readiness.overall_readiness >= 0.8 if previous_readiness else False
        
        # Generate new recommendation
        new_recommendation = self._generate_recommendation(new_readiness)
        
        return ReadinessRecalculationResult(
            job_id=job_id,
            domain_id=domain_id,
            previous_readiness=previous_readiness,
            new_readiness=new_readiness,
            readiness_changes=readiness_changes,
            overall_delta=overall_delta,
            readiness_improved=readiness_improved,
            now_ready=now_ready,
            previously_ready=previously_ready,
            new_recommendation=new_recommendation,
            previous_recommendation=previous_recommendation,
            governed_knowledge_used=[k.name for k in new_governed_knowledge],
            metadata={
                "governed_knowledge_count": len(new_governed_knowledge),
                "readiness_threshold": 0.8,
            },
        )

    def _calculate_readiness_changes(
        self,
        previous: Optional[JobReadinessResult],
        new: JobReadinessResult,
        new_knowledge: List[GovernedKnowledge],
    ) -> List[ReadinessChange]:
        """Calculate changes in readiness components."""
        changes: List[ReadinessChange] = []
        
        if previous is None:
            # No previous readiness - all changes are from 0
            changes.append(
                ReadinessChange(
                    component="overall",
                    previous_value=0.0,
                    new_value=new.overall_readiness.overall_readiness,
                    delta=new.overall_readiness.overall_readiness,
                    reason="Initial readiness calculation",
                )
            )
            return changes
        
        # Knowledge readiness change
        prev_knowledge_coverage = previous.knowledge_readiness.knowledge_coverage
        new_knowledge_coverage = new.knowledge_readiness.knowledge_coverage
        if prev_knowledge_coverage != new_knowledge_coverage:
            changes.append(
                ReadinessChange(
                    component="knowledge",
                    previous_value=prev_knowledge_coverage,
                    new_value=new_knowledge_coverage,
                    delta=new_knowledge_coverage - prev_knowledge_coverage,
                    reason=f"Updated with {len(new_knowledge)} new governed knowledge items",
                )
            )
        
        # Evidence readiness change
        prev_evidence_coverage = previous.evidence_readiness.evidence_coverage
        new_evidence_coverage = new.evidence_readiness.evidence_coverage
        if prev_evidence_coverage != new_evidence_coverage:
            changes.append(
                ReadinessChange(
                    component="evidence",
                    previous_value=prev_evidence_coverage,
                    new_value=new_evidence_coverage,
                    delta=new_evidence_coverage - prev_evidence_coverage,
                    reason="Updated with new evidence from research",
                )
            )
        
        # Overall readiness change
        prev_overall = previous.overall_readiness.overall_readiness
        new_overall = new.overall_readiness.overall_readiness
        if prev_overall != new_overall:
            changes.append(
                ReadinessChange(
                    component="overall",
                    previous_value=prev_overall,
                    new_value=new_overall,
                    delta=new_overall - prev_overall,
                    reason="Overall readiness updated after knowledge integration",
                )
            )
        
        return changes

    def _get_domain_readiness(self, domain_id: str) -> ReadinessScore:
        """Get domain readiness score."""
        # In production, would fetch from actual domain
        return ReadinessScore(
            domain_id=domain_id,
            knowledge_readiness=0.8,
            execution_readiness=0.7,
            evidence_readiness=0.75,
            learning_readiness=0.8,
            overall_readiness=0.75,
        )

    def _generate_recommendation(self, readiness: JobReadinessResult) -> str:
        """Generate recommendation based on readiness."""
        overall_score = readiness.overall_readiness.overall_readiness
        
        if readiness.blockers:
            return "REJECT"
        
        if len(readiness.knowledge_readiness.missing_knowledge) > 0:
            return "LEARN_FIRST"
        
        if len(readiness.evidence_readiness.missing_evidence) > 0:
            return "RESEARCH_FIRST"
        
        if overall_score >= 0.8:
            return "READY"
        
        if overall_score >= 0.6:
            return "READY"
        
        return "REJECT"

    def get_readiness_summary(
        self,
        recalculation_result: ReadinessRecalculationResult,
    ) -> Dict[str, Any]:
        """
        Get a human-readable summary of readiness changes.
        
        Args:
            recalculation_result: The recalculation result
            
        Returns:
            Dictionary with summary information
        """
        summary = {
            "job_id": recalculation_result.job_id,
            "domain_id": recalculation_result.domain_id,
            "readiness_status": "READY" if recalculation_result.now_ready else "NOT_READY",
            "overall_readiness": recalculation_result.new_readiness.overall_readiness.overall_readiness,
            "readiness_improved": recalculation_result.readiness_improved,
            "improvement_delta": recalculation_result.overall_delta,
            "recommendation": recalculation_result.new_recommendation,
        }
        
        if recalculation_result.now_ready:
            summary["ready_reason"] = (
                f"Readiness improved to {recalculation_result.new_readiness.overall_readiness.overall_readiness:.2f} "
                f"after integrating {len(recalculation_result.governed_knowledge_used)} governed knowledge items"
            )
            summary["supporting_evidence"] = [
                k.name for k in recalculation_result.new_readiness.evidence_readiness.available_evidence
            ]
            summary["used_knowledge"] = recalculation_result.governed_knowledge_used
            summary["confidence"] = recalculation_result.new_readiness.confidence
            summary["remaining_risks"] = recalculation_result.new_readiness.risks
        else:
            summary["not_ready_reason"] = (
                f"Readiness at {recalculation_result.new_readiness.overall_readiness.overall_readiness:.2f} "
                f"is below threshold of 0.8"
            )
            summary["missing_capabilities"] = recalculation_result.new_readiness.capability_readiness.missing_capabilities
            summary["missing_knowledge"] = recalculation_result.new_readiness.knowledge_readiness.missing_knowledge
            summary["missing_evidence"] = recalculation_result.new_readiness.evidence_readiness.missing_evidence
            summary["required_research"] = [
                change.reason for change in recalculation_result.readiness_changes
                if change.component in ["knowledge", "evidence"]
            ]
            summary["required_practice"] = []
            summary["readiness_blockers"] = recalculation_result.new_readiness.blockers
        
        return summary
