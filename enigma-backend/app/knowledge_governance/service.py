from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.knowledge_governance.contracts import (
    ConflictResolver,
    EvidenceScorer,
    KnowledgeGovernanceService,
    KnowledgeValidator,
)
from app.knowledge_governance.conflict_resolver import DefaultConflictResolver
from app.knowledge_governance.models import (
    CandidateKnowledge,
    Concept,
    ConceptRelationship,
    ConceptStatus,
    ConceptVersion,
    Evidence,
    EvidenceStatus,
    GovernedKnowledge,
    GovernanceEvent,
    KnowledgeConflict,
    KnowledgeFreshness,
    KnowledgeMaturity,
    RelationshipType,
    SourceType,
)
from app.knowledge_governance.scorer import DefaultEvidenceScorer
from app.knowledge_governance.validator import DefaultKnowledgeValidator


class DefaultKnowledgeGovernanceService(KnowledgeGovernanceService):
    """Default implementation of knowledge governance service."""

    def __init__(
        self,
        validator: Optional[KnowledgeValidator] = None,
        scorer: Optional[EvidenceScorer] = None,
        conflict_resolver: Optional[ConflictResolver] = None,
    ) -> None:
        self.validator = validator or DefaultKnowledgeValidator()
        self.scorer = scorer or DefaultEvidenceScorer()
        self.conflict_resolver = conflict_resolver or DefaultConflictResolver()

        # In-memory storage (in production, this would be a database)
        self._governed_knowledge: Dict[str, GovernedKnowledge] = {}
        self._governance_events: Dict[str, List[GovernanceEvent]] = {}

    def submit_candidate(self, candidate: CandidateKnowledge, actor: str = "system") -> GovernedKnowledge:
        """
        Submit candidate knowledge through the governance pipeline.

        Pipeline:
        1. validate()
        2. score_evidence()
        3. detect_conflicts()
        4. resolve_or_mark_unresolved()
        5. create_version()
        6. update_maturity()
        7. update_freshness()
        8. publish()
        """
        # Step 1: Validate
        validation_result = self.validator.validate(candidate)

        if not validation_result.is_valid:
            # Reject invalid candidates
            event = GovernanceEvent(
                candidate_id=candidate.id,
                action="rejected",
                actor=actor,
                reason=f"Validation failed: {', '.join(validation_result.errors)}",
                timestamp=datetime.utcnow(),
            )
            self._add_governance_event(candidate.id, event)

            # Return rejected knowledge
            return self._create_rejected_knowledge(candidate, validation_result)

        # Step 2: Score evidence
        scored_evidence = []
        for evidence in candidate.evidence:
            score = self.scorer.score(evidence)
            # Update evidence with score
            updated_evidence = replace(evidence, quality_score=score.total_score)
            scored_evidence.append(updated_evidence)

        # Step 3: Create concept from candidate
        concept = Concept(
            id=str(uuid.uuid4()),
            name=candidate.name,
            definition=candidate.definition,
            knowledge_maturity=candidate.proposed_maturity,
            knowledge_confidence=candidate.proposed_confidence,
            knowledge_freshness=self._calculate_freshness(scored_evidence),
            status=ConceptStatus.ACTIVE,
            version=1,
            evidence_ids=[e.id for e in scored_evidence],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Step 4: Detect conflicts
        existing_concepts = [gk.concept for gk in self._governed_knowledge.values()]
        conflicts = self.conflict_resolver.detect_conflicts(concept, existing_concepts)

        # Step 5: Resolve conflicts
        resolved_conflicts = []
        for conflict in conflicts:
            resolution = self.conflict_resolver.resolve_conflict(conflict, scored_evidence)
            if resolution:
                # Conflict resolved
                resolved_conflict = replace(
                    conflict,
                    resolution=resolution,
                    resolution_reason=f"Resolved in favor of {resolution}",
                    status="resolved",
                    resolved_at=datetime.utcnow(),
                )
                resolved_conflicts.append(resolved_conflict)
            else:
                # Mark as unresolved
                unresolved_conflict = replace(
                    conflict,
                    status="unresolved",
                )
                resolved_conflicts.append(unresolved_conflict)

        # Step 6: Create version
        version = ConceptVersion(
            version=1,
            concept_id=concept.id,
            definition=concept.definition,
            evidence_ids=concept.evidence_ids,
            reason="Initial version from candidate submission",
            confidence=concept.knowledge_confidence,
            maturity=concept.knowledge_maturity,
            freshness=concept.knowledge_freshness,
            created_at=datetime.utcnow(),
            status=concept.status,
        )

        # Step 7: Update maturity based on evidence
        updated_maturity = self._update_maturity_based_on_evidence(
            concept.knowledge_maturity,
            scored_evidence,
        )

        # Step 8: Publish
        updated_concept = replace(
            concept,
            knowledge_maturity=updated_maturity,
        )

        # Create governance event
        event = GovernanceEvent(
            candidate_id=candidate.id,
            action="published",
            actor=actor,
            evidence_ids=concept.evidence_ids,
            new_version=1,
            reason="Successfully passed governance pipeline",
            timestamp=datetime.utcnow(),
        )
        self._add_governance_event(updated_concept.id, event)

        # Create governed knowledge
        governed_knowledge = GovernedKnowledge(
            concept=updated_concept,
            versions=[version],
            conflicts=resolved_conflicts,
            relationships=[],
            governance_events=[event],
            validation_result=validation_result.to_dict(),
        )

        # Store
        self._governed_knowledge[updated_concept.id] = governed_knowledge

        return governed_knowledge

    def get_governed_knowledge(self, concept_id: str) -> Optional[GovernedKnowledge]:
        """Retrieve governed knowledge by concept ID."""
        return self._governed_knowledge.get(concept_id)

    def list_governed_knowledge(self, status: Optional[str] = None) -> List[GovernedKnowledge]:
        """List governed knowledge, optionally filtered by status."""
        all_knowledge = list(self._governed_knowledge.values())

        if status:
            return [gk for gk in all_knowledge if gk.concept.status.value == status]

        return all_knowledge

    def get_governance_history(self, concept_id: str) -> List[GovernanceEvent]:
        """Get audit trail for a concept."""
        return self._governance_events.get(concept_id, [])

    def _add_governance_event(self, concept_id: str, event: GovernanceEvent) -> None:
        """Add a governance event to the audit trail."""
        if concept_id not in self._governance_events:
            self._governance_events[concept_id] = []
        self._governance_events[concept_id].append(event)

    def _calculate_freshness(self, evidence: List[Evidence]) -> KnowledgeFreshness:
        """Calculate overall freshness from evidence."""
        if not evidence:
            return KnowledgeFreshness.UNKNOWN

        # Get the worst (oldest) freshness from evidence
        freshness_scores = []
        for ev in evidence:
            if ev.freshness == KnowledgeFreshness.FRESH:
                freshness_scores.append(1.0)
            elif ev.freshness == KnowledgeFreshness.AGING:
                freshness_scores.append(0.6)
            elif ev.freshness == KnowledgeFreshness.STALE:
                freshness_scores.append(0.3)
            elif ev.freshness == KnowledgeFreshness.EXPIRED:
                freshness_scores.append(0.1)
            else:
                freshness_scores.append(0.5)

        avg_freshness = sum(freshness_scores) / len(freshness_scores)

        if avg_freshness >= 0.8:
            return KnowledgeFreshness.FRESH
        elif avg_freshness >= 0.6:
            return KnowledgeFreshness.AGING
        elif avg_freshness >= 0.4:
            return KnowledgeFreshness.STALE
        elif avg_freshness >= 0.2:
            return KnowledgeFreshness.EXPIRED
        else:
            return KnowledgeFreshness.UNKNOWN

    def _update_maturity_based_on_evidence(
        self,
        current_maturity: KnowledgeMaturity,
        evidence: List[Evidence],
    ) -> KnowledgeMaturity:
        """Update maturity based on evidence quality and quantity."""
        if not evidence:
            return KnowledgeMaturity.UNKNOWN

        # Count high-quality evidence
        high_quality_count = sum(1 for e in evidence if e.quality_score >= 0.7)
        total_count = len(evidence)

        # Source diversity
        source_types = set(e.source_type for e in evidence)

        # Calculate achievable maturity based on evidence
        achievable_maturity = KnowledgeMaturity.UNKNOWN

        if total_count >= 1:
            achievable_maturity = KnowledgeMaturity.DEFINITION

        if total_count >= 2 and len(source_types) >= 2:
            achievable_maturity = KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES

        if high_quality_count >= 2 and total_count >= 3:
            achievable_maturity = KnowledgeMaturity.APPLIED

        if high_quality_count >= 3 and total_count >= 5:
            achievable_maturity = KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS

        if high_quality_count >= 5 and len(source_types) >= 3:
            achievable_maturity = KnowledgeMaturity.EXPERT_KNOWLEDGE

        # Return the achievable maturity (governance constrains, not promotes)
        return achievable_maturity

    def _create_rejected_knowledge(
        self,
        candidate: CandidateKnowledge,
        validation_result: Any,
    ) -> GovernedKnowledge:
        """Create a rejected knowledge object."""
        concept = Concept(
            id=str(uuid.uuid4()),
            name=candidate.name,
            definition=candidate.definition,
            status=ConceptStatus.REJECTED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return GovernedKnowledge(
            concept=concept,
            versions=[],
            conflicts=[],
            relationships=[],
            governance_events=[],
            validation_result=validation_result.to_dict(),
        )
