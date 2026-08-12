"""
ENIGMA Profile Router — TASK-017

GET  /api/enigma/profile
     View ENIGMA's operational capability profile.
     Authenticated. Returns capabilities with status, confidence, and evidence counts.
     Does NOT expose: chain-of-thought, prompts, secrets, other users' data.

GET  /api/enigma/profile/capabilities
     List all capabilities in the catalog with their profile status.

POST /api/freelancing/opportunities/assess
     Assess a freelance opportunity against the current ENIGMA profile.
     Returns structured NOT_READY / LEARN_FIRST / READY_TO_APPLY decision.

POST /api/freelancing/jobs/{job_id}/assess
     Assess an existing work_market FreelanceJob (from the existing router).
     Extends /api/freelancing/jobs/{job_id}/assessment with TASK-017 readiness.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.enigma_profile import KnowledgeProgress, EnigmaProfile, CapabilityStatus
from app.routers.auth import get_current_user
from app.engine.capability_catalog import capability_catalog
from app.freelancing.contracts import (
    ApplicationMode,
    BrainReadinessDecision,
    FreelanceOpportunity,
    OpportunityAssessment,
    ReadinessState,
)
from app.freelancing.assessment_service import OpportunityAssessmentService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["enigma_profile"])

_assessment_service = OpportunityAssessmentService()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class OpportunityAssessRequest(BaseModel):
    """
    Client-supplied opportunity for assessment.
    Client provides business data only — no worker_name, no capability override.
    """
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    platform: str = Field("unknown")
    external_id: Optional[str] = Field(None)
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    application_mode: Optional[str] = Field(None)


class CapabilityProfileEntry(BaseModel):
    name: str
    capability_id: str
    status: str
    confidence: float
    evidence_count: int
    successful_executions: int
    failed_executions: int
    execution_available: bool
    freelance_readiness_threshold: float
    meets_threshold: bool
    category: str
    module: str


class AssessmentResponse(BaseModel):
    opportunity_id: str
    overall_score: float
    readiness: str
    required_capabilities: List[Dict[str, Any]]
    missing_capabilities: List[str]
    weak_capabilities: List[str]
    unmapped_skills: List[str]
    risk_flags: List[str]
    decision: str
    blocking_capability: Optional[str]
    execution_available_for_blocking: bool
    policy_overridden: bool
    reasoning_summary: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/enigma/profile")
async def get_enigma_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get ENIGMA's current operational capability profile.

    Returns capabilities with evidence-based status and confidence.
    Safe fields only — no chain-of-thought, no prompts, no secrets.
    """
    # Load all KnowledgeProgress rows for the global enigma profile
    result = await db.execute(
        select(KnowledgeProgress).where(
            KnowledgeProgress.profile_id == "enigma_profile"
        )
    )
    rows = result.scalars().all()

    # Index by domain for fast lookup
    profile_data: Dict[str, KnowledgeProgress] = {row.domain: row for row in rows}

    # Build response from catalog entries (includes capabilities with no evidence yet)
    capabilities: List[Dict[str, Any]] = []
    for entry in capability_catalog.list_all():
        row = profile_data.get(entry.capability_id)
        confidence = float(row.confidence or 0.0) if row else 0.0
        evidence_count = int(row.evidence_count or 0) if row else 0
        success_count = int(row.successful_execution_count or 0) if row else 0
        fail_count = int(row.failed_execution_count or 0) if row else 0
        cap_status = row.capability_status if row else CapabilityStatus.UNKNOWN.value

        capabilities.append({
            "capability_id": entry.capability_id,
            "name": entry.name,
            "description": entry.description,
            "category": entry.category,
            "module": entry.module,
            "status": cap_status,
            "confidence": round(confidence, 4),
            "evidence_count": evidence_count,
            "successful_executions": success_count,
            "failed_executions": fail_count,
            "execution_available": entry.execution_available,
            "freelance_readiness_threshold": entry.freelance_readiness_threshold,
            "meets_threshold": confidence >= entry.freelance_readiness_threshold,
        })

    return {
        "profile_id": "enigma_profile",
        "capabilities": capabilities,
        "total_capabilities": len(capabilities),
        "qualified_count": sum(
            1 for c in capabilities
            if c["status"] in (CapabilityStatus.QUALIFIED.value, CapabilityStatus.PROVEN.value)
        ),
        "ready_for_freelance_count": sum(1 for c in capabilities if c["meets_threshold"]),
    }


