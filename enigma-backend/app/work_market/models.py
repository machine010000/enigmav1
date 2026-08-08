from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JobSource(str, Enum):
    """Marketplace sources without coupling to specific platforms."""
    UPWORK = "upwork"
    FIVERR = "fiverr"
    FREELANCER = "freelancer"
    KHAMASAT = "khamsat"
    MOSTAQL = "mostaql"
    OTHER = "other"


class JobRecommendation(str, Enum):
    """Job evaluation recommendation."""
    APPLY = "apply"
    LEARN_FIRST = "learn_first"
    RESEARCH_FIRST = "research_first"
    REJECT = "reject"


class WorkType(str, Enum):
    """Type of work context."""
    INTERNAL = "internal"
    CLIENT = "client"
    FREELANCE = "freelance"
    MARKETING = "marketing"
    RESEARCH = "research"
    LEARNING = "learning"


class PlatformConnectionStatus(str, Enum):
    """Platform connection status."""
    CONNECTED = "connected"
    NOT_CONNECTED = "not_connected"
    REQUIRES_SETUP = "requires_setup"
    UNAVAILABLE = "unavailable"
    AUTHENTICATION_FAILED = "authentication_failed"


class ApplicationStatus(str, Enum):
    """Application state machine."""
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    LEARNING = "learning"
    READY = "ready"
    DRAFTED = "drafted"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    RESPONDED = "responded"
    WON = "won"
    LOST = "lost"
    WITHDRAWN = "withdrawn"


class PlatformType(str, Enum):
    """Platform type classification."""
    PROPOSAL_BASED = "proposal_based"
    BID_BASED = "bid_based"
    GIG_BASED = "gig_based"
    CONTEST_BASED = "contest_based"


@dataclass(frozen=True)
class FreelanceJob:
    """Immutable domain contract for a freelance job from any marketplace."""
    job_id: str
    source: JobSource
    title: str
    description: str
    client_information: Dict[str, Any] = field(default_factory=dict)
    budget: Optional[float] = None
    currency: str = "USD"
    deadline: Optional[datetime] = None
    skills: List[str] = field(default_factory=list)
    source_url: str = ""
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    normalized_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source": self.source.value,
            "title": self.title,
            "description": self.description,
            "client_information": self.client_information,
            "budget": self.budget,
            "currency": self.currency,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "skills": self.skills,
            "source_url": self.source_url,
            "discovered_at": self.discovered_at.isoformat(),
            "normalized_at": self.normalized_at.isoformat() if self.normalized_at else None,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class JobClassification:
    """Classification of a job into profession, task, and requirements."""
    job_id: str
    profession: str
    task: str
    required_skills: List[str] = field(default_factory=list)
    required_knowledge: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    expected_deliverables: List[str] = field(default_factory=list)
    expected_kpis: List[str] = field(default_factory=list)
    complexity: str = "medium"  # low, medium, high
    estimated_effort: str = "medium"  # low, medium, high
    confidence: float = 0.0
    classified_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "profession": self.profession,
            "task": self.task,
            "required_skills": self.required_skills,
            "required_knowledge": self.required_knowledge,
            "required_capabilities": self.required_capabilities,
            "expected_deliverables": self.expected_deliverables,
            "expected_kpis": self.expected_kpis,
            "complexity": self.complexity,
            "estimated_effort": self.estimated_effort,
            "confidence": self.confidence,
            "classified_at": self.classified_at.isoformat(),
        }


@dataclass(frozen=True)
class JobEvaluation:
    """Evaluation of a job's suitability and requirements."""
    job_id: str
    profession_match: float = 0.0
    skill_match: float = 0.0
    knowledge_match: float = 0.0
    capability_match: float = 0.0
    complexity_score: float = 0.0
    effort_score: float = 0.0
    earning_score: float = 0.0
    success_probability: float = 0.0
    risk_score: float = 0.0
    confidence: float = 0.0
    missing_knowledge: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    missing_capabilities: List[str] = field(default_factory=list)
    recommendation: JobRecommendation = JobRecommendation.REJECT
    reason: str = ""
    evaluated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "profession_match": self.profession_match,
            "skill_match": self.skill_match,
            "knowledge_match": self.knowledge_match,
            "capability_match": self.capability_match,
            "complexity_score": self.complexity_score,
            "effort_score": self.effort_score,
            "earning_score": self.earning_score,
            "success_probability": self.success_probability,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "missing_knowledge": self.missing_knowledge,
            "missing_skills": self.missing_skills,
            "missing_capabilities": self.missing_capabilities,
            "recommendation": self.recommendation.value,
            "reason": self.reason,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


