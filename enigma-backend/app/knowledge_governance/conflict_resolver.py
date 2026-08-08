from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from app.knowledge_governance.contracts import ConflictResolver
from app.knowledge_governance.models import (
    Concept,
    Evidence,
    KnowledgeConflict,
)


class DefaultConflictResolver(ConflictResolver):
    """Default implementation of conflict resolution."""

    def detect_conflicts(self, concept: Concept, existing_concepts: List[Concept]) -> List[KnowledgeConflict]:
        """Detect conflicts between competing knowledge claims."""
        conflicts: List[KnowledgeConflict] = []

        for existing in existing_concepts:
            if self._are_concepts_conflicting(concept, existing):
                conflict = KnowledgeConflict(
                    id=str(uuid.uuid4()),
                    concept_id=concept.id,
                    competing_claims=[
                        f"{concept.name}: {concept.definition}",
                        f"{existing.name}: {existing.definition}",
                    ],
                    evidence_comparison={
                        "concept_evidence_count": len(concept.evidence_ids),
                        "existing_evidence_count": len(existing.evidence_ids),
                        "concept_confidence": concept.knowledge_confidence,
                        "existing_confidence": existing.knowledge_confidence,
                    },
                    status="unresolved",
                    created_at=datetime.utcnow(),
                )
                conflicts.append(conflict)

        return conflicts

    def resolve_conflict(self, conflict: KnowledgeConflict, evidence: List[Evidence]) -> Optional[str]:
        """
        Resolve a knowledge conflict based on governance rules.

        Resolution Rules (priority order):
        1. Higher Evidence Quality
        2. Higher Confidence
        3. Better Freshness
        4. Multiple Independent Sources
        5. Validated Experience

        If unresolvable:
        - Return None
        - Mark as UNRESOLVED
        - Do NOT convert to truth
        """
        evidence_comparison = conflict.evidence_comparison

        # Rule 1: Higher Evidence Quality
        concept_evidence_count = evidence_comparison.get("concept_evidence_count", 0)
        existing_evidence_count = evidence_comparison.get("existing_evidence_count", 0)

        if concept_evidence_count > existing_evidence_count + 1:
            return "concept"  # Concept wins due to more evidence
        elif existing_evidence_count > concept_evidence_count + 1:
            return "existing"  # Existing wins due to more evidence

        # Rule 2: Higher Confidence
        concept_confidence = evidence_comparison.get("concept_confidence", 0.0)
        existing_confidence = evidence_comparison.get("existing_confidence", 0.0)

        if concept_confidence > existing_confidence + 0.2:
            return "concept"  # Concept wins due to higher confidence
        elif existing_confidence > concept_confidence + 0.2:
            return "existing"  # Existing wins due to higher confidence

        # Rule 3: Better Freshness (if evidence available)
        if evidence:
            concept_freshness = self._get_average_freshness(
                [e for e in evidence if e.id in conflict.competing_claims[0]]
            )
            existing_freshness = self._get_average_freshness(
                [e for e in evidence if e.id in conflict.competing_claims[1]]
            )

            if concept_freshness > existing_freshness + 0.2:
                return "concept"
            elif existing_freshness > concept_freshness + 0.2:
                return "existing"

        # Rule 4: Multiple Independent Sources
        # (Simplified check - in real implementation would analyze source diversity)
        if concept_evidence_count >= 3 and existing_evidence_count < 3:
            return "concept"
        elif existing_evidence_count >= 3 and concept_evidence_count < 3:
            return "existing"

        # Rule 5: Validated Experience
        # (Simplified - in real implementation would check validation status)
        # If we reach here, conflict is unresolvable with current evidence
        return None  # Mark as UNRESOLVED

    def _are_concepts_conflicting(self, concept1: Concept, concept2: Concept) -> bool:
        """Check if two concepts have conflicting definitions."""
        # Simple check: if names are similar but definitions differ significantly
        if concept1.name.lower() == concept2.name.lower():
            # Same name, check if definitions are different
            return concept1.definition != concept2.definition

        # Check for semantic conflict (simplified)
        words1 = set(concept1.definition.lower().split())
        words2 = set(concept2.definition.lower().split())

        # If they share many words but have opposite meanings (simplified)
        overlap = len(words1 & words2)
        min_words = min(len(words1), len(words2))

        if overlap > min_words * 0.7:  # 70% overlap
            # High overlap but different definitions suggests conflict
            return concept1.definition != concept2.definition

        return False

    def _get_average_freshness(self, evidence_list: List[Evidence]) -> float:
        """Calculate average freshness score from evidence."""
        if not evidence_list:
            return 0.5

        freshness_scores = []
        for evidence in evidence_list:
            # Convert freshness enum to score
            if evidence.freshness.value == "fresh":
                freshness_scores.append(1.0)
            elif evidence.freshness.value == "aging":
                freshness_scores.append(0.6)
            elif evidence.freshness.value == "stale":
                freshness_scores.append(0.3)
            elif evidence.freshness.value == "expired":
                freshness_scores.append(0.1)
            else:
                freshness_scores.append(0.5)

        return sum(freshness_scores) / len(freshness_scores)
