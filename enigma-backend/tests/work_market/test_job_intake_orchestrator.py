"""
Tests for Job Intake Orchestrator.

Tests the complete job intake and normalization pipeline.
"""

import pytest

from app.work_market.job_intake_orchestrator import (
    JobIntakeOrchestrator,
    JobIntakeResult,
    job_intake_orchestrator,
)
from app.work_market.models import JobSource, JobRecommendation
from app.work_market.job_classifier import SEOJobClassifier
from app.work_market.job_analyzer import SEOJobAnalyzer
from app.work_market.job_readiness import (
    SEOJobReadinessCalculator,
    JobReadinessResult,
    KnowledgeReadinessAssessment,
    EvidenceReadinessAssessment,
    CapabilityReadinessAssessment,
    ExecutionReadinessAssessment,
    ExperienceReadinessAssessment,
)


class TestJobIntakeOrchestrator:
    """Test JobIntakeOrchestrator."""

    def test_ingest_seo_job(self):
        """Test ingesting an SEO job."""
        orchestrator = JobIntakeOrchestrator()
        
        raw_job = {
            "job_id": "job_001",
            "title": "Technical SEO Audit for E-commerce Site",
            "description": "Need a comprehensive technical SEO audit for my e-commerce website. Looking for analysis of site speed, mobile optimization, crawling issues, and recommendations.",
            "budget": 500.0,
            "currency": "USD",
            "skills": ["technical_seo", "site_speed", "mobile_optimization"],
            "source_url": "https://upwork.com/job/001",
        }
        
        result = orchestrator.ingest_job(raw_job, JobSource.UPWORK)
        
        # Check if failed and print errors for debugging
        if result.intake_status == "failed":
            print(f"Errors: {result.errors}")
        
        assert result.intake_status in ["success", "partial"]  # Allow partial success
        assert result.job_id == "job_001"
        assert result.normalized_job is not None

    def test_normalize_job_data(self):
        """Test job normalization."""
        orchestrator = JobIntakeOrchestrator()
        
        raw_job = {
            "title": "Test Job",
            "description": "Test description",
            "budget": 100.0,
            "skills": ["skill1", "skill2"],
        }
        
        normalized = orchestrator._normalize_job(raw_job, JobSource.OTHER)
        
        assert normalized.title == "Test Job"
        assert normalized.description == "Test description"
        assert normalized.budget == 100.0
        assert len(normalized.skills) == 2
        assert normalized.normalized_at is not None

    def test_extract_capabilities(self):
        """Test capability extraction."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.work_market.models import FreelanceJob
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.OTHER,
            title="SEO Audit",
            description="Technical SEO audit",
            skills=["technical_seo", "analytics"],
        )
        
        classification = {
            "profession": "seo_specialist",
            "task_type": "audit",
            "domain_id": "seo",
            "task_id": "audit",
        }
        
        capabilities = orchestrator._extract_capabilities(job, classification)
        
        assert "technical_seo" in capabilities
        assert "analytics" in capabilities
        assert "seo_specialist_expertise" in capabilities
        assert "audit_execution" in capabilities

    def test_create_work_specification(self):
        """Test work specification creation."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.work_market.models import FreelanceJob
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.OTHER,
            title="SEO Audit",
            description="Technical SEO audit",
            budget=500.0,
            skills=["technical_seo"],
        )
        
        classification = {
            "profession": "seo_specialist",
            "task_type": "audit",
            "domain_id": "seo",
            "task_id": "technical_seo_audit",
        }
        
        required_capabilities = ["technical_seo"]
        
        work_spec = orchestrator._create_work_specification(
            job,
            classification,
            required_capabilities,
        )
        
        assert work_spec.title == "SEO Audit"
        assert work_spec.description == "Technical SEO audit"
        assert len(work_spec.required_capabilities) > 0
        assert work_spec.required_tasks is not None
        assert work_spec.constraints is not None

    def test_extract_deliverables(self):
        """Test deliverable extraction."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.work_market.models import FreelanceJob
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.OTHER,
            title="SEO Audit",
            description="Need a comprehensive audit report and analysis document",
        )
        
        deliverables = orchestrator._extract_deliverables(job)
        
        assert "comprehensive_report" in deliverables
        assert "analysis_document" in deliverables

    def test_acceptance_criteria_extraction(self):
        """Test acceptance criteria extraction."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.work_market.models import FreelanceJob
        from datetime import datetime
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.OTHER,
            title="SEO Audit",
            description="Test",
            budget=500.0,
            deadline=datetime(2026, 12, 31),
            skills=["technical_seo"],
        )
        
        criteria = orchestrator._extract_acceptance_criteria(job)
        
        assert "within_budget_USD" in criteria
        assert "delivered_by_deadline" in criteria
        assert "skill_technical_seo" in criteria

    def test_execution_capability_evaluation(self):
        """Test execution capability evaluation."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.work_market.models import FreelanceJob
        from app.expert_domains.contracts import ReadinessScore
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.OTHER,
            title="SEO Audit",
            description="Test",
        )
        
        classification = {"profession": "seo"}
        required_capabilities = ["technical_seo"]
        
        readiness_result = JobReadinessResult(
            work_id="work_001",
            knowledge_readiness=KnowledgeReadinessAssessment(
                required_knowledge=["technical_seo"],
                available_knowledge=["technical_seo"],
                missing_knowledge=[],
                knowledge_coverage=1.0,
                knowledge_confidence=0.9,
            ),
            evidence_readiness=EvidenceReadinessAssessment(
                required_evidence=["audit_evidence"],
                available_evidence=["audit_evidence"],
                missing_evidence=[],
                evidence_coverage=1.0,
                evidence_quality=0.8,
            ),
            capability_readiness=CapabilityReadinessAssessment(
                required_capabilities=["technical_seo"],
                available_capabilities=["technical_seo"],
                missing_capabilities=[],
                capability_coverage=1.0,
            ),
            execution_readiness=ExecutionReadinessAssessment(
                required_tasks=["audit"],
                executable_tasks=["audit"],
                non_executable_tasks=[],
                execution_coverage=1.0,
                resource_availability="high",
                execution_complexity="moderate",
            ),
            experience_readiness=ExperienceReadinessAssessment(
                relevant_experience=["seo_audit"],
                experience_level="intermediate",
                similar_jobs_completed=5,
                success_rate=0.9,
            ),
            overall_readiness=ReadinessScore(
                domain_id="seo",
                knowledge_readiness=0.9,
                execution_readiness=0.8,
                evidence_readiness=0.85,
                learning_readiness=0.8,
                overall_readiness=0.85,
            ),
            confidence=0.85,
        )
        
        capability = orchestrator._evaluate_execution_capability(
            job,
            classification,
            required_capabilities,
            readiness_result,
        )
        
        assert capability["can_execute"] is True
        assert capability["confidence"] == 0.85
        assert capability["estimated_success_probability"] == 0.85
        assert capability["requires_learning"] is False
        assert capability["requires_research"] is False

    def test_recommendation_generation_apply(self):
        """Test recommendation generation for apply."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.expert_domains.contracts import ReadinessScore
        
        readiness_result = JobReadinessResult(
            work_id="work_001",
            knowledge_readiness=KnowledgeReadinessAssessment(
                required_knowledge=[],
                available_knowledge=[],
                missing_knowledge=[],
                knowledge_coverage=1.0,
                knowledge_confidence=0.9,
            ),
            evidence_readiness=EvidenceReadinessAssessment(
                required_evidence=[],
                available_evidence=[],
                missing_evidence=[],
                evidence_coverage=1.0,
                evidence_quality=0.8,
            ),
            capability_readiness=CapabilityReadinessAssessment(
                required_capabilities=[],
                available_capabilities=[],
                missing_capabilities=[],
                capability_coverage=1.0,
            ),
            execution_readiness=ExecutionReadinessAssessment(
                required_tasks=[],
                executable_tasks=[],
                non_executable_tasks=[],
                execution_coverage=1.0,
                resource_availability="high",
                execution_complexity="simple",
            ),
            experience_readiness=ExperienceReadinessAssessment(
                relevant_experience=[],
                experience_level="expert",
            ),
            overall_readiness=ReadinessScore(
                domain_id="seo",
                knowledge_readiness=0.9,
                execution_readiness=0.9,
                evidence_readiness=0.9,
                learning_readiness=0.9,
                overall_readiness=0.9,
            ),
            confidence=0.9,
        )
        
        execution_capability = {
            "blockers": [],
            "requires_learning": False,
            "requires_research": False,
        }
        
        recommendation = orchestrator._generate_recommendation(
            readiness_result,
            execution_capability,
            None,
        )
        
        assert recommendation == JobRecommendation.APPLY

    def test_recommendation_generation_learn_first(self):
        """Test recommendation generation for learn first."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.expert_domains.contracts import ReadinessScore
        
        readiness_result = JobReadinessResult(
            work_id="work_001",
            knowledge_readiness=KnowledgeReadinessAssessment(
                required_knowledge=["new_skill"],
                available_knowledge=[],
                missing_knowledge=["new_skill"],
                knowledge_coverage=0.0,
                knowledge_confidence=0.5,
            ),
            evidence_readiness=EvidenceReadinessAssessment(
                required_evidence=[],
                available_evidence=[],
                missing_evidence=[],
                evidence_coverage=1.0,
                evidence_quality=0.8,
            ),
            capability_readiness=CapabilityReadinessAssessment(
                required_capabilities=[],
                available_capabilities=[],
                missing_capabilities=[],
                capability_coverage=1.0,
            ),
            execution_readiness=ExecutionReadinessAssessment(
                required_tasks=[],
                executable_tasks=[],
                non_executable_tasks=[],
                execution_coverage=1.0,
                resource_availability="high",
                execution_complexity="simple",
            ),
            experience_readiness=ExperienceReadinessAssessment(
                relevant_experience=[],
                experience_level="beginner",
            ),
            overall_readiness=ReadinessScore(
                domain_id="seo",
                knowledge_readiness=0.5,
                execution_readiness=0.7,
                evidence_readiness=0.8,
                learning_readiness=0.6,
                overall_readiness=0.5,
            ),
            confidence=0.5,
        )
        
        execution_capability = {
            "blockers": [],
            "requires_learning": True,
            "requires_research": False,
        }
        
        recommendation = orchestrator._generate_recommendation(
            readiness_result,
            execution_capability,
            None,
        )
        
        assert recommendation == JobRecommendation.LEARN_FIRST

    def test_recommendation_generation_research_first(self):
        """Test recommendation generation for research first."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.expert_domains.contracts import ReadinessScore
        
        readiness_result = JobReadinessResult(
            work_id="work_001",
            knowledge_readiness=KnowledgeReadinessAssessment(
                required_knowledge=[],
                available_knowledge=[],
                missing_knowledge=[],
                knowledge_coverage=1.0,
                knowledge_confidence=0.9,
            ),
            evidence_readiness=EvidenceReadinessAssessment(
                required_evidence=["missing_evidence"],
                available_evidence=[],
                missing_evidence=["missing_evidence"],
                evidence_coverage=0.0,
                evidence_quality=0.5,
            ),
            capability_readiness=CapabilityReadinessAssessment(
                required_capabilities=[],
                available_capabilities=[],
                missing_capabilities=[],
                capability_coverage=1.0,
            ),
            execution_readiness=ExecutionReadinessAssessment(
                required_tasks=[],
                executable_tasks=[],
                non_executable_tasks=[],
                execution_coverage=1.0,
                resource_availability="high",
                execution_complexity="simple",
            ),
            experience_readiness=ExperienceReadinessAssessment(
                relevant_experience=[],
                experience_level="intermediate",
            ),
            overall_readiness=ReadinessScore(
                domain_id="seo",
                knowledge_readiness=0.9,
                execution_readiness=0.7,
                evidence_readiness=0.5,
                learning_readiness=0.8,
                overall_readiness=0.6,
            ),
            confidence=0.6,
        )
        
        execution_capability = {
            "blockers": [],
            "requires_learning": False,
            "requires_research": True,
        }
        
        recommendation = orchestrator._generate_recommendation(
            readiness_result,
            execution_capability,
            None,
        )
        
        assert recommendation == JobRecommendation.RESEARCH_FIRST

    def test_recommendation_generation_reject(self):
        """Test recommendation generation for reject."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.expert_domains.contracts import ReadinessScore
        
        readiness_result = JobReadinessResult(
            work_id="work_001",
            knowledge_readiness=KnowledgeReadinessAssessment(
                required_knowledge=[],
                available_knowledge=[],
                missing_knowledge=[],
                knowledge_coverage=1.0,
                knowledge_confidence=0.9,
            ),
            evidence_readiness=EvidenceReadinessAssessment(
                required_evidence=[],
                available_evidence=[],
                missing_evidence=[],
                evidence_coverage=1.0,
                evidence_quality=0.8,
            ),
            capability_readiness=CapabilityReadinessAssessment(
                required_capabilities=[],
                available_capabilities=[],
                missing_capabilities=[],
                capability_coverage=1.0,
            ),
            execution_readiness=ExecutionReadinessAssessment(
                required_tasks=[],
                executable_tasks=[],
                non_executable_tasks=[],
                execution_coverage=1.0,
                resource_availability="high",
                execution_complexity="simple",
            ),
            experience_readiness=ExperienceReadinessAssessment(
                relevant_experience=[],
                experience_level="beginner",
            ),
            overall_readiness=ReadinessScore(
                domain_id="seo",
                knowledge_readiness=0.5,
                execution_readiness=0.4,
                evidence_readiness=0.5,
                learning_readiness=0.4,
                overall_readiness=0.4,
            ),
            confidence=0.4,
            blockers=["insufficient_experience"],
        )
        
        execution_capability = {
            "blockers": ["insufficient_experience"],
            "requires_learning": False,
            "requires_research": False,
        }
        
        recommendation = orchestrator._generate_recommendation(
            readiness_result,
            execution_capability,
            None,
        )
        
        assert recommendation == JobRecommendation.REJECT

    def test_global_orchestrator_instance(self):
        """Test that global orchestrator instance exists."""
        from app.work_market.job_intake_orchestrator import job_intake_orchestrator
        
        assert job_intake_orchestrator is not None
        assert isinstance(job_intake_orchestrator, JobIntakeOrchestrator)

    def test_ingest_job_with_missing_fields(self):
        """Test ingesting job with missing optional fields."""
        orchestrator = JobIntakeOrchestrator()
        
        raw_job = {
            "title": "Simple Job",
            "description": "Simple description",
        }
        
        result = orchestrator.ingest_job(raw_job, JobSource.OTHER)
        
        # Should still succeed with defaults
        assert result.intake_status == "success"
        assert result.normalized_job is not None
        assert result.normalized_job.budget is None
        assert result.normalized_job.skills == []

    def test_duration_estimation(self):
        """Test duration estimation based on job."""
        orchestrator = JobIntakeOrchestrator()
        
        from app.work_market.models import FreelanceJob
        
        # High budget job
        high_budget_job = FreelanceJob(
            job_id="job_001",
            source=JobSource.OTHER,
            title="High Budget Job",
            description="Test",
            budget=1500.0,
        )
        
        duration = orchestrator._estimate_duration(high_budget_job)
        assert duration == 40.0
        
        # Low budget job
        low_budget_job = FreelanceJob(
            job_id="job_002",
            source=JobSource.OTHER,
            title="Low Budget Job",
            description="Test",
            budget=50.0,
        )
        
        duration = orchestrator._estimate_duration(low_budget_job)
        assert duration == 4.0
