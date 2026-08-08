from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.knowledge_governance.models import (
    CandidateKnowledge,
    Concept,
    Evidence,
    EvidenceScore,
    GovernanceEvent,
    GovernedKnowledge,
    KnowledgeConflict,
    ValidationResult,
)


class KnowledgeValidator(ABC):
    """Contract for validating candidate knowledge."""

    @abstractmethod
    def validate(self, candidate: CandidateKnowledge) -> ValidationResult:
        """
        Validate candidate knowledge for entry into the knowledge system.

        Checks:
        - Definition exists and is meaningful
        - Evidence exists and has quality
        - Evidence freshness is acceptable
        - Confidence is reasonable
        - Consistency is maintained
        - Required metadata is present

        Validation does NOT mean "100% true" - it means "valid for entry
        according to current governance policy".
        """
        pass


class EvidenceScorer(ABC):
    """Contract for scoring evidence quality."""

    @abstractmethod
    def score(self, evidence: Evidence, context: Optional[Dict[str, Any]] = None) -> EvidenceScore:
        """
        Score evidence based on multiple factors.

        Factors:
        - Source Quality (trust level of source type)
        - Freshness (recency and relevance)
        - Corroboration (support from other sources)
        - Specificity (precision and detail)
        - Validation Status (whether evidence has been verified)

        Returns interpretable score with breakdown.
        """
        pass


class ConflictResolver(ABC):
    """Contract for resolving knowledge conflicts."""

    @abstractmethod
    def detect_conflicts(self, concept: Concept, existing_concepts: List[Concept]) -> List[KnowledgeConflict]:
        """Detect conflicts between competing knowledge claims."""
        pass

    @abstractmethod
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
        pass


class KnowledgeGovernanceService(ABC):
    """Contract for the main knowledge governance service."""

    @abstractmethod
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

        Prevents callers from bypassing governance.
        """
        pass

    @abstractmethod
    def get_governed_knowledge(self, concept_id: str) -> Optional[GovernedKnowledge]:
        """Retrieve governed knowledge by concept ID."""
        pass

    @abstractmethod
    def list_governed_knowledge(self, status: Optional[str] = None) -> List[GovernedKnowledge]:
        """List governed knowledge, optionally filtered by status."""
        pass

    @abstractmethod
    def get_governance_history(self, concept_id: str) -> List[GovernanceEvent]:
        """Get audit trail for a concept."""
        pass
