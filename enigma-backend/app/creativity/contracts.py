"""
Creativity Engine Contracts

Core contracts for the Creativity & Opportunity Strategy Engine.
These contracts define the interface between creativity components
and the rest of the Enigma system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from app.marketplace.economics import (
    MarketplaceEconomicsContract,
    EconomicsValue,
    MarketplaceCost,
)
from app.marketplace.contracts import MarketplacePlatform


class ConstraintType(str, Enum):
    """Types of creative constraints."""
    NO_PORTFOLIO = "no_portfolio"
    NO_REVIEWS = "no_reviews"
    LOW_EVIDENCE = "low_evidence"
    LOW_READINESS = "low_readiness"
    HIGH_COMPETITION = "high_competition"
    LOW_BUDGET = "low_budget"
    HIGH_APPLICATION_COST = "high_application_cost"
    KNOWLEDGE_GAP = "knowledge_gap"
    STALE_KNOWLEDGE = "stale_knowledge"
    EXECUTION_GAP = "execution_gap"
    LOW_CONFIDENCE = "low_confidence"
    UNCLEAR_SCOPE = "unclear_scope"
    TIME_CONSTRAINT = "time_constraint"
    PLATFORM_CONSTRAINT = "platform_constraint"
    PRICING_CONSTRAINT = "pricing_constraint"
    WEAK_POSITIONING = "weak_positioning"
    EXPERIENCE_GAP = "experience_gap"


class ConstraintSeverity(str, Enum):
    """Severity levels for constraints."""
    BLOCKING = "blocking"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StrategyCategory(str, Enum):
    """Categories of creative strategies."""
    PRICE_ADJUSTMENT = "price_adjustment"
    SCOPE_REDUCTION = "scope_reduction"
    PROOF_OF_WORK = "proof_of_work"
    POSITIONING_CHANGE = "positioning_change"
    TARGET_SELECTION = "target_selection"
    PROPOSAL_STRATEGY = "proposal_strategy"
    RESEARCH_FIRST = "research_first"
    LEARNING_FIRST = "learning_first"
    EVIDENCE_BUILDING = "evidence_building"
    RISK_REDUCTION = "risk_reduction"
    DELIVERABLE_REDESIGN = "deliverable_redesign"
    CLARIFICATION_FIRST = "clarification_first"


class StrategyStatus(str, Enum):
    """Status of a strategy."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class CreativeConstraint:
    """
    A constraint that limits opportunity success.
    
    Constraints are immutable and describe why an opportunity
    may be difficult to execute successfully.
    """
    constraint_type: ConstraintType
    severity: ConstraintSeverity
    impact: str
    source: str
    confidence: float  # 0.0 to 1.0
    blocking: bool
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_type": self.constraint_type.value,
            "severity": self.severity.value,
            "impact": self.impact,
            "source": self.source,
            "confidence": self.confidence,
            "blocking": self.blocking,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CreativeStrategy:
    """
    A creative strategy to address constraints.
    
    Strategies are descriptive and structured recommendations
    for improving opportunity success probability.
    """
    strategy_id: str
    name: str
    description: str
    category: StrategyCategory
    target_constraints: Set[ConstraintType]
    
    required_capabilities: Set[str] = field(default_factory=set)
    optional_capabilities: Set[str] = field(default_factory=set)
    
    required_knowledge: Set[str] = field(default_factory=set)
    required_evidence: Set[str] = field(default_factory=set)
    
    economic_effect: Optional[EconomicsValue] = None
    risk_effect: Optional[EconomicsValue] = None
    confidence_effect: Optional[EconomicsValue] = None
    
    expected_benefit: float = 0.0  # 0.0 to 1.0
    implementation_complexity: float = 0.5  # 0.0 to 1.0
    reversibility: float = 0.5  # 0.0 to 1.0
    
    platform_compatibility: Set[MarketplacePlatform] = field(default_factory=set)
    domain_compatibility: Set[str] = field(default_factory=set)
    
    requires_research: bool = False
    requires_learning: bool = False
    requires_clarification: bool = False
    
    status: StrategyStatus = StrategyStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "target_constraints": [c.value for c in self.target_constraints],
            "required_capabilities": list(self.required_capabilities),
            "optional_capabilities": list(self.optional_capabilities),
            "required_knowledge": list(self.required_knowledge),
            "required_evidence": list(self.required_evidence),
            "economic_effect": self.economic_effect.to_dict() if self.economic_effect else None,
            "risk_effect": self.risk_effect.to_dict() if self.risk_effect else None,
            "confidence_effect": self.confidence_effect.to_dict() if self.confidence_effect else None,
            "expected_benefit": self.expected_benefit,
            "implementation_complexity": self.implementation_complexity,
            "reversibility": self.reversibility,
            "platform_compatibility": [p.value for p in self.platform_compatibility],
            "domain_compatibility": list(self.domain_compatibility),
            "requires_research": self.requires_research,
            "requires_learning": self.requires_learning,
            "requires_clarification": self.requires_clarification,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class StrategyEvaluation:
    """
    Evaluation of a strategy against opportunity context.
    
    Provides deterministic scoring and explanation for strategy
    recommendation or rejection.
    """
    strategy: CreativeStrategy
    benefit_score: float  # 0.0 to 1.0
    feasibility_score: float  # 0.0 to 1.0
    economic_viability_score: float  # 0.0 to 1.0
    risk_score: float  # 0.0 to 1.0 (lower is better)
    confidence_score: float  # 0.0 to 1.0
    evidence_alignment_score: float  # 0.0 to 1.0
    knowledge_alignment_score: float  # 0.0 to 1.0
    execution_fit_score: float  # 0.0 to 1.0
    reversibility_score: float  # 0.0 to 1.0
    complexity_score: float  # 0.0 to 1.0 (lower is better)
    
    overall_score: float  # 0.0 to 1.0
    
    addressed_constraints: Set[ConstraintType]
    introduced_risks: Set[str]
    
    recommendation_reason: str
    penalty_reasons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.to_dict(),
            "benefit_score": self.benefit_score,
            "feasibility_score": self.feasibility_score,
            "economic_viability_score": self.economic_viability_score,
            "risk_score": self.risk_score,
            "confidence_score": self.confidence_score,
            "evidence_alignment_score": self.evidence_alignment_score,
            "knowledge_alignment_score": self.knowledge_alignment_score,
            "execution_fit_score": self.execution_fit_score,
            "reversibility_score": self.reversibility_score,
            "complexity_score": self.complexity_score,
            "overall_score": self.overall_score,
            "addressed_constraints": [c.value for c in self.addressed_constraints],
            "introduced_risks": list(self.introduced_risks),
            "recommendation_reason": self.recommendation_reason,
            "penalty_reasons": self.penalty_reasons,
        }


