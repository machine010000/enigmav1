from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class KnowledgeMaturity(int, Enum):
    """Knowledge maturity levels."""
    UNKNOWN = 0
    DEFINITION = 1
    SUPPORTED_BY_MULTIPLE_SOURCES = 2
    APPLIED = 3
    VALIDATED_IN_REAL_PROJECTS = 4
    EXPERT_KNOWLEDGE = 5


class KnowledgeFreshness(str, Enum):
    """Knowledge freshness categories."""
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ConceptStatus(str, Enum):
    """Concept lifecycle status."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class EvidenceStatus(str, Enum):
    """Evidence status."""
    VALIDATED = "validated"
    PENDING = "pending"
    REJECTED = "rejected"


class SourceType(str, Enum):
    """Evidence source types with different trust levels."""
    RESEARCH = "research"
    ACADEMY = "academy"
    MEMORY = "memory"
    USER_INPUT = "user_input"
    EXPERIMENT = "experiment"
    EXTERNAL_SOURCE = "external_source"


class RelationshipType(str, Enum):
    """Knowledge graph relationship types."""
    RELATED_TO = "related_to"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    SUPERSEDES = "supersedes"


@dataclass(frozen=True)
class Evidence:
    """Represents evidence supporting or contradicting knowledge."""
    id: str
    source: str
    source_type: SourceType
    claim: str
    retrieved_at: datetime
    published_at: Optional[datetime] = None
    quality_score: float = 0.0
    confidence: float = 0.0
    freshness: KnowledgeFreshness = KnowledgeFreshness.UNKNOWN
    status: EvidenceStatus = EvidenceStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "source_type": self.source_type.value,
            "claim": self.claim,
            "retrieved_at": self.retrieved_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "quality_score": self.quality_score,
            "confidence": self.confidence,
            "freshness": self.freshness.value,
            "status": self.status.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Concept:
    """Represents a knowledge concept - the basic unit of knowledge."""
    id: str
    name: str
    definition: str
    knowledge_maturity: KnowledgeMaturity = KnowledgeMaturity.UNKNOWN
    knowledge_confidence: float = 0.0
    knowledge_freshness: KnowledgeFreshness = KnowledgeFreshness.UNKNOWN
    status: ConceptStatus = ConceptStatus.ACTIVE
    version: int = 1
    evidence_ids: List[str] = field(default_factory=list)
    related_concept_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "knowledge_maturity": self.knowledge_maturity.value,
            "knowledge_confidence": self.knowledge_confidence,
            "knowledge_freshness": self.knowledge_freshness.value,
            "status": self.status.value,
            "version": self.version,
            "evidence_ids": self.evidence_ids,
            "related_concept_ids": self.related_concept_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ConceptVersion:
    """Immutable version of a concept for history tracking."""
    version: int
    concept_id: str
    definition: str
    evidence_ids: List[str] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.0
    maturity: KnowledgeMaturity = KnowledgeMaturity.UNKNOWN
    freshness: KnowledgeFreshness = KnowledgeFreshness.UNKNOWN
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ConceptStatus = ConceptStatus.ACTIVE
    superseded_by: Optional[str] = None
    superseded_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "concept_id": self.concept_id,
            "definition": self.definition,
            "evidence_ids": self.evidence_ids,
            "reason": self.reason,
            "confidence": self.confidence,
            "maturity": self.maturity.value,
            "freshness": self.freshness.value,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "superseded_by": self.superseded_by,
            "superseded_reason": self.superseded_reason,
        }


@dataclass(frozen=True)
class KnowledgeConflict:
    """Represents a conflict between competing knowledge claims."""
    id: str
    concept_id: str
    competing_claims: List[str] = field(default_factory=list)
    evidence_comparison: Dict[str, Any] = field(default_factory=dict)
    resolution: Optional[str] = None
    resolution_reason: Optional[str] = None
    status: str = "unresolved"  # unresolved, resolved, rejected
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "concept_id": self.concept_id,
            "competing_claims": self.competing_claims,
            "evidence_comparison": self.evidence_comparison,
            "resolution": self.resolution,
            "resolution_reason": self.resolution_reason,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass(frozen=True)
class ConceptRelationship:
    """Represents a relationship between concepts in the knowledge graph."""
    id: str
    source_concept_id: str
    target_concept_id: str
    relationship_type: RelationshipType
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class GovernanceEvent:
    """Audit trail entry for governance decisions."""
    candidate_id: str
    action: str
    actor: str
    evidence_ids: List[str] = field(default_factory=list)
    previous_version: Optional[int] = None
    new_version: Optional[int] = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "action": self.action,
            "actor": self.actor,
            "evidence_ids": self.evidence_ids,
            "previous_version": self.previous_version,
            "new_version": self.new_version,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CandidateKnowledge:
    """Knowledge candidate submitted for governance."""
    id: str
    name: str
    definition: str
    evidence: List[Evidence] = field(default_factory=list)
    proposed_maturity: KnowledgeMaturity = KnowledgeMaturity.UNKNOWN
    proposed_confidence: float = 0.0
    source: str = "unknown"
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "evidence": [e.to_dict() for e in self.evidence],
            "proposed_maturity": self.proposed_maturity.value,
            "proposed_confidence": self.proposed_confidence,
            "source": self.source,
            "submitted_at": self.submitted_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GovernedKnowledge:
    """Knowledge that has passed through governance pipeline."""
    concept: Concept
    versions: List[ConceptVersion] = field(default_factory=list)
    conflicts: List[KnowledgeConflict] = field(default_factory=list)
    relationships: List[ConceptRelationship] = field(default_factory=list)
    governance_events: List[GovernanceEvent] = field(default_factory=list)
    validation_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept.to_dict(),
            "versions": [v.to_dict() for v in self.versions],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "relationships": [r.to_dict() for r in self.relationships],
            "governance_events": [e.to_dict() for e in self.governance_events],
            "validation_result": self.validation_result,
        }


class ValidationResult:
    """Result of knowledge validation."""
    def __init__(
        self,
        is_valid: bool,
        errors: List[str],
        warnings: List[str],
        score: float,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "score": self.score,
        }


class EvidenceScore:
    """Result of evidence scoring."""
    def __init__(
        self,
        total_score: float,
        source_quality: float,
        freshness: float,
        corroboration: float,
        validation: float,
        breakdown: Dict[str, Any],
    ):
        self.total_score = total_score
        self.source_quality = source_quality
        self.freshness = freshness
        self.corroboration = corroboration
        self.validation = validation
        self.breakdown = breakdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": self.total_score,
            "source_quality": self.source_quality,
            "freshness": self.freshness,
            "corroboration": self.corroboration,
            "validation": self.validation,
            "breakdown": self.breakdown,
        }
