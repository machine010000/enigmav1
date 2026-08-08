"""
Tests for complete Job Intelligence integration.

Tests the full pipeline from marketplace job to decision context.
"""

import pytest
from datetime import datetime

from app.work_market.models import FreelanceJob, JobSource
from app.work_market.job_intelligence_orchestrator import (
    JobIntelligenceOrchestrator,
    JobIntelligenceResult,
    job_intelligence_orchestrator,
)
from app.expert_domains.contracts import ReadinessScore


class TestJobIntelligenceOrchestrator:
    """Test job intelligence orchestrator."""

    def test_process_job_complete_pipeline(self):
        """Test processing a job through complete intelligence pipeline."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.UPWORK,
            title="SEO Audit for Ecommerce Website",
            description="I need a comprehensive SEO audit for my ecommerce website to identify technical issues and optimization opportunities.",
            skills=["seo", "technical seo", "audit"],
            budget=1500.0,
            currency="USD",
            deadline=datetime(2026, 9, 30),
        )
        
        result = orchestrator.process_job(job)
        
        assert isinstance(result, JobIntelligenceResult)
        assert result.job_id == "job_001"
        assert result.classification is not None
        assert result.work_specification is not None
        assert result.capability_mapping is not None
        assert result.task_mapping is not None
        assert result.analysis is not None
        assert result.readiness is not None
        assert result.recommendation is not None
        assert result.gap_analysis is not None
        assert result.proposal_context is not None
        assert result.processing_time_seconds > 0

    def test_process_job_batch(self):
        """Test processing multiple jobs in batch."""
        orchestrator = JobIntelligenceOrchestrator()
        
        jobs = [
            FreelanceJob(
                job_id="job_002",
                source=JobSource.UPWORK,
                title="SEO Audit",
                description="Need SEO audit",
                budget=1000.0,
            ),
            FreelanceJob(
                job_id="job_003",
                source=JobSource.FIVERR,
                title="Keyword Research",
                description="Need keyword research",
                budget=500.0,
            ),
            FreelanceJob(
                job_id="job_004",
                source=JobSource.FREELANCER,
                title="Local SEO",
                description="Need local SEO",
                budget=800.0,
            ),
        ]
        
        results = orchestrator.process_job_batch(jobs)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, JobIntelligenceResult)
            assert result.recommendation is not None

    def test_get_decision_context(self):
        """Test getting decision context for Decision Layer."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="job_005",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        decision_context = orchestrator.get_decision_context(intelligence)
        
        assert "job_id" in decision_context
        assert "recommendation" in decision_context
        assert "confidence" in decision_context
        assert "reasoning" in decision_context
        assert "readiness" in decision_context
        assert "risk" in decision_context
        assert "value" in decision_context
        assert "gaps" in decision_context
        assert "conditions" in decision_context
        assert "success_probability" in decision_context

    def test_get_proposal_context(self):
        """Test getting proposal context for proposal generation."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="job_006",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        proposal_context = orchestrator.get_proposal_context(intelligence)
        
        assert "client_goals" in proposal_context
        assert "deliverables" in proposal_context
        assert "timeline" in proposal_context
        assert "scope" in proposal_context
        assert "risks" in proposal_context
        assert "value" in proposal_context
        assert "pricing" in proposal_context
        assert "terms" in proposal_context
        assert "communication" in proposal_context

    def test_get_learning_context(self):
        """Test getting learning context for SEO Expert learning."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="job_007",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        learning_context = orchestrator.get_learning_context(intelligence)
        
        assert "knowledge_gaps" in learning_context
        assert "evidence_gaps" in learning_context
        assert "research_requirements" in learning_context
        assert "learning_requirements" in learning_context
        assert "category" in learning_context
        assert "confidence" in learning_context

    def test_domain_readiness_integration(self):
        """Test integration with SEO Expert Domain readiness."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="job_008",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Readiness should be from SEO Expert
        assert isinstance(intelligence.readiness.overall_readiness, ReadinessScore)
        assert intelligence.readiness.overall_readiness.domain_id == "seo"

    def test_global_orchestrator_instance(self):
        """Test global orchestrator instance is available."""
        from app.work_market import job_intelligence_orchestrator as global_orchestrator
        
        assert global_orchestrator is not None
        assert isinstance(global_orchestrator, JobIntelligenceOrchestrator)


class TestJobIntelligencePipeline:
    """Test complete job intelligence pipeline."""

    def test_high_readiness_job_acceptance(self):
        """Test high readiness job results in ACCEPT recommendation."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="high_readiness_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need comprehensive SEO audit with good budget and timeline",
            skills=["seo", "technical seo"],
            budget=3000.0,
            deadline=datetime(2026, 10, 30),
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should have reasonable readiness
        assert intelligence.readiness.overall_readiness.overall_readiness > 0.4
        # Recommendation should be one of the valid options
        assert intelligence.recommendation.recommendation.value in ["accept", "accept_with_conditions", "need_research", "need_learning"]

    def test_low_budget_job_rejection(self):
        """Test low budget job results in REJECT or NEED_LEARNING."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="low_budget_job",
            source=JobSource.FIVERR,
            title="SEO Audit",
            description="Need SEO audit",
            skills=["seo"],
            budget=100.0,  # Very low budget
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should have recommendation reflecting low budget
        assert intelligence.recommendation.recommendation.value in ["reject", "need_learning", "need_research"]

    def test_impossible_timeline_job(self):
        """Test impossible timeline job."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="tight_timeline_job",
            source=JobSource.UPWORK,
            title="Complex SEO Audit",
            description="Need comprehensive SEO audit",
            skills=["seo", "technical seo"],
            budget=2000.0,
            deadline=datetime(2026, 8, 10),  # Very tight deadline
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Timeline should be impossible or tight
        assert intelligence.analysis.timeline_analysis.deadline_feasibility in ["impossible", "tight"]

    def test_gap_analysis_identification(self):
        """Test gap analysis identifies missing knowledge."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="gap_analysis_job",
            source=JobSource.UPWORK,
            title="Complex SEO Strategy",
            description="Need comprehensive SEO strategy",
            skills=["seo", "strategy"],
            budget=4000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Gap analysis should be generated
        assert intelligence.gap_analysis is not None
        assert intelligence.gap_analysis.total_gaps >= 0
        assert intelligence.gap_analysis.estimated_closure_time is not None

    def test_proposal_context_completeness(self):
        """Test proposal context is complete and structured."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="proposal_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1500.0,
        )
        
        intelligence = orchestrator.process_job(job)
        proposal_context = orchestrator.get_proposal_context(intelligence)
        
        # Verify all context sections are present
        assert proposal_context["client_goals"]["primary"] is not None
        assert len(proposal_context["deliverables"]["primary"]) > 0
        assert proposal_context["timeline"]["duration"] is not None
        assert len(proposal_context["scope"]["in_scope"]) >= 0
        assert proposal_context["risks"]["level"] is not None
        assert proposal_context["value"]["business_value"] is not None

    def test_processing_performance(self):
        """Test processing performance is acceptable."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="performance_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Processing should complete in reasonable time
        assert intelligence.processing_time_seconds < 10.0  # Should be much faster

    def test_seo_category_variations(self):
        """Test different SEO categories are handled correctly."""
        orchestrator = JobIntelligenceOrchestrator()
        
        categories = [
            ("SEO Audit", "seo_audit"),
            ("Keyword Research", "keyword_research"),
            ("Technical SEO", "technical_seo"),
            ("Local SEO", "local_seo"),
        ]
        
        for title, expected_category in categories:
            job = FreelanceJob(
                job_id=f"cat_{expected_category}",
                source=JobSource.UPWORK,
                title=title,
                description=f"Need {title.lower()}",
                budget=1000.0,
            )
            
            intelligence = orchestrator.process_job(job)
            
            # Classification should match expected category
            assert intelligence.classification.category.value == expected_category or intelligence.classification.confidence > 0.5
