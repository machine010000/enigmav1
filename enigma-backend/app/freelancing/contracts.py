"""
TASK-017 Freelancing Intelligence Contracts

Defines the canonical contracts for:
  - FreelanceOpportunity  (normalised opportunity across platforms)
  - OpportunityRequirements (extracted structured requirements)
  - CapabilityMatch         (per-capability match result)
  - OpportunityAssessment   (full assessment with readiness decision)
  - ReadinessState          (NOT_READY / LEARN_FIRST / READY_TO_APPLY)
  - BrainReadinessDecision  (Brain's final decision after policy check)

Design rules:
  - Readiness state is computed from evidence, not from LLM assertion.
  - BrainReadinessDecision carries the policy-verified state.
  - Unknown/hallucinated capabilities stay UNMAPPED; they never become
    executable capabilities.
  - No worker_name is exposed to clients.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ApplicationMode(str, Enum):
    """How applications are submitted on this platform."""
    PROPOSAL = "proposal"        # Upwork-style
    BID = "bid"                  # Freelancer/Mostaql-style
    GIG_MATCH = "gig_match"      # Fiverr-style inbound order
    DIRECT_INVITE = "direct_invite"
    UNKNOWN = "unknown"


class ReadinessState(str, Enum):
    """
    TASK-017: Canonical opportunity readiness classification.

    NOT_READY       — critical required capability is missing or unknown.
    LEARN_FIRST     — capability exists in catalog but confidence is below threshold.
    READY_TO_APPLY  — all required capabilities meet or exceed their thresholds.
    HIGH_CONFIDENCE — READY_TO_APPLY with overall score >= 0.85.

    READY_TO_APPLY does NOT mean an application was submitted.
    It means the system has sufficient evidence to proceed to the future
    application workflow.
    """
    NOT_READY = "not_ready"
    LEARN_FIRST = "learn_first"
    READY_TO_APPLY = "ready_to_apply"
    HIGH_CONFIDENCE = "high_confidence"


class BrainDecisionType(str, Enum):
    """Final Brain decision after policy check."""
    SKIP_OPPORTUNITY = "skip_opportunity"
    LEARN_CAPABILITY = "learn_capability"
    PRACTICE_CAPABILITY = "practice_capability"
    RESEARCH_MORE = "research_more"
    READY_TO_APPLY = "ready_to_apply"


@dataclass
class FreelanceOpportunity:
    """
    Normalised internal representation of a freelance opportunity.

    Platform-specific data is abstracted away.  Downstream logic only
    operates on this normalised contract.
    """
    opportunity_id: str
    platform: str                       # platform name string (upwork, fiverr, etc.)
    external_id: str                    # platform-specific job/gig ID
    title: str
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    currency: str = "USD"
    application_mode: ApplicationMode = ApplicationMode.UNKNOWN
    required_skills: List[str] = field(default_factory=list)   # raw skill tags from platform
    preferred_skills: List[str] = field(default_factory=list)
    category: Optional[str] = None
    client_metadata: Dict[str, Any] = field(default_factory=dict)  # public client info only
    source_url: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None  # the user who discovered/imported this opportunity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "platform": self.platform,
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description[:500],  # truncate for safety
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "currency": self.currency,
            "application_mode": self.application_mode.value,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "category": self.category,
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class OpportunityRequirements:
    """
    Structured requirements extracted from a FreelanceOpportunity.

    required_capabilities   — resolved against CapabilityCatalog; unknown → UNMAPPED
    optional_capabilities   — nice-to-have capabilities
    unmapped_skills         — raw skills that could not be mapped to catalog entries
    estimated_complexity    — low / medium / high
    deliverables            — plain-text list
    constraints             — budget, timeline, etc.
    risk_flags              — anything unusual detected in description
    confidence_in_analysis  — 0–1, how confident the extractor is
    """
    opportunity_id: str
    required_capabilities: List[str] = field(default_factory=list)
    optional_capabilities: List[str] = field(default_factory=list)
    unmapped_skills: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"
    deliverables: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    confidence_in_analysis: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "required_capabilities": self.required_capabilities,
            "optional_capabilities": self.optional_capabilities,
            "unmapped_skills": self.unmapped_skills,
            "estimated_complexity": self.estimated_complexity,
            "deliverables": self.deliverables,
            "constraints": self.constraints,
            "risk_flags": self.risk_flags,
            "confidence_in_analysis": self.confidence_in_analysis,
        }


@dataclass
class CapabilityMatch:
    """Per-capability match result in an opportunity assessment."""
    capability: str
    required: bool
    # Catalog entry found
    in_catalog: bool = False
    # Worker currently registered
    execution_available: bool = False
    # Values from the live profile
    profile_status: str = "unknown"
    confidence: float = 0.0
    evidence_count: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    # Threshold from catalog
    minimum_required_confidence: float = 0.65
    # Gap: True if this capability is a blocker
    gap: bool = True
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "required": self.required,
            "in_catalog": self.in_catalog,
            "execution_available": self.execution_available,
            "profile_status": self.profile_status,
            "confidence": round(self.confidence, 4),
            "evidence_count": self.evidence_count,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "minimum_required_confidence": self.minimum_required_confidence,
            "gap": self.gap,
            "reason": self.reason,
        }


@dataclass
class OpportunityAssessment:
    """
    Full opportunity assessment result.

    overall_score is computed from capability matches — never from a single
    LLM-generated number.
    readiness follows ReadinessState — policy-verified, not LLM-asserted.
    """
    opportunity_id: str
    overall_score: float
    readiness: ReadinessState
    capability_matches: List[CapabilityMatch] = field(default_factory=list)
    missing_capabilities: List[str] = field(default_factory=list)
    weak_capabilities: List[str] = field(default_factory=list)
    unmapped_skills: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    reasoning_summary: str = ""
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "overall_score": round(self.overall_score, 4),
            "readiness": self.readiness.value,
            "capability_matches": [m.to_dict() for m in self.capability_matches],
            "missing_capabilities": self.missing_capabilities,
            "weak_capabilities": self.weak_capabilities,
            "unmapped_skills": self.unmapped_skills,
            "risk_flags": self.risk_flags,
            "reasoning_summary": self.reasoning_summary,
            "assessed_at": self.assessed_at.isoformat(),
        }


@dataclass
class BrainReadinessDecision:
    """
    The Brain's final decision after policy/evidence verification.

    The Brain proposes; policy/evidence determines whether the proposal
    is permitted.  This contract records both the Brain's proposal and
    the policy-validated final decision.

    brain_proposed       — what the Brain initially suggested
    policy_overridden    — True if policy blocked the Brain's proposal
    decision             — the authoritative final decision
    blocking_capability  — the weakest blocking capability (for LEARN_FIRST)
    execution_available  — whether a worker exists for blocking_capability
    reasoning            — human-readable explanation (no chain-of-thought)
    """
    decision: BrainDecisionType
    brain_proposed: BrainDecisionType
    policy_overridden: bool = False
    blocking_capability: Optional[str] = None
    execution_available: bool = False
    overall_score: float = 0.0
    readiness: ReadinessState = ReadinessState.NOT_READY
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "brain_proposed": self.brain_proposed.value,
            "policy_overridden": self.policy_overridden,
            "blocking_capability": self.blocking_capability,
            "execution_available": self.execution_available,
            "overall_score": round(self.overall_score, 4),
            "readiness": self.readiness.value,
            "reasoning": self.reasoning,
        }
