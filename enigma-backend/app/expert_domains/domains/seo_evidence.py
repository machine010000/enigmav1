from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.knowledge_governance.models import (
    Evidence,
    EvidenceScore,
    SourceType,
    KnowledgeFreshness,
)


class EvidenceCategory(str, Enum):
    """Categories of SEO evidence."""
    OFFICIAL_DOCUMENTATION = "official_documentation"
    VERIFIED_CASE_STUDY = "verified_case_study"
    MULTIPLE_INDEPENDENT_SOURCES = "multiple_independent_sources"
    EXPERIMENT = "experiment"
    REFLECTION = "reflection"
    SIMULATION = "simulation"
    INDUSTRY_BENCHMARK = "industry_benchmark"
    USER_REPORT = "user_report"


class EvidenceQuality(str, Enum):
    """Quality levels for evidence."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNRELIABLE = "unreliable"


@dataclass
class SEOEvidenceValidation:
    """Validation result for SEO evidence."""
    evidence_id: str
    is_valid: bool
    quality: EvidenceQuality
    confidence: float
    freshness: KnowledgeFreshness
    maturity_impact: float  # -1.0 to 1.0, impact on concept maturity
    source_quality: float  # 0.0 to 1.0
    validation_reasons: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


class SEOEvidenceScorer:
    """
    Scores SEO evidence based on multiple factors.

    Implements EvidenceScorer contract for SEO-specific evidence evaluation.
    """

    def __init__(self) -> None:
        self._source_trust_weights = {
            SourceType.RESEARCH: 0.9,
            SourceType.ACADEMY: 0.85,
            SourceType.EXPERIMENT: 0.7,
            SourceType.EXTERNAL_SOURCE: 0.6,
            SourceType.USER_INPUT: 0.4,
            SourceType.MEMORY: 0.5,
        }

        self._source_quality_weights = {
            EvidenceCategory.OFFICIAL_DOCUMENTATION: 0.95,
            EvidenceCategory.VERIFIED_CASE_STUDY: 0.85,
            EvidenceCategory.MULTIPLE_INDEPENDENT_SOURCES: 0.9,
            EvidenceCategory.EXPERIMENT: 0.7,
            EvidenceCategory.REFLECTION: 0.5,
            EvidenceCategory.SIMULATION: 0.4,
            EvidenceCategory.INDUSTRY_BENCHMARK: 0.75,
            EvidenceCategory.USER_REPORT: 0.3,
        }

    def score(self, evidence: Evidence, context: Optional[Dict[str, Any]] = None) -> EvidenceScore:
        """
        Score SEO evidence based on multiple factors.

        Factors:
        - Source Quality (trust level of source type)
        - Freshness (recency and relevance)
        - Corroboration (support from other sources)
        - Specificity (precision and detail)
        - Validation Status (whether evidence has been verified)

        Returns interpretable score with breakdown.
        """
        context = context or {}

        # Calculate individual factors
        source_quality = self._score_source_quality(evidence, context)
        freshness = self._score_freshness(evidence, context)
        corroboration = self._score_corroboration(evidence, context)
        specificity = self._score_specificity(evidence, context)
        validation = self._score_validation(evidence, context)

        # Calculate weighted total score
        weights = {
            "source_quality": 0.3,
            "freshness": 0.2,
            "corroboration": 0.25,
            "specificity": 0.15,
            "validation": 0.1,
        }

        total_score = (
            source_quality * weights["source_quality"]
            + freshness * weights["freshness"]
            + corroboration * weights["corroboration"]
            + specificity * weights["specificity"]
            + validation * weights["validation"]
        )

        breakdown = {
            "source_quality": source_quality,
            "freshness": freshness,
            "corroboration": corroboration,
            "specificity": specificity,
            "validation": validation,
            "weights": weights,
        }

        return EvidenceScore(
            total_score=total_score,
            source_quality=source_quality,
            freshness=freshness,
            corroboration=corroboration,
            validation=validation,
            breakdown=breakdown,
        )

    def _score_source_quality(self, evidence: Evidence, context: Dict[str, Any]) -> float:
        """Score based on source type and trust."""
        base_score = self._source_trust_weights.get(evidence.source_type, 0.5)

        # Adjust for known high-quality sources
        source = evidence.source.lower()
        if "google" in source or "search central" in source:
            base_score = min(base_score + 0.1, 1.0)
        elif "moz" in source or "ahrefs" in source or "semrush" in source:
            base_score = min(base_score + 0.05, 1.0)

        return base_score

    def _score_freshness(self, evidence: Evidence, context: Dict[str, Any]) -> float:
        """Score based on evidence freshness."""
        # Use evidence's own freshness if available
        if evidence.freshness == KnowledgeFreshness.FRESH:
            return 1.0
        elif evidence.freshness == KnowledgeFreshness.AGING:
            return 0.7
        elif evidence.freshness == KnowledgeFreshness.STALE:
            return 0.4
        elif evidence.freshness == KnowledgeFreshness.EXPIRED:
            return 0.1
        else:
            # Calculate based on timestamp
            age = datetime.utcnow() - evidence.retrieved_at
            if age < timedelta(days=30):
                return 1.0
            elif age < timedelta(days=90):
                return 0.8
            elif age < timedelta(days=180):
                return 0.6
            elif age < timedelta(days=365):
                return 0.4
            else:
                return 0.2

    def _score_corroboration(self, evidence: Evidence, context: Dict[str, Any]) -> float:
        """Score based on corroboration from other sources."""
        # Check if context has corroboration data
        corroborating_sources = context.get("corroborating_sources", 0)
        
        if corroborating_sources >= 3:
            return 1.0
        elif corroborating_sources == 2:
            return 0.8
        elif corroborating_sources == 1:
            return 0.6
        else:
            return 0.3

    def _score_specificity(self, evidence: Evidence, context: Dict[str, Any]) -> float:
        """Score based on specificity and detail of evidence."""
        claim_length = len(evidence.claim)
        
        if claim_length > 500:
            return 1.0
        elif claim_length > 300:
            return 0.8
        elif claim_length > 150:
            return 0.6
        elif claim_length > 50:
            return 0.4
        else:
            return 0.2

    def _score_validation(self, evidence: Evidence, context: Dict[str, Any]) -> float:
        """Score based on validation status."""
        if evidence.status.value == "validated":
            return 1.0
        elif evidence.status.value == "pending":
            return 0.5
        else:  # rejected
            return 0.0


class SEOEvidenceValidator:
    """
    Validates SEO evidence and determines quality and maturity impact.

    Provides detailed validation results for SEO-specific evidence.
    """

    def __init__(self) -> None:
        self._scorer = SEOEvidenceScorer()

    def validate(self, evidence: Evidence, context: Optional[Dict[str, Any]] = None) -> SEOEvidenceValidation:
        """
        Validate SEO evidence.

        Returns detailed validation including:
        - Validity check
        - Quality level
        - Confidence
        - Freshness
        - Maturity impact
        - Source quality
        - Validation reasons
        """
        context = context or {}

        # Score the evidence
        score = self._scorer.score(evidence, context)

        # Determine quality level
        quality = self._determine_quality(score.total_score)

        # Determine validity
        is_valid = quality != EvidenceQuality.UNRELIABLE

        # Calculate maturity impact
        maturity_impact = self._calculate_maturity_impact(score, quality)

        # Generate validation reasons
        validation_reasons = self._generate_validation_reasons(score, quality, evidence)

        return SEOEvidenceValidation(
            evidence_id=evidence.id,
            is_valid=is_valid,
            quality=quality,
            confidence=score.total_score,
            freshness=evidence.freshness,
            maturity_impact=maturity_impact,
            source_quality=score.source_quality,
            validation_reasons=validation_reasons,
        )

    def _determine_quality(self, total_score: float) -> EvidenceQuality:
        """Determine evidence quality level from score."""
        if total_score >= 0.9:
            return EvidenceQuality.CRITICAL
        elif total_score >= 0.75:
            return EvidenceQuality.HIGH
        elif total_score >= 0.6:
            return EvidenceQuality.MEDIUM
        elif total_score >= 0.4:
            return EvidenceQuality.LOW
        else:
            return EvidenceQuality.UNRELIABLE

    def _calculate_maturity_impact(self, score: EvidenceScore, quality: EvidenceQuality) -> float:
        """Calculate impact on concept maturity."""
        base_impact = score.total_score * 0.5  # Base impact from score

        # Adjust based on quality
        if quality == EvidenceQuality.CRITICAL:
            base_impact += 0.3
        elif quality == EvidenceQuality.HIGH:
            base_impact += 0.2
        elif quality == EvidenceQuality.MEDIUM:
            base_impact += 0.1
        elif quality == EvidenceQuality.LOW:
            base_impact -= 0.1
        else:  # UNRELIABLE
            base_impact -= 0.3

        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, base_impact))

    def _generate_validation_reasons(
        self,
        score: EvidenceScore,
        quality: EvidenceQuality,
        evidence: Evidence,
    ) -> List[str]:
        """Generate human-readable validation reasons."""
        reasons = []

        # Source quality
        if score.source_quality >= 0.8:
            reasons.append("High-quality source")
        elif score.source_quality >= 0.6:
            reasons.append("Medium-quality source")
        else:
            reasons.append("Low-quality source")

        # Freshness
        if score.freshness >= 0.8:
            reasons.append("Fresh evidence")
        elif score.freshness >= 0.5:
            reasons.append("Aging evidence")
        else:
            reasons.append("Stale evidence")

        # Corroboration
        if score.corroboration >= 0.8:
            reasons.append("Well-corroborated")
        elif score.corroboration >= 0.5:
            reasons.append("Some corroboration")
        else:
            reasons.append("Limited corroboration")

        # Validation status
        if evidence.status.value == "validated":
            reasons.append("Validated evidence")
        elif evidence.status.value == "pending":
            reasons.append("Pending validation")
        else:
            reasons.append("Rejected evidence")

        return reasons


class SEOEvidenceAggregator:
    """
    Aggregates multiple evidence sources for a concept.

    Provides combined scoring and validation for multiple evidence items.
    """

    def __init__(self) -> None:
        self._validator = SEOEvidenceValidator()

    def aggregate_evidence(
        self,
        evidence_list: List[Evidence],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate multiple evidence sources.

        Returns:
        - Combined score
        - Average quality
        - Total maturity impact
        - Validation summary
        - Best evidence
        """
        if not evidence_list:
            return {
                "combined_score": 0.0,
                "average_quality": EvidenceQuality.UNRELIABLE,
                "total_maturity_impact": 0.0,
                "validation_summary": "No evidence",
                "best_evidence": None,
                "evidence_count": 0,
            }

        context = context or {}
        validations = []
        total_score = 0.0
        total_maturity_impact = 0.0
        best_validation = None
        best_score = -1.0

        # Validate each evidence
        for evidence in evidence_list:
            # Update context with corroboration count
            context["corroborating_sources"] = len(evidence_list) - 1
            
            validation = self._validator.validate(evidence, context)
            validations.append(validation)

            total_score += validation.confidence
            total_maturity_impact += validation.maturity_impact

            # Track best evidence
            if validation.confidence > best_score:
                best_score = validation.confidence
                best_validation = validation

        # Calculate aggregates
        average_score = total_score / len(validations)
        average_quality = self._validator._determine_quality(average_score)
        total_maturity_impact = total_maturity_impact / len(validations)

        # Generate validation summary
        valid_count = sum(1 for v in validations if v.is_valid)
        validation_summary = f"{valid_count}/{len(validations)} evidence valid"

        return {
            "combined_score": average_score,
            "average_quality": average_quality,
            "total_maturity_impact": total_maturity_impact,
            "validation_summary": validation_summary,
            "best_evidence": best_validation,
            "evidence_count": len(evidence_list),
            "individual_validations": validations,
        }
