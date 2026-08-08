from __future__ import annotations

from app.knowledge_governance.models import (
    Concept,
    ConceptStatus,
    ConceptVersion,
    ConceptRelationship,
    Evidence,
    EvidenceStatus,
    EvidenceScore,
    GovernanceEvent,
    GovernedKnowledge,
    KnowledgeConflict,
    KnowledgeFreshness,
    KnowledgeMaturity,
    CandidateKnowledge,
    RelationshipType,
    SourceType,
    ValidationResult,
)
from app.knowledge_governance.contracts import (
    KnowledgeValidator,
    EvidenceScorer,
    ConflictResolver,
    KnowledgeGovernanceService,
)
from app.knowledge_governance.service import DefaultKnowledgeGovernanceService
from app.knowledge_governance.validator import DefaultKnowledgeValidator
from app.knowledge_governance.scorer import DefaultEvidenceScorer
from app.knowledge_governance.conflict_resolver import DefaultConflictResolver

__all__ = [
    # Models
    "Concept",
    "ConceptStatus",
    "ConceptVersion",
    "ConceptRelationship",
    "Evidence",
    "EvidenceStatus",
    "EvidenceScore",
    "GovernanceEvent",
    "GovernedKnowledge",
    "KnowledgeConflict",
    "KnowledgeFreshness",
    "KnowledgeMaturity",
    "CandidateKnowledge",
    "RelationshipType",
    "SourceType",
    "ValidationResult",
    # Contracts
    "KnowledgeValidator",
    "EvidenceScorer",
    "ConflictResolver",
    "KnowledgeGovernanceService",
    # Implementations
    "DefaultKnowledgeGovernanceService",
    "DefaultKnowledgeValidator",
    "DefaultEvidenceScorer",
    "DefaultConflictResolver",
]

# Default service instance
knowledge_governance_service = DefaultKnowledgeGovernanceService()
