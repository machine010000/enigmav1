from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.knowledge_governance import Evidence, GovernedKnowledge, KnowledgeFreshness


class EvidenceGapSeverity(str, Enum):
    """Severity levels for evidence gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EvidenceGap:
    """A gap in evidence required for a job."""
    gap_id: str
    concept_id: str
    concept_name: str
    required_evidence_type: str
    current_evidence_count: int
    required_evidence_count: int
    quality_threshold: float
    current_quality: float
    freshness_threshold: KnowledgeFreshness
    current_freshness: KnowledgeFreshness
    severity: EvidenceGapSeverity
    description: str
    domain_id: str
    job_id: str
    suggested_research_queries: List[str] = field(default_factory=list)
    identified_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvidenceGapAnalysisResult:
    """Result of evidence gap analysis."""
    job_id: str
    domain_id: str
    total_gaps: int
    critical_gaps: int
    high_gaps: int
    medium_gaps: int
    low_gaps: int
    gaps: List[EvidenceGap] = field(default_factory=list)
    readiness_impact: float = 0.0  # 0.0 to 1.0, impact on overall readiness
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvidenceGapAnalyzer:
    """
    Analyzes evidence gaps for job requirements.
    
    Compares required evidence (from job capabilities) against available
    governed evidence to identify gaps in quantity, quality, and freshness.
    """

    def __init__(self) -> None:
        self._freshness_priority = {
            KnowledgeFreshness.FRESH: 4,
            KnowledgeFreshness.AGING: 3,
            KnowledgeFreshness.STALE: 2,
            KnowledgeFreshness.EXPIRED: 1,
            KnowledgeFreshness.UNKNOWN: 0,
        }
        self._default_quality_threshold = 0.7
        self._default_freshness_threshold = KnowledgeFreshness.AGING
        self._default_evidence_count = 2

    def analyze_gaps(
        self,
        job_id: str,
        domain_id: str,
        required_evidence: List[str],
        available_knowledge: List[GovernedKnowledge],
    ) -> EvidenceGapAnalysisResult:
        """
        Analyze evidence gaps for a job.
        
        Args:
            job_id: The job identifier
            domain_id: The domain identifier
            required_evidence: List of required evidence types/concepts
            available_knowledge: List of available governed knowledge with evidence
            
        Returns:
            EvidenceGapAnalysisResult with identified gaps
        """
        gaps: List[EvidenceGap] = []
        
        # Create a map of available knowledge for quick lookup
        available_map = {k.name: k for k in available_knowledge}
        
        for required_concept in required_evidence:
            governed = available_map.get(required_concept)
            
            if governed is None:
                # Evidence completely missing
                gap = EvidenceGap(
                    gap_id=f"evidence_gap_{hash(required_concept)}",
                    concept_id=required_concept,
                    concept_name=required_concept,
                    required_evidence_type="general",
                    current_evidence_count=0,
                    required_evidence_count=self._default_evidence_count,
                    quality_threshold=self._default_quality_threshold,
                    current_quality=0.0,
                    freshness_threshold=self._default_freshness_threshold,
                    current_freshness=KnowledgeFreshness.UNKNOWN,
                    severity=EvidenceGapSeverity.CRITICAL,
                    description=f"Required evidence for '{required_concept}' is completely missing",
                    domain_id=domain_id,
                    job_id=job_id,
                    suggested_research_queries=self._generate_research_queries(required_concept),
                )
                gaps.append(gap)
            else:
                # Evidence exists but check quality, quantity, and freshness
                evidence_list = governed.evidence if governed.evidence else []
                
                # Check quantity
                if len(evidence_list) < self._default_evidence_count:
                    gap = EvidenceGap(
                        gap_id=f"evidence_gap_{hash(required_concept)}_quantity",
                        concept_id=required_concept,
                        concept_name=required_concept,
                        required_evidence_type="general",
                        current_evidence_count=len(evidence_list),
                        required_evidence_count=self._default_evidence_count,
                        quality_threshold=self._default_quality_threshold,
                        current_quality=self._calculate_average_quality(evidence_list),
                        freshness_threshold=self._default_freshness_threshold,
                        current_freshness=governed.freshness,
                        severity=self._calculate_quantity_gap_severity(len(evidence_list)),
                        description=f"Insufficient evidence for '{required_concept}': {len(evidence_list)} found, {self._default_evidence_count} required",
                        domain_id=domain_id,
                        job_id=job_id,
                        suggested_research_queries=self._generate_research_queries(required_concept),
                    )
                    gaps.append(gap)
                
                # Check quality
                avg_quality = self._calculate_average_quality(evidence_list)
                if avg_quality < self._default_quality_threshold:
                    gap = EvidenceGap(
                        gap_id=f"evidence_gap_{hash(required_concept)}_quality",
                        concept_id=required_concept,
                        concept_name=required_concept,
                        required_evidence_type="general",
                        current_evidence_count=len(evidence_list),
                        required_evidence_count=self._default_evidence_count,
                        quality_threshold=self._default_quality_threshold,
                        current_quality=avg_quality,
                        freshness_threshold=self._default_freshness_threshold,
                        current_freshness=governed.freshness,
                        severity=self._calculate_quality_gap_severity(avg_quality),
                        description=f"Low evidence quality for '{required_concept}': {avg_quality:.2f}, threshold {self._default_quality_threshold}",
                        domain_id=domain_id,
                        job_id=job_id,
                        suggested_research_queries=self._generate_research_queries(required_concept),
                    )
                    gaps.append(gap)
                
                # Check freshness
                if self._freshness_priority[governed.freshness] < self._freshness_priority[self._default_freshness_threshold]:
                    gap = EvidenceGap(
                        gap_id=f"evidence_gap_{hash(required_concept)}_freshness",
                        concept_id=required_concept,
                        concept_name=required_concept,
                        required_evidence_type="general",
                        current_evidence_count=len(evidence_list),
                        required_evidence_count=self._default_evidence_count,
                        quality_threshold=self._default_quality_threshold,
                        current_quality=avg_quality,
                        freshness_threshold=self._default_freshness_threshold,
                        current_freshness=governed.freshness,
                        severity=self._calculate_freshness_gap_severity(governed.freshness),
                        description=f"Stale evidence for '{required_concept}': {governed.freshness.value}, threshold {self._default_freshness_threshold.value}",
                        domain_id=domain_id,
                        job_id=job_id,
                        suggested_research_queries=self._generate_research_queries(required_concept),
                    )
                    gaps.append(gap)
        
        # Calculate gap statistics
        critical_count = sum(1 for g in gaps if g.severity == EvidenceGapSeverity.CRITICAL)
        high_count = sum(1 for g in gaps if g.severity == EvidenceGapSeverity.HIGH)
        medium_count = sum(1 for g in gaps if g.severity == EvidenceGapSeverity.MEDIUM)
        low_count = sum(1 for g in gaps if g.severity == EvidenceGapSeverity.LOW)
        
        # Calculate readiness impact
        readiness_impact = self._calculate_readiness_impact(gaps, len(required_evidence))
        
        return EvidenceGapAnalysisResult(
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

    def _calculate_average_quality(self, evidence_list: List[Evidence]) -> float:
        """Calculate average quality score from evidence list."""
        if not evidence_list:
            return 0.0
        
        total_quality = sum(e.quality_score for e in evidence_list if e.quality_score is not None)
        return total_quality / len(evidence_list)

    def _calculate_quantity_gap_severity(self, current_count: int) -> EvidenceGapSeverity:
        """Calculate severity based on evidence quantity gap."""
        if current_count == 0:
            return EvidenceGapSeverity.CRITICAL
        elif current_count == 1:
            return EvidenceGapSeverity.HIGH
        elif current_count == 2:
            return EvidenceGapSeverity.MEDIUM
        else:
            return EvidenceGapSeverity.LOW

    def _calculate_quality_gap_severity(self, current_quality: float) -> EvidenceGapSeverity:
        """Calculate severity based on evidence quality gap."""
        if current_quality < 0.3:
            return EvidenceGapSeverity.CRITICAL
        elif current_quality < 0.5:
            return EvidenceGapSeverity.HIGH
        elif current_quality < 0.7:
            return EvidenceGapSeverity.MEDIUM
        else:
            return EvidenceGapSeverity.LOW

    def _calculate_freshness_gap_severity(self, current_freshness: KnowledgeFreshness) -> EvidenceGapSeverity:
        """Calculate severity based on evidence freshness gap."""
        if current_freshness == KnowledgeFreshness.UNKNOWN:
            return EvidenceGapSeverity.CRITICAL
        elif current_freshness == KnowledgeFreshness.STALE:
            return EvidenceGapSeverity.HIGH
        elif current_freshness == KnowledgeFreshness.RECENT:
            return EvidenceGapSeverity.MEDIUM
        else:
            return EvidenceGapSeverity.LOW

    def _generate_research_queries(self, concept: str) -> List[str]:
        """Generate research queries for an evidence gap."""
        return [
            f"{concept} evidence and case studies",
            f"{concept} recent research and studies",
            f"{concept} industry reports",
            f"{concept} expert opinions and analysis",
        ]

    def _calculate_readiness_impact(self, gaps: List[EvidenceGap], total_required: int) -> float:
        """Calculate impact on overall readiness based on evidence gaps."""
        if total_required == 0:
            return 0.0
        
        weighted_gap_score = 0.0
        for gap in gaps:
            if gap.severity == EvidenceGapSeverity.CRITICAL:
                weighted_gap_score += 1.0
            elif gap.severity == EvidenceGapSeverity.HIGH:
                weighted_gap_score += 0.75
            elif gap.severity == EvidenceGapSeverity.MEDIUM:
                weighted_gap_score += 0.5
            else:
                weighted_gap_score += 0.25
        
        return weighted_gap_score / total_required
