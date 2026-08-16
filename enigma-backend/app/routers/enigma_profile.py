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
from app.freelancing.development_bridge import (
    DevelopmentPlanError,
    OpportunityDevelopmentBridge,
    StaleDevelopmentPlanError,
)
from app.freelancing.controlled_application_package import (
    ClaimGroundingError,
    ControlledApplicationPackageService,
    OwnershipError,
    PackageNotFoundError,
    ReadinessGateError,
    ReviewStateError,
    StaleReadinessError,
)
from app.core.logging_config import get_logger
from app.learning.revalidation_service import (
    CapabilityFreshnessView,
    CapabilityNotFoundError,
    CapabilityNotProvenError,
    CapabilityRevalidationService,
    RevalidationPersistenceError,
    RevalidationResponseData,
)

logger = get_logger(__name__)

router = APIRouter(tags=["enigma_profile"])

_assessment_service = OpportunityAssessmentService()
_development_bridge = OpportunityDevelopmentBridge()
_revalidation_service = CapabilityRevalidationService()
_application_package_service = ControlledApplicationPackageService()


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
    revalidation_available: bool = False


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


class DevelopmentPlanRequest(OpportunityAssessRequest):
    opportunity_id: str = Field(..., min_length=1, max_length=200)
    target_id: Optional[str] = None


class DevelopmentPlanExecutionRequest(DevelopmentPlanRequest):
    plan_id: str = Field(..., min_length=1, max_length=100)


class CapabilityFreshnessResponse(BaseModel):
    capability: str
    status: str
    freshness: str
    last_success_at: Optional[str]
    last_verified: Optional[str]
    revalidation_interval_days: int
    stale_horizon_days: int
    advanced_diversity: int
    required_diversity: int
    revalidation_required: bool