@dataclass(frozen=True)
class LearningRequirement:
    """Structured learning requirement derived from job evaluation."""
    job_id: str
    missing_knowledge: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    missing_capabilities: List[str] = field(default_factory=list)
    research_tasks: List[str] = field(default_factory=list)
    academy_modules: List[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high
    estimated_learning_effort: str = "medium"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "missing_knowledge": self.missing_knowledge,
            "missing_skills": self.missing_skills,
            "missing_capabilities": self.missing_capabilities,
            "research_tasks": self.research_tasks,
            "academy_modules": self.academy_modules,
            "priority": self.priority,
            "estimated_learning_effort": self.estimated_learning_effort,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ApplicationDraft:
    """Prepared application draft without submission."""
    job_id: str
    profession: str
    understanding_of_task: str
    proposed_approach: str
    relevant_capabilities: List[str] = field(default_factory=list)
    relevant_experience: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    estimated_timeline: str = ""
    questions_for_client: List[str] = field(default_factory=list)
    confidence: float = 0.0
    risks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "profession": self.profession,
            "understanding_of_task": self.understanding_of_task,
            "proposed_approach": self.proposed_approach,
            "relevant_capabilities": self.relevant_capabilities,
            "relevant_experience": self.relevant_experience,
            "deliverables": self.deliverables,
            "estimated_timeline": self.estimated_timeline,
            "questions_for_client": self.questions_for_client,
            "confidence": self.confidence,
            "risks": self.risks,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class WorkContext:
    """Context for work type (internal vs external)."""
    work_type: WorkType
    client: Optional[str] = None
    profession: Optional[str] = None
    task: Optional[str] = None
    goal: str = ""
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    deliverables: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_type": self.work_type.value,
            "client": self.client,
            "profession": self.profession,
            "task": self.task,
            "goal": self.goal,
            "budget": self.budget,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "deliverables": self.deliverables,
            "success_metrics": self.success_metrics,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class Platform:
    """Platform registry contract for freelance marketplaces."""
    platform_id: str
    name: str
    type: PlatformType
    connection_status: PlatformConnectionStatus = PlatformConnectionStatus.NOT_CONNECTED
    auth_status: str = "not_authenticated"
    profile_status: str = "not_set_up"
    application_model: str = ""
    capabilities: List[str] = field(default_factory=list)
    application_requirements: Dict[str, Any] = field(default_factory=dict)
    credits_available: Optional[int] = None
    availability: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    # Enhanced fields for policies and rules
    proposal_rules: Dict[str, Any] = field(default_factory=dict)
    pricing_rules: Dict[str, Any] = field(default_factory=dict)
    connection_requirements: Dict[str, Any] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform_id": self.platform_id,
            "name": self.name,
            "type": self.type.value,
            "connection_status": self.connection_status.value,
            "auth_status": self.auth_status,
            "profile_status": self.profile_status,
            "application_model": self.application_model,
            "capabilities": self.capabilities,
            "application_requirements": self.application_requirements,
            "credits_available": self.credits_available,
            "availability": self.availability,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "proposal_rules": self.proposal_rules,
            "pricing_rules": self.pricing_rules,
            "connection_requirements": self.connection_requirements,
            "limits": self.limits,
        }


@dataclass(frozen=True)
class JobAssessment:
    """Enigma's assessment of a job's suitability."""
    job_id: str
    profession_match: float = 0.0
    capability_match: float = 0.0
    knowledge_readiness: float = 0.0
    evidence_readiness: float = 0.0
    execution_readiness: float = 0.0
    overall_readiness: float = 0.0
    blockers: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    missing_knowledge: List[str] = field(default_factory=list)
    missing_capabilities: List[str] = field(default_factory=list)
    recommendation: JobRecommendation = JobRecommendation.REJECT
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "profession_match": self.profession_match,
            "capability_match": self.capability_match,
            "knowledge_readiness": self.knowledge_readiness,
            "evidence_readiness": self.evidence_readiness,
            "execution_readiness": self.execution_readiness,
            "overall_readiness": self.overall_readiness,
            "blockers": self.blockers,
            "risks": self.risks,
            "missing_knowledge": self.missing_knowledge,
            "missing_capabilities": self.missing_capabilities,
            "recommendation": self.recommendation.value,
            "assessed_at": self.assessed_at.isoformat(),
        }


@dataclass(frozen=True)
class Application:
    """Application state machine contract."""
    application_id: str
    job_id: str
    platform: str
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    draft_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    blockers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "job_id": self.job_id,
            "platform": self.platform,
            "status": self.status.value,
            "draft_id": self.draft_id,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "blockers": self.blockers,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class ActiveWork:
    """Active work lifecycle contract."""
    work_id: str
    application_id: str
    job_title: str
    platform: str
    state: str = "accepted"
    started_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    deliverables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "application_id": self.application_id,
            "job_title": self.job_title,
            "platform": self.platform,
            "state": self.state,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "deliverables": self.deliverables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
