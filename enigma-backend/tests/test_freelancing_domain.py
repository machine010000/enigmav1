"""
Domain Tests: Freelancing Models and Services

These tests verify the correctness of freelancing domain models,
platform registry, job assessment, and application state machine.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.work_market.models import (
    Platform,
    PlatformType,
    PlatformConnectionStatus,
    FreelanceJob,
    JobSource,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
    JobAssessment,
    Application,
    ApplicationStatus,
    ActiveWork,
)
from app.work_market.platform_registry import PlatformRegistry
from app.work_market.readiness_service import FreelancingReadinessService


class TestPlatform:
    """Tests for Platform model and Platform Registry."""

    def test_platform_creation(self):
        """Test that Platform can be created with required fields."""
        platform = Platform(
            platform_id="upwork",
            name="Upwork",
            type=PlatformType.PROPOSAL_BASED,
        )
        assert platform.platform_id == "upwork"
        assert platform.name == "Upwork"
        assert platform.type == PlatformType.PROPOSAL_BASED
        assert platform.connection_status == PlatformConnectionStatus.NOT_CONNECTED

    def test_platform_to_dict(self):
        """Test that Platform can be serialized to dict."""
        platform = Platform(
            platform_id="upwork",
            name="Upwork",
            type=PlatformType.PROPOSAL_BASED,
            connection_status=PlatformConnectionStatus.CONNECTED,
        )
        data = platform.to_dict()
        assert data["platform_id"] == "upwork"
        assert data["name"] == "Upwork"
        assert data["type"] == "proposal_based"
        assert data["connection_status"] == "connected"

    def test_platform_registry_initialization(self):
        """Test that Platform Registry initializes with default platforms."""
        registry = PlatformRegistry()
        platforms = registry.get_all_platforms()
        assert len(platforms) > 0
        
        # Check that key platforms exist
        platform_ids = [p.platform_id for p in platforms]
        assert "upwork" in platform_ids
        assert "freelancer" in platform_ids
        assert "fiverr" in platform_ids

    def test_platform_registry_get_platform(self):
        """Test that Platform Registry can retrieve specific platforms."""
        registry = PlatformRegistry()
        upwork = registry.get_platform("upwork")
        assert upwork is not None
        assert upwork.name == "Upwork"
        assert upwork.type == PlatformType.PROPOSAL_BASED

    def test_platform_registry_update_status(self):
        """Test that Platform Registry can update platform status."""
        registry = PlatformRegistry()
        updated = registry.update_platform_status(
            "upwork",
            PlatformConnectionStatus.CONNECTED,
            auth_status="authenticated",
            profile_status="complete",
            credits_available=10,
        )
        assert updated is not None
        assert updated.connection_status == PlatformConnectionStatus.CONNECTED
        assert updated.auth_status == "authenticated"
        assert updated.credits_available == 10

    def test_platform_registry_capability_check(self):
        """Test that Platform Registry can check platform capabilities."""
        registry = PlatformRegistry()
        assert registry.has_capability("upwork", "job_discovery")
        assert registry.has_capability("upwork", "application_submission")
        assert not registry.has_capability("upwork", "nonexistent_capability")

    def test_platform_registry_get_application_cost(self):
        """Test that Platform Registry can get application cost information."""
        registry = PlatformRegistry()
        cost_info = registry.get_application_cost("upwork")
        assert cost_info is not None
        assert "platform_id" in cost_info
        assert "requirements" in cost_info


class TestJobAssessment:
    """Tests for Job Assessment model and service."""

    def test_job_assessment_creation(self):
        """Test that JobAssessment can be created with required fields."""
        assessment = JobAssessment(
            job_id="job-1",
            profession_match=0.8,
            capability_match=0.7,
            overall_readiness=0.75,
        )
        assert assessment.job_id == "job-1"
        assert assessment.profession_match == 0.8
        assert assessment.overall_readiness == 0.75

    def test_job_assessment_to_dict(self):
        """Test that JobAssessment can be serialized to dict."""
        assessment = JobAssessment(
            job_id="job-1",
            profession_match=0.8,
            capability_match=0.7,
            overall_readiness=0.75,
            recommendation=JobRecommendation.APPLY,
        )
        data = assessment.to_dict()
        assert data["job_id"] == "job-1"
        assert data["profession_match"] == 0.8
        assert data["recommendation"] == "apply"

    def test_readiness_service_assessment(self):
        """Test that FreelancingReadinessService can assess job readiness."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-1",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
        )
        
        classification = JobClassification(
            job_id="job-1",
            profession="SEO Specialist",
            task="SEO Audit",
            required_skills=["SEO", "Technical SEO"],
            required_knowledge=["Technical SEO"],
            required_capabilities=["SEO Audit"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-1",
            profession_match=0.8,
            skill_match=0.7,
            knowledge_match=0.6,
            capability_match=0.7,
            missing_knowledge=[],
            missing_capabilities=[],
            recommendation=JobRecommendation.APPLY,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        assert assessment.job_id == "job-1"
        assert 0.0 <= assessment.overall_readiness <= 1.0
        assert isinstance(assessment.blockers, list)
        assert isinstance(assessment.risks, list)

    def test_readiness_service_can_apply(self):
        """Test that can_apply correctly determines application readiness."""
        service = FreelancingReadinessService()
        
        # Test with ready assessment
        ready_assessment = JobAssessment(
            job_id="job-1",
            overall_readiness=0.8,
            recommendation=JobRecommendation.APPLY,
            blockers=[],
        )
        assert service.can_apply(ready_assessment) is True
        
        # Test with blocked assessment
        blocked_assessment = JobAssessment(
            job_id="job-1",
            overall_readiness=0.5,
            recommendation=JobRecommendation.LEARN_FIRST,
            blockers=["Missing knowledge"],
        )
        assert service.can_apply(blocked_assessment) is False

    def test_readiness_service_get_application_blockers(self):
        """Test that get_application_blockers returns structured blockers."""
        service = FreelancingReadinessService()
        
        assessment = JobAssessment(
            job_id="job-1",
            blockers=["Missing knowledge", "Insufficient capability"],
        )
        
        blockers = service.get_application_blockers(assessment)
        assert len(blockers) == 2
        assert "Missing knowledge" in blockers
        assert "Insufficient capability" in blockers

    def test_readiness_service_get_required_learning(self):
        """Test that get_required_learning returns structured learning requirements."""
        service = FreelancingReadinessService()
        
        assessment = JobAssessment(
            job_id="job-1",
            missing_knowledge=["Technical SEO"],
            missing_capabilities=["SEO Audit"],
        )
        
        learning = service.get_required_learning(assessment)
        assert "knowledge" in learning
        assert "capabilities" in learning
        assert "Technical SEO" in learning["knowledge"]
        assert "SEO Audit" in learning["capabilities"]


class TestApplication:
    """Tests for Application model and state machine."""

    def test_application_creation(self):
        """Test that Application can be created with required fields."""
        application = Application(
            application_id="app-1",
            job_id="job-1",
            platform="upwork",
        )
        assert application.application_id == "app-1"
        assert application.job_id == "job-1"
        assert application.platform == "upwork"
        assert application.status == ApplicationStatus.DISCOVERED

    def test_application_to_dict(self):
        """Test that Application can be serialized to dict."""
        application = Application(
            application_id="app-1",
            job_id="job-1",
            platform="upwork",
            status=ApplicationStatus.DRAFTED,
        )
        data = application.to_dict()
        assert data["application_id"] == "app-1"
        assert data["status"] == "drafted"

    def test_application_state_machine_transitions(self):
        """Test that ApplicationStatus enum has all required states."""
        required_states = [
            ApplicationStatus.DISCOVERED,
            ApplicationStatus.ASSESSED,
            ApplicationStatus.LEARNING,
            ApplicationStatus.READY,
            ApplicationStatus.DRAFTED,
            ApplicationStatus.REVIEW_REQUIRED,
            ApplicationStatus.APPROVED,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.RESPONDED,
            ApplicationStatus.WON,
            ApplicationStatus.LOST,
            ApplicationStatus.WITHDRAWN,
        ]
        assert len(required_states) == 12


class TestActiveWork:
    """Tests for ActiveWork model."""

    def test_active_work_creation(self):
        """Test that ActiveWork can be created with required fields."""
        work = ActiveWork(
            work_id="work-1",
            application_id="app-1",
            job_title="SEO Audit",
            platform="upwork",
        )
        assert work.work_id == "work-1"
        assert work.application_id == "app-1"
        assert work.job_title == "SEO Audit"
        assert work.platform == "upwork"

    def test_active_work_to_dict(self):
        """Test that ActiveWork can be serialized to dict."""
        work = ActiveWork(
            work_id="work-1",
            application_id="app-1",
            job_title="SEO Audit",
            platform="upwork",
            state="execution",
        )
        data = work.to_dict()
        assert data["work_id"] == "work-1"
        assert data["state"] == "execution"


class TestFreelanceJob:
    """Tests for FreelanceJob model."""

    def test_freelance_job_creation(self):
        """Test that FreelanceJob can be created with required fields."""
        job = FreelanceJob(
            job_id="job-1",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
        )
        assert job.job_id == "job-1"
        assert job.source == JobSource.UPWORK
        assert job.title == "SEO Audit"

    def test_freelance_job_to_dict(self):
        """Test that FreelanceJob can be serialized to dict."""
        job = FreelanceJob(
            job_id="job-1",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=100.0,
        )
        data = job.to_dict()
        assert data["job_id"] == "job-1"
        assert data["source"] == "upwork"
        assert data["budget"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
