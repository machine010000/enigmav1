from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.auth import get_current_user
from app.database import get_db
from app.freelancing.submission_intent_service import (
    SubmissionIntentService,
    IntentNotFoundError,
    IntentEligibilityError,
    IntentStateError,
    IntentStaleReadinessError,
)
from app.models.user import User
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

# Initialize repositories
platform_repository = InMemoryPlatformRepository()
job_repository = InMemoryJobRepository()
classification_repository = InMemoryJobClassificationRepository()
evaluation_repository = InMemoryJobEvaluationRepository()
assessment_repository = InMemoryJobAssessmentRepository()
application_repository = InMemoryApplicationRepository()
active_work_repository = InMemoryActiveWorkRepository()

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
async def get_freelancing_overview() -> Dict:
    """
    Get freelancing workspace overview.
    
    Returns summary statistics for the freelancing workspace.
    """
    platforms = platform_registry.get_all_platforms()
    connected_platforms = [p for p in platforms if p.connection_status.value == "connected"]
    
    return {
        "status": "active",
        "platforms_connected": len(connected_platforms),
        "platforms_total": len(platforms),
        "capabilities_ready": 3,  # TODO: Get from expert domain
        "overall_readiness": 0.78,  # TODO: Calculate from actual data
        "jobs_discovered": len(job_repository.get_all_jobs()),
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


@router.get("/jobs")
async def get_jobs() -> List[Dict]:
    """
    Get all discovered jobs.
    
    Returns list of jobs with their basic information.
    """
    jobs = job_repository.get_all_jobs()
    return [job.to_dict() for job in jobs]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Dict:
    """
    Get a specific job by ID.
    
    Returns full job details including classification and evaluation.
    """
    job = job_repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    classification = classification_repository.get_classification(job_id)
    evaluation = evaluation_repository.get_evaluation(job_id)
    assessment = assessment_repository.get_assessment(job_id)
    
    return {
        "job": job.to_dict(),
        "classification": classification.to_dict() if classification else None,
        "evaluation": evaluation.to_dict() if evaluation else None,
        "assessment": assessment.to_dict() if assessment else None,
    }


@router.get("/jobs/{job_id}/assessment")
async def get_job_assessment(job_id: str) -> Dict:
    """
    Get job readiness assessment.
    
    Returns Enigma's assessment of job readiness including blockers and risks.
    """
    job = job_repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    assessment = assessment_repository.get_assessment(job_id)
    if not assessment:
        # Generate assessment on-demand
        classification = classification_repository.get_classification(job_id)
        evaluation = evaluation_repository.get_evaluation(job_id)
        
        if not classification or not evaluation:
            raise HTTPException(
                status_code=400,
                detail="Job must be classified and evaluated before assessment"
            )
        
        assessment = readiness_service.assess_readiness(job, classification, evaluation)
        assessment_repository.save_assessment(assessment)
    
    return assessment.to_dict()


@router.post("/jobs/{job_id}/research")
async def start_job_research(job_id: str) -> Dict:
    """
    Start research for a job.
    
    Triggers research process to fill knowledge gaps.
    Returns research status and learning requirements.
    """
    job = job_repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    assessment = assessment_repository.get_assessment(job_id)
    if not assessment:
        raise HTTPException(status_code=400, detail="Job must be assessed first")
    
    # Generate learning requirements
    classification = classification_repository.get_classification(job_id)
    evaluation = evaluation_repository.get_evaluation(job_id)
    
    if not classification or not evaluation:
        raise HTTPException(status_code=400, detail="Job must be classified and evaluated first")
    
    learning_requirements = learning_analyzer.create_learning_requirement(evaluation)
    
    # TODO: Integrate with Knowledge Governance to trigger actual research
    
    return {
        "job_id": job_id,
        "research_status": "initiated",
        "learning_requirements": learning_requirements.to_dict() if learning_requirements else None,
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