@dataclass(frozen=True)
class CreativeOpportunityContext:
    """
    Normalized context for creativity reasoning.
    
    Provides creativity engine with opportunity information
    without owning the opportunity itself.
    """
    work_specification: Optional[str] = None
    profession: Optional[str] = None
    expert_domain: Optional[str] = None
    required_capabilities: Set[str] = field(default_factory=set)
    required_tasks: Set[str] = field(default_factory=set)
    
    knowledge_readiness: float = 0.5  # 0.0 to 1.0
    execution_readiness: float = 0.5  # 0.0 to 1.0
    evidence_readiness: float = 0.5  # 0.0 to 1.0
    proposal_readiness: float = 0.5  # 0.0 to 1.0
    platform_readiness: float = 0.5  # 0.0 to 1.0
    
    risk_score: float = 0.5  # 0.0 to 1.0
    confidence_score: float = 0.5  # 0.0 to 1.0
    
    competition_level: float = 0.5  # 0.0 to 1.0
    
    budget: Optional[float] = None
    estimated_revenue: Optional[float] = None
    application_cost: Optional[float] = None
    expected_value: Optional[float] = None
    
    portfolio_strength: float = 0.5  # 0.0 to 1.0
    review_strength: float = 0.5  # 0.0 to 1.0
    experience_strength: float = 0.5  # 0.0 to 1.0
    
    knowledge_freshness: float = 0.5  # 0.0 to 1.0
    
    platform_economics: Optional[MarketplaceEconomicsContract] = None
    
    constraints: List[CreativeConstraint] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_specification": self.work_specification,
            "profession": self.profession,
            "expert_domain": self.expert_domain,
            "required_capabilities": list(self.required_capabilities),
            "required_tasks": list(self.required_tasks),
            "knowledge_readiness": self.knowledge_readiness,
            "execution_readiness": self.execution_readiness,
            "evidence_readiness": self.evidence_readiness,
            "proposal_readiness": self.proposal_readiness,
            "platform_readiness": self.platform_readiness,
            "risk_score": self.risk_score,
            "confidence_score": self.confidence_score,
            "competition_level": self.competition_level,
            "budget": self.budget,
            "estimated_revenue": self.estimated_revenue,
            "application_cost": self.application_cost,
            "expected_value": self.expected_value,
            "portfolio_strength": self.portfolio_strength,
            "review_strength": self.review_strength,
            "experience_strength": self.experience_strength,
            "knowledge_freshness": self.knowledge_freshness,
            "platform_economics": self.platform_economics.to_dict() if self.platform_economics else None,
            "constraints": [c.to_dict() for c in self.constraints],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CreativityResult:
    """
    Result of creativity engine processing.
    
    Contains candidate strategies, rankings, and recommendations
    for the Decision Engine to consume.
    """
    opportunity_context: CreativeOpportunityContext
    candidate_strategies: List[CreativeStrategy]
    ranked_strategies: List[StrategyEvaluation]
    
    constraints: List[CreativeConstraint]
    unresolved_constraints: List[CreativeConstraint]
    
    research_required: bool
    learning_required: bool
    clarification_required: bool
    
    confidence: float  # 0.0 to 1.0
    explanation: str
    
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_context": self.opportunity_context.to_dict(),
            "candidate_strategies": [s.to_dict() for s in self.candidate_strategies],
            "ranked_strategies": [e.to_dict() for e in self.ranked_strategies],
            "constraints": [c.to_dict() for c in self.constraints],
            "unresolved_constraints": [c.to_dict() for c in self.unresolved_constraints],
            "research_required": self.research_required,
            "learning_required": self.learning_required,
            "clarification_required": self.clarification_required,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "generated_at": self.generated_at,
        }


@dataclass
class CreativityEngineContract:
    """
    Contract for creativity engine implementations.
    
    Defines the interface that all creativity providers must implement,
    allowing for both rule-based and future AI-based implementations.
    """
    engine_id: str
    name: str
    description: str
    version: str
    
    def generate_strategies(
        self,
        context: CreativeOpportunityContext,
    ) -> CreativityResult:
        """
        Generate creative strategies for the given context.
        
        Args:
            context: Opportunity context for reasoning
            
        Returns:
            CreativityResult with candidate and ranked strategies
        """
        raise NotImplementedError
