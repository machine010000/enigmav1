"""
Pipeline Context

Domain-agnostic pipeline context that carries the output of every stage.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.economics import (
    MarketplaceEconomicsContract,
    EconomicAssessment,
    EconomicDecision,
)
from app.marketplace.account_state import MarketplaceAccountState
from app.marketplace.account_economics import EconomicSafetyResult, EconomicMetrics
from app.creativity.contracts import (
    CreativeOpportunityContext,
    CreativityResult,
    CreativeConstraint,
)
from app.time_intelligence.contracts import (
    TimezoneInfo,
    CustomerTimeContext,
    DeadlineAnalysis,
    WorkingHourOverlap,
)
from app.enigma_profile.contracts import EnigmaProfile


class PipelineStage(str, Enum):
    """Pipeline stages in execution order."""
    JOB_RECEIVED = "job_received"
    CLASSIFICATION = "classification"
    WORK_SPECIFICATION = "work_specification"
    ECONOMICS_ASSESSMENT = "economics_assessment"
    KNOWLEDGE_READINESS = "knowledge_readiness"
    EVIDENCE_READINESS = "evidence_readiness"
    CREATIVITY_ENGINE = "creativity_engine"
    DECISION_EVALUATION = "decision_evaluation"
    DECISION_GATE = "decision_gate"
    EXECUTION_READINESS = "execution_readiness"
    EXECUTION_PLANNING = "execution_planning"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    """Overall pipeline status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class PipelineContext:
    """
    Canonical pipeline context carrying outputs of all stages.
    
    Reuses existing contracts wherever possible to avoid duplication.
    """
    # Input
    job_id: str
    job_data: Dict[str, Any] = field(default_factory=dict)
    
    # Stage: Classification
    classification: Optional[str] = None
    profession: Optional[str] = None
    expert_domain: Optional[str] = None
    
    # Stage: Work Specification
    work_specification: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    required_tasks: List[str] = field(default_factory=list)
    
    # Stage: Marketplace Intelligence
    platform: Optional[MarketplacePlatform] = None
    platform_job_id: Optional[str] = None
    
    # Stage: Economics Assessment
    economics_contract: Optional[MarketplaceEconomicsContract] = None
    economic_assessment: Optional[EconomicAssessment] = None
    economic_decision: Optional[EconomicDecision] = None
    economic_blocking_reason: Optional[str] = None
    
    # Stage: Account State (TASK-048)
    account_state: Optional[MarketplaceAccountState] = None
    economic_safety_result: Optional[EconomicSafetyResult] = None
    economic_metrics: Optional[EconomicMetrics] = None
    
    # Stage: Time Intelligence (TASK-049)
    customer_timezone: Optional[TimezoneInfo] = None
    customer_time_context: Optional[CustomerTimeContext] = None
    deadline_analysis: Optional[DeadlineAnalysis] = None
    working_hour_overlap: Optional[WorkingHourOverlap] = None
    
    # Stage: Enigma Profile (TASK-049)
    enigma_profile: Optional[EnigmaProfile] = None
    
    # Stage: Knowledge Readiness
    knowledge_readiness: float = 0.5  # 0.0 to 1.0
    knowledge_freshness: float = 0.5  # 0.0 to 1.0
    knowledge_gaps: List[str] = field(default_factory=list)
    knowledge_blocking_reason: Optional[str] = None
    
    # Stage: Evidence Readiness
    evidence_readiness: float = 0.5  # 0.0 to 1.0
    portfolio_strength: float = 0.5  # 0.0 to 1.0
    review_strength: float = 0.5  # 0.0 to 1.0
    experience_strength: float = 0.5  # 0.0 to 1.0
    evidence_gaps: List[str] = field(default_factory=list)
    evidence_blocking_reason: Optional[str] = None
    
    # Stage: Creativity Engine
    creativity_context: Optional[CreativeOpportunityContext] = None
    creativity_result: Optional[CreativityResult] = None
    creativity_constraints: List[CreativeConstraint] = field(default_factory=list)
    
    # Stage: Decision Evaluation
    decision: Optional[str] = None  # ACCEPT, REJECT, NEED_*, etc.
    decision_reason: Optional[str] = None
    decision_conditions: List[str] = field(default_factory=list)
    
    # Stage: Execution Readiness
    execution_readiness: float = 0.5  # 0.0 to 1.0
    risk_score: float = 0.5  # 0.0 to 1.0
    scope_clarity: float = 0.5  # 0.0 to 1.0
    execution_blocking_reason: Optional[str] = None
    
    # Stage: Execution Planning
    execution_plan: Optional[Dict[str, Any]] = None
    
    # Pipeline State
    current_stage: PipelineStage = PipelineStage.JOB_RECEIVED
    status: PipelineStatus = PipelineStatus.PENDING
    blocking_stage: Optional[PipelineStage] = None
    blocking_reason: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def can_proceed_to_execution(self) -> bool:
        """
        Check if pipeline can proceed to execution.
        
        Returns:
            True if all gates pass, False otherwise
        """
        # Decision must be ACCEPT or ACCEPT_WITH_CONDITIONS
        if self.decision not in ["ACCEPT", "ACCEPT_WITH_CONDITIONS"]:
            return False
        
        # Economics must not be blocking
        if self.economic_blocking_reason:
            return False
        
        # Knowledge must not be blocking
        if self.knowledge_blocking_reason:
            return False
        
        # Evidence must not be blocking
        if self.evidence_blocking_reason:
            return False
        
        # Execution must not be blocking
        if self.execution_blocking_reason:
            return False
        
        return True
    
    def is_blocked(self) -> bool:
        """Check if pipeline is blocked."""
        return self.status == PipelineStatus.BLOCKED
    
    def is_failed(self) -> bool:
        """Check if pipeline has failed."""
        return self.status == PipelineStatus.FAILED
    
    def is_completed(self) -> bool:
        """Check if pipeline is completed."""
        return self.status == PipelineStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "job_id": self.job_id,
            "classification": self.classification,
            "profession": self.profession,
            "expert_domain": self.expert_domain,
            "work_specification": self.work_specification,
            "required_capabilities": self.required_capabilities,
            "required_tasks": self.required_tasks,
            "platform": self.platform.value if self.platform else None,
            "platform_job_id": self.platform_job_id,
            "economic_decision": self.economic_decision.value if self.economic_decision else None,
            "economic_blocking_reason": self.economic_blocking_reason,
            "knowledge_readiness": self.knowledge_readiness,
            "knowledge_freshness": self.knowledge_freshness,
            "knowledge_gaps": self.knowledge_gaps,
            "knowledge_blocking_reason": self.knowledge_blocking_reason,
            "evidence_readiness": self.evidence_readiness,
            "portfolio_strength": self.portfolio_strength,
            "review_strength": self.review_strength,
            "experience_strength": self.experience_strength,
            "evidence_gaps": self.evidence_gaps,
            "evidence_blocking_reason": self.evidence_blocking_reason,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "decision_conditions": self.decision_conditions,
            "execution_readiness": self.execution_readiness,
            "risk_score": self.risk_score,
            "scope_clarity": self.scope_clarity,
            "execution_blocking_reason": self.execution_blocking_reason,
            "current_stage": self.current_stage.value,
            "status": self.status.value,
            "blocking_stage": self.blocking_stage.value if self.blocking_stage else None,
            "blocking_reason": self.blocking_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