class CapabilityRevalidationResponse(BaseModel):
    capability: str
    status_before: str
    freshness_before: str
    action: str
    attempts_run: int
    success: bool
    evaluation_score: Optional[float]
    status_after: str
    freshness_after: str
    confidence: float
    evidence_count: int
    stop_reason: Optional[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/api/enigma/profile/capabilities/{capability_id}/freshness",
    response_model=CapabilityFreshnessResponse,
)
async def get_capability_freshness(
    capability_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CapabilityFreshnessResponse:
    try:
        view = await _revalidation_service.get_freshness(
            db, str(current_user.id), capability_id
        )
        return CapabilityFreshnessResponse(**view.to_dict())
    except CapabilityNotFoundError:
        raise HTTPException(status_code=404, detail="Capability not found")
    except Exception:
        logger.exception("capability_freshness_failed", extra={"capability": capability_id})
        raise HTTPException(status_code=500, detail="Unable to assess capability freshness")


@router.post(
    "/api/enigma/profile/capabilities/{capability_id}/revalidate",
    response_model=CapabilityRevalidationResponse,
)
async def request_capability_revalidation(
    capability_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CapabilityRevalidationResponse:
    try:
        result = await _revalidation_service.request_revalidation(
            db, str(current_user.id), capability_id
        )
        return CapabilityRevalidationResponse(**result.to_dict())
    except CapabilityNotFoundError:
        raise HTTPException(status_code=404, detail="Capability not found")
    except CapabilityNotProvenError:
        raise HTTPException(status_code=409, detail="Capability is not proven")
    except RevalidationPersistenceError:
        raise HTTPException(status_code=500, detail="Revalidation could not be completed")
    except Exception:
        logger.exception("capability_revalidation_failed", extra={"capability": capability_id})
        raise HTTPException(status_code=500, detail="Revalidation could not be completed")

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
    try:
        result = await db.execute(
            select(KnowledgeProgress).where(
                KnowledgeProgress.profile_id == "enigma_profile"
            )
        )
        rows = result.scalars().all()
        # Index by domain for fast lookup
        profile_data: Dict[str, KnowledgeProgress] = {row.domain: row for row in rows}
    except Exception:
        # DB schema may not yet have TASK-017 columns (pre-migration) — graceful degradation
        profile_data = {}

    # Build response from catalog entries (includes capabilities with no evidence yet)
    capabilities: List[Dict[str, Any]] = []
    for entry in capability_catalog.list_all():
        row = profile_data.get(entry.capability_id)
        confidence = float(row.confidence or 0.0) if row else 0.0
        evidence_count = int(getattr(row, 'evidence_count', None) or 0) if row else 0
        success_count = int(getattr(row, 'successful_execution_count', None) or 0) if row else 0
        fail_count = int(getattr(row, 'failed_execution_count', None) or 0) if row else 0
        cap_status = getattr(row, 'capability_status', None) or CapabilityStatus.UNKNOWN.value if row else CapabilityStatus.UNKNOWN.value

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
            "revalidation_available": entry.revalidation_interval_days is not None,
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


def _development_opportunity(
    request: DevelopmentPlanRequest, user_id: str
) -> FreelanceOpportunity:
    app_mode = ApplicationMode.UNKNOWN
    if request.application_mode:
        try:
            app_mode = ApplicationMode(request.application_mode.lower())
        except ValueError:
            pass
    return FreelanceOpportunity(
        opportunity_id=request.opportunity_id,
        platform=request.platform,
        external_id=request.external_id or request.opportunity_id,
        title=request.title,
        description=request.description,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        currency=request.currency,
        application_mode=app_mode,
        required_skills=request.required_skills,
        preferred_skills=request.preferred_skills,
        user_id=user_id,
    )


@router.post("/api/freelancing/opportunities/development-plan")
async def generate_opportunity_development_plan(
    request: DevelopmentPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Reassess authoritatively and return non-executing development actions."""
    opportunity = _development_opportunity(request, str(current_user.id))
    _, assessment, decision = await _assessment_service.assess(opportunity, db)
    try:
        plans = await _development_bridge.generate(
            assessment=assessment, decision=decision, db=db,
            user_id=str(current_user.id), target_id=request.target_id,
        )
    except DevelopmentPlanError:
        raise HTTPException(status_code=404, detail="Owned target not found")
    return {
        "opportunity_id": opportunity.opportunity_id,
        "assessment_readiness": assessment.readiness.value,
        "decision": decision.decision.value,
        "development_actions": [plan.to_dict() for plan in plans],
    }


@router.post("/api/freelancing/opportunities/development-plan/execute")
async def execute_opportunity_development_plan(
    request: DevelopmentPlanExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Explicitly execute one server-regenerated, policy-valid development action."""
    opportunity = _development_opportunity(request, str(current_user.id))
    _, assessment, decision = await _assessment_service.assess(opportunity, db)
    try:
        plans = await _development_bridge.generate(
            assessment=assessment, decision=decision, db=db,
            user_id=str(current_user.id), target_id=request.target_id,
        )
        plan = next((item for item in plans if item.plan_id == request.plan_id), None)
        if plan is None:
            raise StaleDevelopmentPlanError("plan is invalid or stale")
        result = await _development_bridge.execute(
            plan, db=db, user_id=str(current_user.id)
        )
    except StaleDevelopmentPlanError:
        raise HTTPException(status_code=409, detail="Development plan is stale")
    except DevelopmentPlanError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "plan_id": plan.plan_id,
        "capability_id": plan.capability_id,
        "training_mode": plan.recommended_training_mode,
        "action": result.action,
        "execution_id": result.execution_id,
        "attempts_run": result.attempts_run,
        "evaluation": result.evaluation.to_dict() if result.evaluation else None,
        "capability_status": result.capability_status,
        "reason": result.reason,
    }


# ---------------------------------------------------------------------------
# Application Package
# ---------------------------------------------------------------------------

class ApplicationPackageRequest(OpportunityAssessRequest):
    """
    Request to build a controlled application package.

    opportunity_id  — caller-supplied ID for idempotency tracking (optional)
    target_id       — authenticated-user-owned product ID (optional but preferred)
    """
    opportunity_id: Optional[str] = Field(None, max_length=200)
    target_id: Optional[str] = Field(None, max_length=100)


@router.post(
    "/api/freelancing/opportunities/application-package",
    status_code=status.HTTP_200_OK,
)
async def build_application_package(
    request: ApplicationPackageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Build a controlled evidence-backed application package for a ready_to_apply
    opportunity.

    The server ALWAYS re-evaluates readiness server-side before building.
    A client-supplied "ready_to_apply" value is never trusted — the current
    profile state is the authoritative source.

    Returns the package in READY_FOR_HUMAN_APPROVAL state.
    Does NOT automatically submit, send, or apply to any platform.
    Does NOT mutate learning or capability evidence.
    Stops at the human approval boundary.
    """
    try:
        package = await _application_package_service.build(
            user=current_user,
            opportunity_title=request.title,
            opportunity_description=request.description,
            platform=request.platform,
            required_skills=request.required_skills,
            opportunity_id=request.opportunity_id,
            target_id=request.target_id,
            db=db,
        )
    except ReadinessGateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "opportunity_not_ready",
                "message": str(exc),
                "decision": exc.decision,
                "blocking_capability": exc.blocking_capability,
            },
        )
    except OwnershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ownership_violation",
                "message": str(exc),
            },
        )
    except ClaimGroundingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "claim_grounding_failed",
                "message": str(exc),
            },
        )
    except Exception as exc:
        logger.exception(
            "application_package_build_failed",
            extra={"user_id": str(current_user.id), "error_type": type(exc).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application package build failed. Please try again.",
        )

    return package.to_dict()


# ---------------------------------------------------------------------------
# Application Package — read + review (TASK-051)
# ---------------------------------------------------------------------------

class PackageReviewRequest(BaseModel):
    """Human review decision for a controlled application package."""
    decision: str = Field(
        ...,
        description="'approve' or 'reject'",
        pattern=r"^(approve|reject)$",
    )
    note: Optional[str] = Field(None, max_length=2000)
    # Optional opportunity context for stale re-check on approve.
    # If omitted the server uses the persisted opportunity_title/platform.
    opportunity_description: Optional[str] = Field(None, max_length=5000)
    required_skills: Optional[List[str]] = Field(None)


@router.get(
    "/api/freelancing/application-packages/{application_id}",
    status_code=status.HTTP_200_OK,
)
async def get_application_package(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve a controlled application package by ID.

    Only the package owner can retrieve it.  Returns 404 for non-existent
    or other-user packages (non-disclosure policy).
    """
    try:
        package = await _application_package_service.get_by_id(
            user=current_user,
            application_id=application_id,
            db=db,
        )
    except PackageNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    except Exception as exc:
        logger.exception(
            "application_package_get_failed",
            extra={"user_id": str(current_user.id), "error_type": type(exc).__name__},
        )
        raise HTTPException(status_code=500, detail="Retrieval failed.")
    return package.to_dict()


@router.get(
    "/api/freelancing/application-packages",
    status_code=status.HTTP_200_OK,
)
async def list_application_packages(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    List authenticated user's controlled application packages.

    Returns newest-first, paginated.  Never returns other users' packages.
    """
    packages = await _application_package_service.list_for_user(
        user=current_user,
        db=db,
        limit=min(limit, 50),
        offset=max(offset, 0),
    )
    return {
        "packages": [p.to_dict() for p in packages],
        "count": len(packages),
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/api/freelancing/application-packages/{application_id}/review",
    status_code=status.HTTP_200_OK,
)
async def review_application_package(
    application_id: str,
    request: PackageReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Apply a human review decision to a controlled application package.

    Allowed decisions: 'approve' | 'reject'

    APPROVE:
      - Triggers a fresh server-side readiness re-assessment.
      - If the opportunity is no longer ready_to_apply, returns 409 with
        stale_readiness=true.  Package state remains READY_FOR_HUMAN_APPROVAL.
      - If still ready, state transitions to APPROVED.
      - Does NOT submit externally.

    REJECT:
      - No readiness re-check.
      - State transitions to REJECTED immediately.
      - Does NOT mutate learning.

    Both transitions are permanent.  A second review on an already-reviewed
    package returns 409.
    """
    try:
        package = await _application_package_service.review(
            user=current_user,
            application_id=application_id,
            decision=request.decision,
            note=request.note,
            db=db,
            opportunity_description=request.opportunity_description,
            required_skills=request.required_skills,
        )
    except PackageNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    except StaleReadinessError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "stale_readiness",
                "message": str(exc),
                "current_decision": exc.current_decision,
                "stale_on_approval_attempt": True,
            },
        )
    except ReviewStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_state_transition",
                "message": str(exc),
            },
        )
    except Exception as exc:
        logger.exception(
            "application_package_review_failed",
            extra={"user_id": str(current_user.id), "error_type": type(exc).__name__},
        )
        raise HTTPException(status_code=500, detail="Review failed.")
    return package.to_dict()
