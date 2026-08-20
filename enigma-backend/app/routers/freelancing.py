from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.auth import get_current_user, require_admin_user
from app.core.config import settings
from app.database import get_db
from app.freelancing.freelancer_client import (
    FreelancerClientError,
    FreelancerRateLimited,
    FreelancerTimeout,
    FreelancerUnauthorized,
)
from app.freelancing.freelancer_discovery_service import (
    FreelancerDiscoveryService,
    FreelancerNotConfiguredError,
)
from app.freelancing.submission_intent_service import (
    SubmissionIntentService,
    IntentNotFoundError,
    IntentEligibilityError,
    IntentStateError,
    IntentStaleReadinessError,
)
from app.models.user import User
from app.models.marketplace import MarketplaceJob, MarketplaceJobAssessment
from app.models.marketplace import ManualOpportunitySubmission
from app.freelancing.manual_intake import (
    DuplicateOpportunityError, ManualOpportunityService,
    ManualOpportunityStateError, normalize_source_url,
)
from app.freelancing.controlled_application_package import ControlledApplicationPackageService, ReadinessGateError
from app.work_market.models import (
    FreelanceJob,
    JobSource,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
    Platform,
    JobAssessment,
    Application,
    ApplicationStatus,
    ActiveWork,
)
from app.work_market.platform_registry import PlatformRegistry
from app.work_market.readiness_service import FreelancingReadinessService
from app.work_market.classifier import JobClassifier
from app.work_market.evaluator import JobEvaluator
from app.work_market.learning_analyzer import LearningAnalyzer
from app.work_market.application_draft_generator import ApplicationDraftGenerator
from app.work_market.repositories import (
    InMemoryPlatformRepository,
    InMemoryJobRepository,
    InMemoryJobClassificationRepository,
    InMemoryJobEvaluationRepository,
    InMemoryJobAssessmentRepository,
    InMemoryApplicationRepository,
    InMemoryActiveWorkRepository,
)
from app.work_market.knowledge_governance_adapter import MockKnowledgeProvider
from app.work_market.evidence_adapter import MockEvidenceProvider
from app.work_market.expert_domain_adapter import MockExpertDomainAdapter
from app.work_market.decision_adapter import MockDecisionProvider
from app.work_market.work_specification_adapter import MockWorkSpecificationProvider

router = APIRouter(prefix="/api/freelancing", tags=["freelancing"])

# Initialize submission intent service
_submission_intent_service = SubmissionIntentService()
_freelancer_discovery_service = FreelancerDiscoveryService(settings)
_manual_intake_service = ManualOpportunityService()
_manual_package_service = ControlledApplicationPackageService()

SUPPORTED_MANUAL_PLATFORMS = {"workana", "peopleperhour", "upwork", "freelancer", "mostaql", "other"}
SUPPORTED_LANGUAGES = {"ar", "en", "es", "fr"}
MANUAL_LIFECYCLES = {"draft", "ready_for_analysis", "analyzed", "proposal_prepared", "approved", "manually_submitted", "client_replied", "won", "lost", "withdrawn", "expired"}


