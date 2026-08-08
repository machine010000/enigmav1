from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.knowledge_governance.contracts import EvidenceScorer
from app.knowledge_governance.models import (
    Evidence,
    EvidenceScore,
    SourceType,
    KnowledgeFreshness,
)


class DefaultEvidenceScorer(EvidenceScorer):
    """Default implementation of evidence scoring."""

    # Source quality weights based on trust levels
    SOURCE_QUALITY_WEIGHTS = {
        SourceType.RESEARCH: 0.9,
        SourceType.ACADEMY: 0.85,
        SourceType.EXPERIMENT: 0.75,
        SourceType.MEMORY: 0.6,
        SourceType.EXTERNAL_SOURCE: 0.5,
        SourceType.USER_INPUT: 0.3,
    }

    def score(self, evidence: Evidence, context: Optional[Dict[str, Any]] = None) -> EvidenceScore:
        """Score evidence based on multiple factors."""
        context = context or {}

        # 1. Source Quality
        source_quality = self._score_source_quality(evidence.source_type)

        # 2. Freshness
        freshness = self._score_freshness(evidence)

        # 3. Corroboration (if other evidence exists in context)
        corroboration = self._score_corroboration(evidence, context)

        # 4. Validation Status
        validation = self._score_validation(evidence.status)

        # Calculate total score
        total_score = (
            source_quality * 0.4 +
            freshness * 0.25 +
            corroboration * 0.2 +
            validation * 0.15
        )

        breakdown = {
            "source_quality": source_quality,
            "freshness": freshness,
            "corroboration": corroboration,
            "validation": validation,
            "source_type": evidence.source_type.value,
            "published_at": evidence.published_at.isoformat() if evidence.published_at else None,
        }

        return EvidenceScore(
            total_score=total_score,
            source_quality=source_quality,
            freshness=freshness,
            corroboration=corroboration,
            validation=validation,
            breakdown=breakdown,
        )

    def _score_source_quality(self, source_type: SourceType) -> float:
        """Score based on source type trust level."""
        return self.SOURCE_QUALITY_WEIGHTS.get(source_type, 0.5)

    def _score_freshness(self, evidence: Evidence) -> float:
        """Score based on evidence freshness."""
        if not evidence.published_at:
            return 0.5  # Neutral if no date

        age_days = (datetime.utcnow() - evidence.published_at).days

        # Freshness thresholds (in days)
        if age_days <= 30:
            return 1.0  # Very fresh
        elif age_days <= 90:
            return 0.8  # Fresh
        elif age_days <= 180:
            return 0.6  # Acceptable
        elif age_days <= 365:
            return 0.4  # Aging
        elif age_days <= 730:
            return 0.2  # Stale
        else:
            return 0.1  # Expired

    def _score_corroboration(self, evidence: Evidence, context: Dict[str, Any]) -> float:
        """Score based on corroboration from other sources."""
        other_evidence = context.get("other_evidence", [])
        if not other_evidence:
            return 0.5  # Neutral if no context

        # Count similar claims from different sources
        similar_claims = sum(
            1 for e in other_evidence
            if e.source_type != evidence.source_type and
            self._claims_are_similar(evidence.claim, e.claim)
        )

        if similar_claims >= 3:
            return 1.0  # Strong corroboration
        elif similar_claims == 2:
            return 0.8  # Good corroboration
        elif similar_claims == 1:
            return 0.6  # Some corroboration
        else:
            return 0.4  # No corroboration

    def _score_validation(self, status: str) -> float:
        """Score based on validation status."""
        if status == "validated":
            return 1.0
        elif status == "pending":
            return 0.5
        elif status == "rejected":
            return 0.0
        else:
            return 0.5  # Unknown

    def _claims_are_similar(self, claim1: str, claim2: str) -> bool:
        """Simple similarity check for claims."""
        # In a real implementation, this would use semantic similarity
        # For now, use simple word overlap
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())
        overlap = len(words1 & words2)
        return overlap >= 3  # At least 3 words in common
