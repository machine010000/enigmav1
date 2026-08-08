from __future__ import annotations

from typing import Dict, List, Optional

from app.work_market.models import (
    Platform,
    FreelanceJob,
    JobClassification,
    JobEvaluation,
    JobAssessment,
    Application,
    ApplicationStatus,
    ActiveWork,
)
from app.work_market.contracts import (
    PlatformRepository,
    JobRepository,
    JobClassificationRepository,
    JobEvaluationRepository,
    JobAssessmentRepository,
    ApplicationRepository,
    ActiveWorkRepository,
)


class InMemoryPlatformRepository(PlatformRepository):
    """In-memory implementation of PlatformRepository for development/testing."""

    def __init__(self) -> None:
        self._platforms: Dict[str, Platform] = {}

    def get_platform(self, platform_id: str) -> Optional[Platform]:
        return self._platforms.get(platform_id)

    def get_all_platforms(self) -> List[Platform]:
        return list(self._platforms.values())

    def save_platform(self, platform: Platform) -> Platform:
        self._platforms[platform.platform_id] = platform
        return platform

    def update_platform_status(self, platform_id: str, status: str) -> Optional[Platform]:
        platform = self._platforms.get(platform_id)
        if not platform:
            return None
        # Create updated platform (immutable pattern)
        from app.work_market.models import PlatformConnectionStatus
        from dataclasses import replace
        
        updated = replace(platform, connection_status=PlatformConnectionStatus(status))
        self._platforms[platform_id] = updated
        return updated


class InMemoryJobRepository(JobRepository):
    """In-memory implementation of JobRepository for development/testing."""

    def __init__(self) -> None:
        self._jobs: Dict[str, FreelanceJob] = {}

    def get_job(self, job_id: str) -> Optional[FreelanceJob]:
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[FreelanceJob]:
        return list(self._jobs.values())

    def save_job(self, job: FreelanceJob) -> FreelanceJob:
        self._jobs[job.job_id] = job
        return job

    def delete_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False


class InMemoryJobClassificationRepository(JobClassificationRepository):
    """In-memory implementation of JobClassificationRepository for development/testing."""

    def __init__(self) -> None:
        self._classifications: Dict[str, JobClassification] = {}

    def get_classification(self, job_id: str) -> Optional[JobClassification]:
        return self._classifications.get(job_id)

    def save_classification(self, classification: JobClassification) -> JobClassification:
        self._classifications[classification.job_id] = classification
        return classification


class InMemoryJobEvaluationRepository(JobEvaluationRepository):
    """In-memory implementation of JobEvaluationRepository for development/testing."""

    def __init__(self) -> None:
        self._evaluations: Dict[str, JobEvaluation] = {}

    def get_evaluation(self, job_id: str) -> Optional[JobEvaluation]:
        return self._evaluations.get(job_id)

    def save_evaluation(self, evaluation: JobEvaluation) -> JobEvaluation:
        self._evaluations[evaluation.job_id] = evaluation
        return evaluation


class InMemoryJobAssessmentRepository(JobAssessmentRepository):
    """In-memory implementation of JobAssessmentRepository for development/testing."""

    def __init__(self) -> None:
        self._assessments: Dict[str, JobAssessment] = {}

    def get_assessment(self, job_id: str) -> Optional[JobAssessment]:
        return self._assessments.get(job_id)

    def save_assessment(self, assessment: JobAssessment) -> JobAssessment:
        self._assessments[assessment.job_id] = assessment
        return assessment


class InMemoryApplicationRepository(ApplicationRepository):
    """In-memory implementation of ApplicationRepository for development/testing."""

    def __init__(self) -> None:
        self._applications: Dict[str, Application] = {}

    def get_application(self, application_id: str) -> Optional[Application]:
        return self._applications.get(application_id)

    def get_all_applications(self) -> List[Application]:
        return list(self._applications.values())

    def get_applications_for_job(self, job_id: str) -> List[Application]:
        return [app for app in self._applications.values() if app.job_id == job_id]

    def save_application(self, application: Application) -> Application:
        self._applications[application.application_id] = application
        return application

    def update_application_status(
        self,
        application_id: str,
        status: ApplicationStatus
    ) -> Optional[Application]:
        application = self._applications.get(application_id)
        if not application:
            return None
        from dataclasses import replace
        from datetime import datetime
        
        updated = replace(application, status=status, updated_at=datetime.utcnow())
        self._applications[application_id] = updated
        return updated


class InMemoryActiveWorkRepository(ActiveWorkRepository):
    """In-memory implementation of ActiveWorkRepository for development/testing."""

    def __init__(self) -> None:
        self._active_work: Dict[str, ActiveWork] = {}

    def get_active_work(self, work_id: str) -> Optional[ActiveWork]:
        return self._active_work.get(work_id)

    def get_all_active_work(self) -> List[ActiveWork]:
        return list(self._active_work.values())

    def save_active_work(self, work: ActiveWork) -> ActiveWork:
        self._active_work[work.work_id] = work
        return work

    def update_work_state(self, work_id: str, state: str) -> Optional[ActiveWork]:
        work = self._active_work.get(work_id)
        if not work:
            return None
        from dataclasses import replace
        
        updated = replace(work, state=state)
        self._active_work[work_id] = updated
        return updated