class ManualOpportunityCreate(BaseModel):
    platform: str = Field(..., max_length=40)
    source_url: Optional[str] = Field(None, max_length=2000)
    external_project_id: Optional[str] = Field(None, max_length=200)
    title: str = Field(..., min_length=1, max_length=500)
    original_description: str = Field(..., min_length=1, max_length=30000)
    normalized_requirements: Dict[str, Any] = Field(default_factory=dict)
    budget_type: Optional[Literal["fixed", "hourly", "negotiable"]] = None
    budget_min: Optional[float] = Field(None, ge=0, le=100000000)
    budget_max: Optional[float] = Field(None, ge=0, le=100000000)
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    required_skills: List[str] = Field(default_factory=list, max_length=50)
    client_info: Dict[str, Any] = Field(default_factory=dict)
    source_language: str = "en"
    customer_preferred_language: str = "en"
    proposal_language: str = "en"
    translation_metadata: Dict[str, Any] = Field(default_factory=dict)
    analyze: bool = False

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in SUPPORTED_MANUAL_PLATFORMS:
            raise ValueError("Unsupported platform")
        return value

    @field_validator("source_language", "customer_preferred_language", "proposal_language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported language")
        return value

    @field_validator("required_skills")
    @classmethod
    def validate_manual_skills(cls, values: List[str]) -> List[str]:
        cleaned = [" ".join(value.split()) for value in values]
        if any(not value or len(value) > 100 for value in cleaned):
            raise ValueError("Skills must contain 1 to 100 characters")
        return cleaned

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: Optional[str]) -> Optional[str]:
        return normalize_source_url(value)

    @model_validator(mode="after")
    def validate_budget(self) -> "ManualOpportunityCreate":
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError("budget_min cannot exceed budget_max")
        return self


class ManualOpportunityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    original_description: Optional[str] = Field(None, min_length=1, max_length=30000)
    source_url: Optional[str] = Field(None, max_length=2000)
    external_project_id: Optional[str] = Field(None, max_length=200)
    normalized_requirements: Optional[Dict[str, Any]] = None
    budget_type: Optional[Literal["fixed", "hourly", "negotiable"]] = None
    budget_min: Optional[float] = Field(None, ge=0, le=100000000)
    budget_max: Optional[float] = Field(None, ge=0, le=100000000)
    currency: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    required_skills: Optional[List[str]] = Field(None, max_length=50)
    client_info: Optional[Dict[str, Any]] = None
    source_language: Optional[Literal["ar", "en", "es", "fr"]] = None
    customer_preferred_language: Optional[Literal["ar", "en", "es", "fr"]] = None
    proposal_language: Optional[Literal["ar", "en", "es", "fr"]] = None
    translation_metadata: Optional[Dict[str, Any]] = None

    @field_validator("source_url")
    @classmethod
    def validate_update_url(cls, value: Optional[str]) -> Optional[str]:
        return normalize_source_url(value)

class ManualSubmissionRequest(BaseModel):
    marketplace_proposal_id: Optional[str] = Field(None, max_length=200)
    submitted_at: Optional[datetime] = None
    proposal_text: str = Field(..., min_length=1, max_length=30000)
    submitted_price: Optional[float] = Field(None, ge=0, le=100000000)
    currency: str = Field(..., min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    delivery_estimate: Optional[str] = Field(None, max_length=200)
    admin_notes: Optional[str] = Field(None, max_length=5000)


class ManualOutcomeRequest(BaseModel):
    outcome: Literal["manually_submitted", "client_replied", "won", "lost", "withdrawn", "expired"]
    admin_notes: Optional[str] = Field(None, max_length=5000)


def _manual_job_dict(job: MarketplaceJob, submission: Optional[ManualOpportunitySubmission] = None) -> Dict[str, Any]:
    data = _durable_job_dict(job)
    data.update({
        "manual_entry": True, "no_live_api_connection": True,
        "original_text": job.original_text or job.description,
        "normalized_requirements": job.normalized_requirements or {},
        "source_language": job.source_language, "customer_preferred_language": job.customer_preferred_language,
        "proposal_language": job.proposal_language, "translation_metadata": job.translation_metadata or {},
        "created_by_user_id": job.created_by_user_id,
        "proposal_application_id": job.proposal_application_id,
        "submission": ({
            "marketplace_proposal_id": submission.marketplace_proposal_id,
            "submitted_at": submission.submitted_at.isoformat(),
            "proposal_text_snapshot": submission.proposal_text_snapshot,
            "submitted_price": float(submission.submitted_price) if submission.submitted_price is not None else None,
            "currency": submission.currency, "delivery_estimate": submission.delivery_estimate,
            "outcome_status": submission.outcome_status, "admin_notes": submission.admin_notes,
            "application_id": submission.application_id, "submission_intent_id": submission.submission_intent_id,
        } if submission else None),
    })
    return data


class FreelancerSyncRequest(BaseModel):
    query: Optional[str] = Field(default=None, max_length=200)
    skills: List[str] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=25, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, values: List[str]) -> List[str]:
        normalized = []
        for value in values:
            skill = " ".join(value.split())
            if not skill or len(skill) > 64:
                raise ValueError("Each skill must contain 1 to 64 characters")
            normalized.append(skill)
        return normalized

