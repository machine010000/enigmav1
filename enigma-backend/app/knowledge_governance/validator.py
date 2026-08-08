from __future__ import annotations

from typing import List

from app.knowledge_governance.contracts import KnowledgeValidator
from app.knowledge_governance.models import (
    CandidateKnowledge,
    ValidationResult,
)


class DefaultKnowledgeValidator(KnowledgeValidator):
    """Default implementation of knowledge validation."""

    def validate(self, candidate: CandidateKnowledge) -> ValidationResult:
        """Validate candidate knowledge against governance policies."""
        errors: List[str] = []
        warnings: List[str] = []
        score = 1.0

        # Check definition
        if not candidate.definition or len(candidate.definition.strip()) < 10:
            errors.append("Definition must be at least 10 characters")
            score -= 0.3

        # Check evidence
        if not candidate.evidence:
            warnings.append("No evidence provided - concept will have low confidence")
            score -= 0.2
        elif len(candidate.evidence) < 2:
            warnings.append("Single evidence source - consider multiple sources for better confidence")
            score -= 0.1

        # Check evidence quality
        for evidence in candidate.evidence:
            if evidence.quality_score < 0.3:
                warnings.append(f"Evidence {evidence.id} has low quality score")
                score -= 0.05

        # Check confidence
        if candidate.proposed_confidence < 0.0 or candidate.proposed_confidence > 1.0:
            errors.append("Confidence must be between 0.0 and 1.0")
            score -= 0.2

        # Check maturity
        if candidate.proposed_maturity.value > 2 and len(candidate.evidence) < 2:
            errors.append("Maturity level 2+ requires multiple evidence sources")
            score -= 0.3

        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            score=score,
        )
