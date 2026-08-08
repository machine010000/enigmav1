from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import DomainConcept, KnowledgeArea
from app.knowledge_governance import GovernedKnowledge, KnowledgeMaturity


class GapSeverity(str, Enum):
    """Severity levels for knowledge gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class KnowledgeGap:
    """A gap in knowledge required for a job."""
    gap_id: str
    concept_id: str
    concept_name: str
    required_maturity: KnowledgeMaturity
    current_maturity: KnowledgeMaturity
    severity: GapSeverity
    description: str
    domain_id: str
    job_id: str
    suggested_research_queries: List[str] = field(default_factory=list)
    suggested_practice_tasks: List[str] = field(default_factory=list)
    identified_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeGapAnalysisResult:
    """Result of knowledge gap analysis."""
    job_id: str
    domain_id: str
    total_gaps: int
    critical_gaps: int
    high_gaps: int
    medium_gaps: int
    low_gaps: int
    gaps: List[KnowledgeGap] = field(default_factory=list)
    readiness_impact: float = 0.0  # 0.0 to 1.0, impact on overall readiness
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGapAnalyzer:
    """
    Analyzes knowledge gaps for job requirements.
    
    Compares required knowledge (from job capabilities) against available
    governed knowledge to identify gaps in maturity, coverage, and specificity.
    """

    def __init__(self) -> None:
        self._maturity_priority = {
            KnowledgeMaturity.EXPERT_KNOWLEDGE: 5,
            KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS: 4,
            KnowledgeMaturity.APPLIED: 3,
            KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES: 2,
            KnowledgeMaturity.DEFINITION: 1,
            KnowledgeMaturity.UNKNOWN: 0,
        }

    def analyze_gaps(
        self,
        job_id: str,
        domain_id: str,
        required_knowledge: List[str],
        available_knowledge: List[GovernedKnowledge],
    ) -> KnowledgeGapAnalysisResult:
        """
        Analyze knowledge gaps for a job.
        
        Args:
            job_id: The job identifier
            domain_id: The domain identifier
            required_knowledge: List of required knowledge concept IDs
            available_knowledge: List of available governed knowledge
            
        Returns:
            KnowledgeGapAnalysisResult with identified gaps
        """
        gaps: List[KnowledgeGap] = []
        
        # Create a map of available knowledge for quick lookup
        available_map = {k.name: k for k in available_knowledge}
        
        for required_concept in required_knowledge:
            governed = available_map.get(required_concept)
            
            if governed is None:
                # Knowledge completely missing
                gap = KnowledgeGap(
                    gap_id=f"gap_{hash(required_concept)}",
                    concept_id=required_concept,
                    concept_name=required_concept,
                    required_maturity=KnowledgeMaturity.APPLIED,
                    current_maturity=KnowledgeMaturity.UNKNOWN,
                    severity=GapSeverity.CRITICAL,
                    description=f"Required knowledge '{required_concept}' is completely missing",
                    domain_id=domain_id,
                    job_id=job_id,
                    suggested_research_queries=self._generate_research_queries(required_concept),
                    suggested_practice_tasks=self._generate_practice_tasks(required_concept),
                )
                gaps.append(gap)
            else:
                # Knowledge exists but check maturity
                required_maturity = self._infer_required_maturity(required_concept)
                current_maturity = governed.knowledge_maturity
                
                if self._maturity_priority[current_maturity] < self._maturity_priority[required_maturity]:
                    gap = KnowledgeGap(
                        gap_id=f"gap_{hash(required_concept)}",
                        concept_id=required_concept,
                        concept_name=required_concept,
                        required_maturity=required_maturity,
                        current_maturity=current_maturity,
                        severity=self._calculate_maturity_gap_severity(required_maturity, current_maturity),
                        description=f"Knowledge '{required_concept}' maturity insufficient: required {required_maturity.value}, current {current_maturity.value}",
                        domain_id=domain_id,
                        job_id=job_id,
                        suggested_research_queries=self._generate_research_queries(required_concept),
                        suggested_practice_tasks=self._generate_practice_tasks(required_concept),
                    )
                    gaps.append(gap)
        
        # Calculate gap statistics
        critical_count = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL)
        high_count = sum(1 for g in gaps if g.severity == GapSeverity.HIGH)
        medium_count = sum(1 for g in gaps if g.severity == GapSeverity.MEDIUM)
        low_count = sum(1 for g in gaps if g.severity == GapSeverity.LOW)
        
        # Calculate readiness impact
        readiness_impact = self._calculate_readiness_impact(gaps, len(required_knowledge))
        
        return KnowledgeGapAnalysisResult(
            job_id=job_id,
            domain_id=domain_id,
            total_gaps=len(gaps),
            critical_gaps=critical_count,
            high_gaps=high_count,
            medium_gaps=medium_count,
            low_gaps=low_count,
            gaps=gaps,
            readiness_impact=readiness_impact,
        )

    def _infer_required_maturity(self, concept: str) -> KnowledgeMaturity:
        """Infer required maturity level based on concept name."""
        # Simple heuristic - in production would use domain-specific rules
        if any(keyword in concept.lower() for keyword in ["expert", "advanced", "complex"]):
            return KnowledgeMaturity.EXPERT_KNOWLEDGE
        elif any(keyword in concept.lower() for keyword in ["basic", "simple", "fundamental"]):
            return KnowledgeMaturity.DEFINITION
        else:
            return KnowledgeMaturity.APPLIED

    def _calculate_maturity_gap_severity(
        self,
        required: KnowledgeMaturity,
        current: KnowledgeMaturity,
    ) -> GapSeverity:
        """Calculate severity based on maturity gap."""
        gap = self._maturity_priority[required] - self._maturity_priority[current]
        
        if gap >= 3:
            return GapSeverity.CRITICAL
        elif gap == 2:
            return GapSeverity.HIGH
        elif gap == 1:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW

    def _generate_research_queries(self, concept: str) -> List[str]:
        """Generate research queries for a knowledge gap."""
        return [
            f"{concept} best practices",
            f"{concept} implementation guide",
            f"{concept} examples",
            f"how to implement {concept}",
        ]

    def _generate_practice_tasks(self, concept: str) -> List[str]:
        """Generate practice tasks for a knowledge gap."""
        return [
            f"Practice {concept} with sample project",
            f"Implement {concept} in a test environment",
            f"Review {concept} case studies",
        ]

    def _calculate_readiness_impact(self, gaps: List[KnowledgeGap], total_required: int) -> float:
        """Calculate impact on overall readiness based on gaps."""
        if total_required == 0:
            return 0.0
        
        weighted_gap_score = 0.0
        for gap in gaps:
            if gap.severity == GapSeverity.CRITICAL:
                weighted_gap_score += 1.0
            elif gap.severity == GapSeverity.HIGH:
                weighted_gap_score += 0.75
            elif gap.severity == GapSeverity.MEDIUM:
                weighted_gap_score += 0.5
            else:
                weighted_gap_score += 0.25
        
        return weighted_gap_score / total_required