# Initialize repositories
platform_repository = InMemoryPlatformRepository()
job_repository = InMemoryJobRepository()
classification_repository = InMemoryJobClassificationRepository()
evaluation_repository = InMemoryJobEvaluationRepository()
assessment_repository = InMemoryJobAssessmentRepository()
application_repository = InMemoryApplicationRepository()
active_work_repository = InMemoryActiveWorkRepository()


def _durable_job_dict(job: MarketplaceJob, assessment: Optional[MarketplaceJobAssessment] = None) -> Dict:
    return {
        "job_id": job.job_id,
        "source": job.platform,
        "title": job.title,
        "description": job.description,
        "client_information": job.client_info or {},
        "budget": float(job.budget_max) if job.budget_max is not None else None,
        "budget_min": float(job.budget_min) if job.budget_min is not None else None,
        "budget_max": float(job.budget_max) if job.budget_max is not None else None,
        "currency": job.currency,
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "skills": job.skills_required or [],
        "source_url": job.url or "",
        "discovered_at": job.first_seen_at.isoformat() if job.first_seen_at else None,
        "last_seen_at": job.last_seen_at.isoformat() if job.last_seen_at else None,
        "lifecycle_status": job.lifecycle_status,
        "platform_job_id": job.platform_job_id,
        "metadata": job.job_metadata or {},
        "assessment": {
            "readiness": assessment.readiness,
            "decision": assessment.decision,
            "overall_readiness_score": assessment.overall_readiness_score,
            "missing_capabilities": assessment.missing_capabilities or [],
            "updated_at": assessment.updated_at.isoformat() if assessment.updated_at else None,
        } if assessment else None,
    }


# Initialize services with providers
platform_registry = PlatformRegistry()
knowledge_provider = MockKnowledgeProvider()
evidence_provider = MockEvidenceProvider()
expert_domain_provider = MockExpertDomainAdapter()
decision_provider = MockDecisionProvider()
work_specification_provider = MockWorkSpecificationProvider()
readiness_service = FreelancingReadinessService(
    knowledge_provider=knowledge_provider,
    evidence_provider=evidence_provider,
    expert_domain_provider=expert_domain_provider,
)
job_classifier = JobClassifier()
job_evaluator = JobEvaluator()
learning_analyzer = LearningAnalyzer()
draft_generator = ApplicationDraftGenerator()


