from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.knowledge_governance import KnowledgeMaturity, KnowledgeFreshness


class DomainLifecycleStage(str, Enum):
    """Lifecycle stages for expert domains."""
    UNKNOWN = "unknown"
    LEARNING = "learning"
    GROWING = "growing"
    OPERATIONAL = "operational"
    EXPERT = "expert"
    SELF_IMPROVING = "self_improving"


class ReasoningPatternType(str, Enum):
    """Types of reasoning patterns."""
    DIAGNOSIS = "diagnosis"
    COMPARISON = "comparison"
    OPTIMIZATION = "optimization"
    PREDICTION = "prediction"
    PLANNING = "planning"
    EVALUATION = "evaluation"
    RECOMMENDATION = "recommendation"


@dataclass(frozen=True)
class DomainIdentity:
    """Identity information for an expert domain."""
    domain_id: str
    name: str
    description: str
    version: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_domain: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeArea:
    """A knowledge area within a domain."""
    area_id: str
    name: str
    description: str
    required_concepts: List[str] = field(default_factory=list)
    importance: str = "medium"  # low, medium, high, critical


@dataclass(frozen=True)
class DomainConcept:
    """A concept within an expert domain."""
    concept_id: str
    name: str
    definition: str
    importance: str  # low, medium, high, critical
    related_concepts: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    knowledge_maturity: KnowledgeMaturity = KnowledgeMaturity.UNKNOWN
    freshness: KnowledgeFreshness = KnowledgeFreshness.UNKNOWN
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class DomainEvidence:
    """Evidence supporting domain knowledge."""
    evidence_id: str
    source: str
    reliability: float  # 0.0 to 1.0
    timestamp: datetime
    domain: str
    concept_id: str
    confidence: float  # 0.0 to 1.0
    validation_status: str  # pending, validated, rejected
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningPattern:
    """A reusable reasoning pattern for expert domains."""
    pattern_id: str
    pattern_type: ReasoningPatternType
    name: str
    description: str
    required_inputs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionRule:
    """A decision rule for expert domains."""
    rule_id: str
    name: str
    description: str
    preconditions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    failure_conditions: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DomainKPI:
    """A KPI definition for expert domains."""
    kpi_id: str
    metric: str
    target: Optional[float] = None
    threshold: Optional[float] = None
    importance: str = "medium"  # low, medium, high, critical
    measurement_method: str = ""
    unit: str = ""


@dataclass(frozen=True)
class ExecutionStandard:
    """Execution standards for expert domains."""
    standard_id: str
    name: str
    required_inputs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    quality_gates: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluationResult:
    """Evaluation result for expert domains."""
    domain_id: str
    execution_quality: float  # 0.0 to 1.0
    knowledge_quality: float  # 0.0 to 1.0
    evidence_coverage: float  # 0.0 to 1.0
    risk: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    completeness: float  # 0.0 to 1.0
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ReadinessScore:
    """Readiness score for expert domains."""
    domain_id: str
    knowledge_readiness: float  # 0.0 to 1.0
    execution_readiness: float  # 0.0 to 1.0
    evidence_readiness: float  # 0.0 to 1.0
    learning_readiness: float  # 0.0 to 1.0
    overall_readiness: float  # 0.0 to 1.0
    calculated_at: datetime = field(default_factory=datetime.utcnow)


class ExpertDomainContract(ABC):
    """Contract that all expert domains must implement."""

    @abstractmethod
    def get_identity(self) -> DomainIdentity:
        """Return the domain identity."""
        pass

    @abstractmethod
    def get_knowledge_areas(self) -> List[KnowledgeArea]:
        """Return the knowledge areas for this domain."""
        pass

    @abstractmethod
    def get_concepts(self) -> List[DomainConcept]:
        """Return the concepts for this domain."""
        pass

    @abstractmethod
    def get_evidence_types(self) -> List[str]:
        """Return the types of evidence this domain accepts."""
        pass

    @abstractmethod
    def get_reasoning_patterns(self) -> List[ReasoningPattern]:
        """Return the reasoning patterns for this domain."""
        pass

    @abstractmethod
    def get_decision_rules(self) -> List[DecisionRule]:
        """Return the decision rules for this domain."""
        pass

    @abstractmethod
    def get_kpis(self) -> List[DomainKPI]:
        """Return the KPIs for this domain."""
        pass

    @abstractmethod
    def get_execution_standards(self) -> List[ExecutionStandard]:
        """Return the execution standards for this domain."""
        pass

    @abstractmethod
    def evaluate(self) -> EvaluationResult:
        """Evaluate the current state of the domain."""
        pass

    @abstractmethod
    def get_readiness(self) -> ReadinessScore:
        """Return the readiness score for this domain."""
        pass

    @abstractmethod
    def get_lifecycle_stage(self) -> DomainLifecycleStage:
        """Return the current lifecycle stage."""
        pass

    @abstractmethod
    def can_advance_to_stage(self, stage: DomainLifecycleStage) -> bool:
        """Check if the domain can advance to the given lifecycle stage."""
        pass
