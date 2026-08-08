from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

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
from app.knowledge_governance.models import GovernedKnowledge
from app.expert_domains.contracts import ExpertDomainContract, ReadinessScore


class KnowledgeProvider(ABC):
    """Contract for providing governed knowledge to freelancing layer."""

    @abstractmethod
    def get_knowledge_for_concept(self, concept_id: str) -> Optional[GovernedKnowledge]:
        """Get governed knowledge for a specific concept."""
        pass

    @abstractmethod
    def get_knowledge_maturity(self, concept_id: str) -> float:
        """Get knowledge maturity score (0.0 to 1.0)."""
        pass

    @abstractmethod
    def get_knowledge_freshness(self, concept_id: str) -> float:
        """Get knowledge freshness score (0.0 to 1.0)."""
        pass

    @abstractmethod
    def get_knowledge_confidence(self, concept_id: str) -> float:
        """Get knowledge confidence score (0.0 to 1.0)."""
        pass


class EvidenceProvider(ABC):
    """Contract for providing evidence information to freelancing layer."""

    @abstractmethod
    def get_evidence_for_capability(self, capability_id: str) -> Dict[str, Any]:
        """Get evidence information for a capability."""
        pass

    @abstractmethod
    def get_evidence_coverage(self, capability_id: str) -> float:
        """Get evidence coverage score (0.0 to 1.0)."""
        pass

    @abstractmethod
    def get_evidence_quality(self, capability_id: str) -> float:
        """Get evidence quality score (0.0 to 1.0)."""
        pass

    @abstractmethod
    def get_evidence_freshness(self, capability_id: str) -> float:
        """Get evidence freshness score (0.0 to 1.0)."""
        pass


class ProfessionProvider(ABC):
    """Contract for providing profession information."""

    @abstractmethod
    def get_profession_capabilities(self, profession_id: str) -> List[str]:
        """Get capabilities for a profession."""
        pass

    @abstractmethod
    def get_profession_readiness(self, profession_id: str) -> float:
        """Get profession readiness score (0.0 to 1.0)."""
        pass


class ExpertDomainProvider(ABC):
    """Contract for providing expert domain information."""

    @abstractmethod
    def get_active_domain(self) -> Optional[ExpertDomainContract]:
        """Get the currently active expert domain."""
        pass

    @abstractmethod
    def get_domain_capabilities(self, domain_id: str) -> List[str]:
        """Get capabilities for a domain."""
        pass

    @abstractmethod
    def get_domain_readiness(self, domain_id: str) -> Optional[ReadinessScore]:
        """Get readiness score for a domain."""
        pass

    @abstractmethod
    def get_domain_tasks(self, domain_id: str) -> List[Dict[str, Any]]:
        """Get tasks for a domain."""
        pass


class DecisionProvider(ABC):
    """Contract for decision layer integration."""

    @abstractmethod
    def request_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request a decision from the decision engine.
        
        Returns decision record with:
        - decision: ACCEPT, REJECT, NEED_LEARNING, NEED_RESEARCH, etc.
        - confidence: Decision confidence score
        - reasoning: Decision reasoning
        - blockers: Any blockers
        - requirements: Any requirements
        """
        pass

    @abstractmethod
    def can_proceed(self, decision_record: Dict[str, Any]) -> bool:
        """Check if a decision allows proceeding."""
        pass


class WorkSpecificationProvider(ABC):
    """Contract for work specification transformation."""

    @abstractmethod
    def transform_job_to_specification(self, job: FreelanceJob) -> Dict[str, Any]:
        """
        Transform a marketplace job into a work specification.
        
        Returns:
        - work_specification_id
        - requirements
        - deliverables
        - acceptance_criteria
        - success_metrics
        - constraints
        """
        pass

    @abstractmethod
    def get_specification(self, spec_id: str) -> Optional[Dict[str, Any]]:
        """Get a work specification by ID."""
        pass


class PlatformRepository(ABC):
    """Contract for platform data persistence."""

    @abstractmethod
    def get_platform(self, platform_id: str) -> Optional[Platform]:
        """Get a platform by ID."""
        pass

    @abstractmethod
    def get_all_platforms(self) -> List[Platform]:
        """Get all platforms."""
        pass

    @abstractmethod
    def save_platform(self, platform: Platform) -> Platform:
        """Save a platform."""
        pass

    @abstractmethod
    def update_platform_status(self, platform_id: str, status: str) -> Optional[Platform]:
        """Update platform connection status."""
        pass


class JobRepository(ABC):
    """Contract for job data persistence."""

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[FreelanceJob]:
        """Get a job by ID."""
        pass

    @abstractmethod
    def get_all_jobs(self) -> List[FreelanceJob]:
        """Get all jobs."""
        pass

    @abstractmethod
    def save_job(self, job: FreelanceJob) -> FreelanceJob:
        """Save a job."""
        pass

    @abstractmethod
    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        pass


class JobClassificationRepository(ABC):
    """Contract for job classification persistence."""

    @abstractmethod
    def get_classification(self, job_id: str) -> Optional[JobClassification]:
        """Get classification for a job."""
        pass

    @abstractmethod
    def save_classification(self, classification: JobClassification) -> JobClassification:
        """Save a classification."""
        pass


class JobEvaluationRepository(ABC):
    """Contract for job evaluation persistence."""

    @abstractmethod
    def get_evaluation(self, job_id: str) -> Optional[JobEvaluation]:
        """Get evaluation for a job."""
        pass

    @abstractmethod
    def save_evaluation(self, evaluation: JobEvaluation) -> JobEvaluation:
        """Save an evaluation."""
        pass


class JobAssessmentRepository(ABC):
    """Contract for job assessment persistence."""

    @abstractmethod
    def get_assessment(self, job_id: str) -> Optional[JobAssessment]:
        """Get assessment for a job."""
        pass

    @abstractmethod
    def save_assessment(self, assessment: JobAssessment) -> JobAssessment:
        """Save an assessment."""
        pass


class ApplicationRepository(ABC):
    """Contract for application data persistence."""

    @abstractmethod
    def get_application(self, application_id: str) -> Optional[Application]:
        """Get an application by ID."""
        pass

    @abstractmethod
    def get_all_applications(self) -> List[Application]:
        """Get all applications."""
        pass

    @abstractmethod
    def get_applications_for_job(self, job_id: str) -> List[Application]:
        """Get applications for a specific job."""
        pass

    @abstractmethod
    def save_application(self, application: Application) -> Application:
        """Save an application."""
        pass

    @abstractmethod
    def update_application_status(
        self,
        application_id: str,
        status: ApplicationStatus
    ) -> Optional[Application]:
        """Update application status."""
        pass


class ActiveWorkRepository(ABC):
    """Contract for active work data persistence."""

    @abstractmethod
    def get_active_work(self, work_id: str) -> Optional[ActiveWork]:
        """Get active work by ID."""
        pass

    @abstractmethod
    def get_all_active_work(self) -> List[ActiveWork]:
        """Get all active work."""
        pass

    @abstractmethod
    def save_active_work(self, work: ActiveWork) -> ActiveWork:
        """Save active work."""
        pass

    @abstractmethod
    def update_work_state(self, work_id: str, state: str) -> Optional[ActiveWork]:
        """Update work state."""
        pass