@router.get("/")
async def get_freelancing_overview(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Get freelancing workspace overview.
    
    Returns summary statistics for the freelancing workspace.
    """
    platforms = platform_registry.get_all_platforms()
    connected_platforms = [p for p in platforms if p.connection_status.value == "connected"]
    
    jobs_discovered = await db.scalar(select(func.count(MarketplaceJob.id)).where(MarketplaceJob.profile_id == "enigma_profile"))
    return {
        "status": "active",
        "platforms_connected": len(connected_platforms),
        "platforms_total": len(platforms),
        "capabilities_ready": 3,  # TODO: Get from expert domain
        "overall_readiness": 0.78,  # TODO: Calculate from actual data
        "jobs_discovered": int(jobs_discovered or 0),
        "applications_total": len(application_repository.get_all_applications()),
    }


@router.get("/platforms")
async def get_platforms() -> List[Dict]:
    """
    Get all registered platforms.
    
    Returns platform registry with connection status and capabilities.
    """
    platforms = platform_registry.get_all_platforms()
    return [platform.to_dict() for platform in platforms]


@router.get("/platforms/{platform_id}")
async def get_platform(platform_id: str) -> Dict:
    """
    Get a specific platform by ID.
    """
    platform = platform_registry.get_platform(platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail=f"Platform {platform_id} not found")
    return platform.to_dict()


@router.get("/freelancer/connection/status")
async def get_freelancer_connection_status(
    current_user: User = Depends(require_admin_user),
) -> Dict:
    """Return configuration/runtime state without contacting Freelancer.com."""
    connection = _freelancer_discovery_service.connection_status()
    return {
        "platform": connection.platform,
        "state": connection.state,
        "configured": connection.configured,
        "sandbox": connection.sandbox,
        "last_sync_at": connection.last_sync_at,
        "last_error_code": connection.last_error_code,
    }


@router.post("/freelancer/sync")
async def sync_freelancer_opportunities(
    request: FreelancerSyncRequest,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Run one explicit, admin-triggered, read-only discovery transaction."""
    try:
        return await _freelancer_discovery_service.sync(
            db,
            query=request.query,
            skills=request.skills,
            limit=request.limit,
        )
    except FreelancerNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "not_configured", "message": str(exc)})
    except FreelancerUnauthorized:
        _freelancer_discovery_service.record_upstream_error("upstream_unauthorized")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "upstream_unauthorized", "message": "Freelancer authentication was rejected"})
    except FreelancerRateLimited:
        _freelancer_discovery_service.record_upstream_error("upstream_rate_limited")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "upstream_rate_limited", "message": "Freelancer rate limit reached"})
    except FreelancerTimeout:
        _freelancer_discovery_service.record_upstream_error("upstream_timeout")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail={"code": "upstream_timeout", "message": "Freelancer request timed out"})
    except FreelancerClientError:
        _freelancer_discovery_service.record_upstream_error("upstream_error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "upstream_error", "message": "Freelancer discovery failed"})


@router.get("/freelancer/sync/summary")
async def get_freelancer_sync_summary(
    current_user: User = Depends(require_admin_user),
) -> Dict:
    """Return the latest process-local safe sync metadata."""
    summary = _freelancer_discovery_service.last_summary()
    if summary is None:
        raise HTTPException(status_code=404, detail="No Freelancer sync has completed")
    return summary


@router.post("/manual/preview")
async def preview_manual_opportunity(
    request: ManualOpportunityCreate,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Validate and normalize without writing."""
    data = request.model_dump(exclude={"analyze"})
    duplicate = await _manual_intake_service.find_duplicate(
        db, platform=request.platform, external_project_id=request.external_project_id,
        source_url=request.source_url, title=request.title, client_info=request.client_info,
    )
    return {"valid": True, "normalized": data, "duplicate": {"existing_job_id": duplicate.job_id} if duplicate else None}


@router.post("/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_opportunity(
    request: ManualOpportunityCreate,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    try:
        job = await _manual_intake_service.create(
            db, actor_id=str(current_user.id), data=request.model_dump(exclude={"analyze"}), analyze=request.analyze,
        )
        if request.analyze:
            from app.routers.enigma_profile import _assess_existing_job
            await _assess_existing_job(job.job_id, current_user, db, commit=False)
            _manual_intake_service.transition(job, "analyzed")
        await db.commit()
        await db.refresh(job)
    except DuplicateOpportunityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "duplicate_opportunity", "existing_job_id": exc.existing_job_id})
    except Exception:
        await db.rollback()
        raise
    return _manual_job_dict(job)


@router.get("/manual")
async def list_manual_opportunities(
    current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    jobs = await _manual_intake_service.list(db)
    submissions = (await db.execute(select(ManualOpportunitySubmission).where(
        ManualOpportunitySubmission.profile_id == "enigma_profile",
    ))).scalars().all()
    by_job = {item.job_id: item for item in submissions}
    return [_manual_job_dict(job, by_job.get(job.job_id)) for job in jobs]


@router.get("/manual/{job_id}")
async def get_manual_opportunity(
    job_id: str, current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    job = await _manual_intake_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manual opportunity not found")
    submission = await db.scalar(select(ManualOpportunitySubmission).where(
        ManualOpportunitySubmission.profile_id == "enigma_profile", ManualOpportunitySubmission.job_id == job_id,
    ))
    assessment = await db.scalar(select(MarketplaceJobAssessment).where(
        MarketplaceJobAssessment.profile_id == "enigma_profile", MarketplaceJobAssessment.job_id == job_id,
    ))
    result = _manual_job_dict(job, submission)
    result["assessment"] = _durable_job_dict(job, assessment).get("assessment") if assessment else None
    return result


@router.patch("/manual/{job_id}")
async def update_manual_opportunity(
    job_id: str, request: ManualOpportunityUpdate,
    current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    job = await _manual_intake_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manual opportunity not found")
    data = request.model_dump(exclude_unset=True)
    min_budget = data.get("budget_min", float(job.budget_min) if job.budget_min is not None else None)
    max_budget = data.get("budget_max", float(job.budget_max) if job.budget_max is not None else None)
    if min_budget is not None and max_budget is not None and min_budget > max_budget:
        raise HTTPException(status_code=422, detail="budget_min cannot exceed budget_max")
    try:
        updated = await _manual_intake_service.update(db, job=job, data=data)
        await db.commit()
        await db.refresh(updated)
        return _manual_job_dict(updated)
    except DuplicateOpportunityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={"code": "duplicate_opportunity", "existing_job_id": exc.existing_job_id})
    except ManualOpportunityStateError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/manual/{job_id}/analyze")
async def analyze_manual_opportunity(
    job_id: str, current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    job = await _manual_intake_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manual opportunity not found")
    from app.routers.enigma_profile import _assess_existing_job
    if job.lifecycle_status != "ready_for_analysis":
        raise HTTPException(status_code=409, detail=f"Invalid lifecycle transition: {job.lifecycle_status} -> analyzed")
    try:
        result = await _assess_existing_job(job_id, current_user, db, commit=False)
        _manual_intake_service.transition(job, "analyzed")
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return result.model_dump() if hasattr(result, "model_dump") else result


@router.post("/manual/{job_id}/proposal-package")
async def prepare_manual_proposal_package(
    job_id: str, current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    job = await _manual_intake_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manual opportunity not found")
    try:
        package = await _manual_package_service.build(
            user=current_user, opportunity_title=job.title, opportunity_description=job.description,
            platform=job.platform, required_skills=job.skills_required or [], opportunity_id=job.job_id,
            target_id=None, db=db,
        )
    except ReadinessGateError as exc:
        raise HTTPException(status_code=409, detail={"code": "opportunity_not_ready", "decision": exc.decision})
    _manual_intake_service.transition(job, "proposal_prepared")
    job.proposal_application_id = package.application_id
    await db.commit()
    return package.to_dict()


@router.post("/manual/{job_id}/submission", status_code=status.HTTP_201_CREATED)
async def record_manual_submission(
    job_id: str, request: ManualSubmissionRequest,
    current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    job = await _manual_intake_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manual opportunity not found")
    try:
        record = await _manual_intake_service.record_submission(db, job=job, actor_id=str(current_user.id), data=request.model_dump())
        await db.commit()
        await db.refresh(record)
    except ManualOpportunityStateError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return _manual_job_dict(job, record)


@router.patch("/manual/{job_id}/outcome")
async def update_manual_submission_outcome(
    job_id: str, request: ManualOutcomeRequest,
    current_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    job = await _manual_intake_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manual opportunity not found")
    try:
        record = await _manual_intake_service.update_outcome(db, job=job, outcome=request.outcome, notes=request.admin_notes)
        await db.commit()
        await db.refresh(record)
    except ManualOpportunityStateError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return _manual_job_dict(job, record)


@router.get("/jobs")
async def get_jobs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> List[Dict]:
    """
    Get all discovered jobs.
    
    Returns list of jobs with their basic information.
    """
    jobs = (await db.execute(
        select(MarketplaceJob).where(MarketplaceJob.profile_id == "enigma_profile").order_by(MarketplaceJob.last_seen_at.desc())
    )).scalars().all()
    return [_durable_job_dict(job) for job in jobs]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Get a specific job by ID.
    
    Returns full job details including classification and evaluation.
    """
    job = await db.scalar(select(MarketplaceJob).where(MarketplaceJob.job_id == job_id, MarketplaceJob.profile_id == "enigma_profile"))
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    assessment = await db.scalar(select(MarketplaceJobAssessment).where(MarketplaceJobAssessment.job_id == job_id, MarketplaceJobAssessment.profile_id == "enigma_profile"))
    
    return {
        "job": _durable_job_dict(job, assessment),
        "classification": None,
        "evaluation": None,
        "assessment": {
            "readiness": assessment.readiness,
            "decision": assessment.decision,
            "overall_readiness_score": assessment.overall_readiness_score,
            "required_capabilities": assessment.required_capabilities or [],
            "missing_capabilities": assessment.missing_capabilities or [],
            "weak_capabilities": assessment.weak_capabilities or [],
            "unmapped_skills": assessment.unmapped_skills or [],
            "risk_flags": assessment.risk_flags or [],
            "reasoning_summary": assessment.reasoning_summary or "",
            "blocking_capability": assessment.blocking_capability,
        } if assessment else None,
    }


@router.get("/jobs/{job_id}/assessment")
async def get_job_assessment(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Get job readiness assessment.
    
    Returns Enigma's assessment of job readiness including blockers and risks.
    """
    job = await db.scalar(select(MarketplaceJob).where(MarketplaceJob.job_id == job_id, MarketplaceJob.profile_id == "enigma_profile"))
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    assessment = await db.scalar(select(MarketplaceJobAssessment).where(MarketplaceJobAssessment.job_id == job_id, MarketplaceJobAssessment.profile_id == "enigma_profile"))
    if not assessment:
        raise HTTPException(status_code=404, detail="No durable assessment exists for this job")
    return {
        "job_id": assessment.job_id,
        "readiness": assessment.readiness,
        "decision": assessment.decision,
        "overall_readiness_score": assessment.overall_readiness_score,
        "required_capabilities": assessment.required_capabilities or [],
        "missing_capabilities": assessment.missing_capabilities or [],
        "weak_capabilities": assessment.weak_capabilities or [],
        "unmapped_skills": assessment.unmapped_skills or [],
        "risk_flags": assessment.risk_flags or [],
        "reasoning_summary": assessment.reasoning_summary or "",
        "assessed_at": assessment.assessed_at.isoformat() if assessment.assessed_at else None,
    }


@router.post("/jobs/{job_id}/research")
async def start_job_research(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Start research for a job.
    
    Triggers research process to fill knowledge gaps.
    Returns research status and learning requirements.
    """
    job = await db.scalar(select(MarketplaceJob).where(MarketplaceJob.job_id == job_id, MarketplaceJob.profile_id == "enigma_profile"))
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    assessment = await db.scalar(select(MarketplaceJobAssessment).where(MarketplaceJobAssessment.job_id == job_id, MarketplaceJobAssessment.profile_id == "enigma_profile"))
    if not assessment:
        raise HTTPException(status_code=400, detail="Job must be assessed first")
    
    # Generate learning requirements
    learning_requirements = {
        "job_id": job_id,
        "missing_capabilities": assessment.missing_capabilities or [],
        "research_tasks": [],
        "academy_modules": [],
        "priority": "medium",
    }
    
    # TODO: Integrate with Knowledge Governance to trigger actual research
    
    return {
        "job_id": job_id,
        "research_status": "initiated",
        "learning_requirements": learning_requirements,
        "message": "Research initiated. Check back for updates.",
    }


@router.get("/applications")
async def get_applications() -> List[Dict]:
    """
    Get all applications.
    
    Returns list of applications with their current status.
    """
    applications = application_repository.get_all_applications()
    return [application.to_dict() for application in applications]


@router.get("/applications/{application_id}")
async def get_application(application_id: str) -> Dict:
    """
    Get a specific application by ID.
    
    Returns full application details including draft and status.
    """
    application = application_repository.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    
    return application.to_dict()


@router.post("/applications")
async def create_application(request: Dict) -> Dict:
    """
    Create a new application draft.
    
    Creates an application draft for a job after readiness assessment.
    Requires decision layer approval before creation.
    """
    job_id = request.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    
    job = job_repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    assessment = assessment_repository.get_assessment(job_id)
    if not assessment:
        raise HTTPException(status_code=400, detail="Job must be assessed first")
    
    # Check if ready to apply
    if not readiness_service.can_apply(assessment):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Cannot apply yet",
                "blockers": readiness_service.get_application_blockers(assessment),
                "required_learning": readiness_service.get_required_learning(assessment),
            }
        )
    
    # Request decision from decision layer
    decision_context = {
        "job_id": job_id,
        "readiness": assessment.overall_readiness,
        "blockers": assessment.blockers,
        "risks": assessment.risks,
        "recommendation": assessment.recommendation.value,
    }
    
    decision_record = decision_provider.request_decision(decision_context)
    
    # Check if decision allows proceeding
    if not decision_provider.can_proceed(decision_record):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Decision layer rejected application",
                "decision": decision_record.get("decision"),
                "reasoning": decision_record.get("reasoning"),
                "blockers": decision_record.get("blockers"),
                "requirements": decision_record.get("requirements"),
            }
        )
    
    # Generate application draft
    classification = classification_repository.get_classification(job_id)
    evaluation = evaluation_repository.get_evaluation(job_id)
    
    if not classification or not evaluation:
        raise HTTPException(status_code=400, detail="Job must be classified and evaluated first")
    
    draft = draft_generator.generate_draft(job, classification, evaluation)
    
    # Create application record
    application_id = str(uuid4())
    application = Application(
        application_id=application_id,
        job_id=job_id,
        platform=job.source.value,
        status=ApplicationStatus.DRAFTED,
        draft_id=draft.understanding_of_task[:50],  # Use part of understanding as draft ID
        blockers=[],
        metadata={"decision_record": decision_record},
    )
    
    application_repository.save_application(application)
    
    return {
        "application": application.to_dict(),
        "draft": draft.to_dict(),
        "decision": decision_record,
        "message": "Application draft created successfully with decision approval",
    }