@router.post(
    "/api/freelancing/opportunities/assess",
    response_model=AssessmentResponse,
    status_code=status.HTTP_200_OK,
)
async def assess_opportunity(
    request: OpportunityAssessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Assess a freelance opportunity against ENIGMA's current capability profile.

    The client provides business intent (title, description, skills).
    The Brain decides; policy verifies; evidence determines readiness.
    No worker_name is accepted or returned.

    Returns NOT_READY / LEARN_FIRST / READY_TO_APPLY with structured explanation.
    """
    # Resolve application mode safely
    app_mode = ApplicationMode.UNKNOWN
    if request.application_mode:
        try:
            app_mode = ApplicationMode(request.application_mode.lower())
        except ValueError:
            pass

    opportunity = FreelanceOpportunity(
        opportunity_id=str(uuid.uuid4()),
        platform=request.platform,
        external_id=request.external_id or str(uuid.uuid4()),
        title=request.title,
        description=request.description,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        currency=request.currency,
        application_mode=app_mode,
        required_skills=request.required_skills,
        preferred_skills=request.preferred_skills,
        user_id=str(current_user.id),
    )

    try:
        requirements, assessment, decision = await _assessment_service.assess(
            opportunity=opportunity,
            db=db,
        )
    except Exception as e:
        logger.error(
            "assessment_service_error",
            extra={"error_type": type(e).__name__, "user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment failed. Please try again.",
        )

    return AssessmentResponse(
        opportunity_id=assessment.opportunity_id,
        overall_score=round(assessment.overall_score, 4),
        readiness=assessment.readiness.value,
        required_capabilities=[m.to_dict() for m in assessment.capability_matches if m.required],
        missing_capabilities=assessment.missing_capabilities,
        weak_capabilities=assessment.weak_capabilities,
        unmapped_skills=assessment.unmapped_skills,
        risk_flags=assessment.risk_flags,
        decision=decision.decision.value,
        blocking_capability=decision.blocking_capability,
        execution_available_for_blocking=decision.execution_available,
        policy_overridden=decision.policy_overridden,
        reasoning_summary=assessment.reasoning_summary,
    )


@router.post(
    "/api/freelancing/jobs/{job_id}/assess",
    response_model=AssessmentResponse,
    status_code=status.HTTP_200_OK,
)
async def assess_existing_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Assess an existing FreelanceJob (from work_market) using TASK-017 readiness.

    Extends /api/freelancing/jobs/{job_id}/assessment with structured
    NOT_READY / LEARN_FIRST / READY_TO_APPLY classification.
    """
    from app.work_market.repositories import InMemoryJobRepository

    # The existing router uses an in-memory repository (global singleton)
    # Import the same instance used by the freelancing router
    from app.routers.freelancing import job_repository

    job = job_repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    opportunity = FreelanceOpportunity(
        opportunity_id=job_id,
        platform=job.source.value,
        external_id=job_id,
        title=job.title,
        description=job.description,
        budget_max=job.budget,
        currency=job.currency,
        required_skills=job.skills,
        user_id=str(current_user.id),
    )

    try:
        requirements, assessment, decision = await _assessment_service.assess(
            opportunity=opportunity,
            db=db,
        )
    except Exception as e:
        logger.error(
            "job_assessment_error",
            extra={"job_id": job_id, "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment failed. Please try again.",
        )

    return AssessmentResponse(
        opportunity_id=assessment.opportunity_id,
        overall_score=round(assessment.overall_score, 4),
        readiness=assessment.readiness.value,
        required_capabilities=[m.to_dict() for m in assessment.capability_matches if m.required],
        missing_capabilities=assessment.missing_capabilities,
        weak_capabilities=assessment.weak_capabilities,
        unmapped_skills=assessment.unmapped_skills,
        risk_flags=assessment.risk_flags,
        decision=decision.decision.value,
        blocking_capability=decision.blocking_capability,
        execution_available_for_blocking=decision.execution_available,
        policy_overridden=decision.policy_overridden,
        reasoning_summary=assessment.reasoning_summary,
    )