@router.get("/active-work")
async def get_active_work() -> List[Dict]:
    """
    Get all active work.
    
    Returns list of active work items with their lifecycle state.
    """
    active_work = active_work_repository.get_all_active_work()
    return [work.to_dict() for work in active_work]


@router.get("/capabilities")
async def get_capabilities() -> List[Dict]:
    """
    Get Enigma's capabilities for freelancing.
    
    Returns capabilities with readiness scores from the expert domain.
    """
    # Get capabilities from expert domain provider
    domain = expert_domain_provider.get_active_domain()
    if domain:
        capabilities = expert_domain_provider.get_domain_capabilities(domain.domain_id)
    else:
        # Use mock capabilities
        capabilities = expert_domain_provider.get_domain_capabilities("default")
    
    # Build capability list with readiness
    capability_list = []
    for cap in capabilities:
        readiness = expert_domain_provider.get_domain_readiness("default")
        capability_list.append({
            "id": cap.lower().replace(" ", "_"),
            "name": cap,
            "knowledge_maturity": "Applied",  # TODO: Get from knowledge governance
            "readiness_status": "READY" if readiness and readiness.overall_readiness > 0.7 else "PARTIALLY_READY",
            "readiness_score": readiness.overall_readiness if readiness else 0.5,
            "evidence_count": 5,  # TODO: Get from evidence provider
            "freshness": "Fresh",  # TODO: Get from knowledge governance
            "status": "READY",
        })
    
    return capability_list


# ---------------------------------------------------------------------------
# TASK-052: Submission Intent API Endpoints
# ---------------------------------------------------------------------------

@router.post("/application-packages/{application_id}/submission-intent")
async def create_submission_intent(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    Create or reuse a PENDING_EXTERNAL_SUBMISSION intent for an APPROVED application package.
    
    TASK-052: Safe boundary - no external submission occurs.
    Eligibility requires: package exists, owned by user, state=APPROVED, fresh readiness passes.
    """
    try:
        intent = await _submission_intent_service.create_intent(
            user=current_user,
            application_id=application_id,
            db=db,
        )
        return intent.to_dict()
    except IntentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IntentEligibilityError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": str(e), "reason": e.reason},
        )
    except IntentStaleReadinessError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "current_decision": e.current_decision,
                "reason": "stale_readiness",
            },
        )


@router.get("/submission-intents/{submission_id}")
async def get_submission_intent(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    Get a specific submission intent by ID.
    
    TASK-052: Ownership-scoped - cross-user returns 404.
    """
    try:
        intent = await _submission_intent_service.get_by_id(
            user=current_user,
            submission_id=submission_id,
            db=db,
        )
        return intent.to_dict()
    except IntentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/submission-intents")
async def list_submission_intents(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    List submission intents for the authenticated user.
    
    TASK-052: Ownership-scoped - only user's own intents.
    """
    intents = await _submission_intent_service.list_for_user(
        user=current_user,
        db=db,
        limit=limit,
        offset=offset,
    )
    return {
        "intents": [intent.to_dict() for intent in intents],
        "count": len(intents),
        "limit": limit,
        "offset": offset,
    }


@router.post("/submission-intents/{submission_id}/cancel")
async def cancel_submission_intent(
    submission_id: str,
    note: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    Cancel a PENDING_EXTERNAL_SUBMISSION intent.
    
    TASK-052: Does NOT contact external platforms.
    Only PENDING_EXTERNAL_SUBMISSION can be cancelled.
    """
    try:
        intent = await _submission_intent_service.cancel_intent(
            user=current_user,
            submission_id=submission_id,
            note=note,
            db=db,
        )
        return intent.to_dict()
    except IntentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IntentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Helper endpoint for testing - add a sample job
@router.post("/jobs/sample")
async def add_sample_job() -> Dict:
    """
    Add a sample job for testing purposes.
    """
    job_id = str(uuid4())
    job = FreelanceJob(
        job_id=job_id,
        source=JobSource.UPWORK,
        title="SEO Audit for E-commerce Site",
        description="Need a comprehensive SEO audit for my e-commerce website to improve rankings and traffic.",
        client_information={"client_name": "Tech Startup Inc", "client_rating": "4.8"},
        budget=75.0,
        currency="USD",
        skills=["SEO", "Technical SEO", "Keyword Research", "Competitor Analysis"],
        source_url="https://upwork.com/jobs/sample",
    )
    
    job_repository.save_job(job)
    
    # Classify the job
    classification = job_classifier.classify(job)
    classification_repository.save_classification(classification)
    
    # Evaluate the job
    evaluation = job_evaluator.evaluate(job, classification)
    evaluation_repository.save_evaluation(evaluation)
    
    # Assess readiness
    assessment = readiness_service.assess_readiness(job, classification, evaluation)
    assessment_repository.save_assessment(assessment)
    
    return {
        "job": job.to_dict(),
        "classification": classification.to_dict(),
        "evaluation": evaluation.to_dict(),
        "assessment": assessment.to_dict(),
    }
