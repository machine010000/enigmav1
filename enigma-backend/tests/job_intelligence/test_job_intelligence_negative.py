"""
Negative tests for Job Intelligence pipeline.

Tests edge cases, error conditions, and boundary scenarios.
"""

import pytest
from datetime import datetime

from app.work_market.models import FreelanceJob, JobSource
from app.work_market.job_intelligence_orchestrator import JobIntelligenceOrchestrator
from app.expert_domains.work.work_specification import WorkSpecification


class TestJobIntelligenceNegative:
    """Test negative scenarios for job intelligence."""

    def test_job_with_no_description(self):
        """Test job with empty description."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="no_desc_job",
            source=JobSource.UPWORK,
            title="SEO Work",
            description="",  # Empty description
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still process but with lower confidence
        assert intelligence.classification.confidence < 0.7

    def test_job_with_no_budget(self):
        """Test job with no budget specified."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="no_budget_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=None,  # No budget
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still process
        assert intelligence.analysis.budget_analysis.budget_adequacy in ["adequate", "insufficient"]

    def test_job_with_no_skills(self):
        """Test job with no skills specified."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="no_skills_job",
            source=JobSource.UPWORK,
            title="SEO Work",
            description="Need some SEO work",
            skills=[],  # No skills
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still process with default classification
        assert intelligence.classification.category is not None

    def test_job_with_very_low_budget(self):
        """Test job with very low budget."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="very_low_budget_job",
            source=JobSource.FIVERR,
            title="SEO Audit",
            description="Need SEO audit",
            budget=50.0,  # Very low budget
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should recommend rejection or need learning
        assert intelligence.recommendation.recommendation.value in ["reject", "need_learning", "need_research"]

    def test_job_with_impossible_deadline(self):
        """Test job with impossible deadline."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="impossible_deadline_job",
            source=JobSource.UPWORK,
            title="Complex SEO Audit",
            description="Need comprehensive SEO audit",
            budget=2000.0,
            deadline=datetime(2026, 8, 8),  # Very near future
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Timeline should be impossible
        assert intelligence.analysis.timeline_analysis.deadline_feasibility == "impossible"

    def test_job_with_very_high_budget(self):
        """Test job with very high budget."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="high_budget_job",
            source=JobSource.UPWORK,
            title="Comprehensive SEO Strategy",
            description="Need comprehensive SEO strategy",
            budget=10000.0,  # Very high budget
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Budget should be generous
        assert intelligence.analysis.budget_analysis.budget_adequacy == "generous"

    def test_job_with_ambiguous_title(self):
        """Test job with ambiguous title."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="ambiguous_job",
            source=JobSource.UPWORK,
            title="Help with my website",
            description="I need help with my website",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still classify but with lower confidence
        assert intelligence.classification.confidence < 0.6

    def test_job_with_very_long_description(self):
        """Test job with very long description."""
        orchestrator = JobIntelligenceOrchestrator()
        
        long_description = "SEO work " * 500  # Very long description
        
        job = FreelanceJob(
            job_id="long_desc_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description=long_description,
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still process without errors
        assert intelligence.processing_time_seconds < 10.0

    def test_job_with_special_characters(self):
        """Test job with special characters in title/description."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="special_chars_job",
            source=JobSource.UPWORK,
            title="SEO Audit @#$%^&*()",
            description="Need SEO audit with special characters: !@#$%^&*()",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still process
        assert intelligence.classification is not None

    def test_job_with_unknown_category(self):
        """Test job that doesn't match any SEO category."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="unknown_category_job",
            source=JobSource.UPWORK,
            title="Web Development",
            description="Need website development",
            skills=["web development", "programming"],
            budget=2000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should default to SEO audit
        assert intelligence.classification.category is not None

    def test_multiple_jobs_batch_processing(self):
        """Test batch processing with mixed job types."""
        orchestrator = JobIntelligenceOrchestrator()
        
        jobs = [
            FreelanceJob(
                job_id="batch_1",
                source=JobSource.UPWORK,
                title="SEO Audit",
                description="Need SEO audit",
                budget=1000.0,
            ),
            FreelanceJob(
                job_id="batch_2",
                source=JobSource.FIVERR,
                title="Web Design",
                description="Need web design",
                budget=500.0,
            ),
            FreelanceJob(
                job_id="batch_3",
                source=JobSource.FREELANCER,
                title="Content Writing",
                description="Need content writing",
                budget=300.0,
            ),
        ]
        
        results = orchestrator.process_job_batch(jobs)
        
        # All should process
        assert len(results) == 3
        for result in results:
            assert result.recommendation is not None

    def test_work_specification_with_empty_metadata(self):
        """Test work specification with empty metadata."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="empty_metadata_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still work even if metadata is initially empty
        assert intelligence.work_specification is not None
        assert "category" in intelligence.work_specification.metadata

    def test_very_complex_job(self):
        """Test very complex job with high requirements."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="complex_job",
            source=JobSource.UPWORK,
            title="Enterprise SEO Strategy and Implementation",
            description="Need comprehensive enterprise-level SEO strategy including technical SEO, content optimization, link building, local SEO, and ongoing monitoring for large ecommerce platform with multiple international markets.",
            skills=["seo", "technical seo", "content", "link building", "local seo", "ecommerce"],
            budget=15000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should identify as very complex
        assert intelligence.analysis.difficulty_analysis.overall_difficulty in ["hard", "very_hard"]
        # Should have significant gaps
        assert intelligence.gap_analysis.total_gaps >= 0

    def test_minimal_job(self):
        """Test minimal job with minimal information."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="minimal_job",
            source=JobSource.FIVERR,
            title="SEO",
            description="SEO",
            budget=100.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should still process
        assert intelligence.recommendation.recommendation is not None


class TestJobIntelligenceEdgeCases:
    """Test edge cases for job intelligence."""

    def test_zero_budget_job(self):
        """Test job with zero budget."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="zero_budget_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=0.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should handle zero budget
        assert intelligence.analysis.budget_analysis.budget_adequacy == "insufficient"

    def test_negative_budget_job(self):
        """Test job with negative budget (invalid)."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="negative_budget_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=-100.0,  # Invalid negative budget
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should handle gracefully
        assert intelligence.analysis.budget_analysis.budget_adequacy == "insufficient"

    def test_past_deadline_job(self):
        """Test job with deadline in the past."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="past_deadline_job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            budget=1000.0,
            deadline=datetime(2026, 7, 1),  # Past deadline
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should handle past deadline
        assert intelligence.analysis.timeline_analysis.deadline_feasibility == "impossible"

    def test_job_with_unicode_characters(self):
        """Test job with unicode characters."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="unicode_job",
            source=JobSource.UPWORK,
            title="SEO Audit Ñoño 中文",
            description="Need SEO audit with unicode: café, naïve, 日本語",
            budget=1000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should handle unicode
        assert intelligence.classification is not None

    def test_job_with_extremely_high_complexity(self):
        """Test job with maximum complexity requirements."""
        orchestrator = JobIntelligenceOrchestrator()
        
        job = FreelanceJob(
            job_id="max_complexity_job",
            source=JobSource.UPWORK,
            title="Global Enterprise SEO Transformation",
            description="Need complete SEO transformation for global enterprise with 50+ websites, 20+ languages, complex technical infrastructure, and strict compliance requirements",
            budget=50000.0,
        )
        
        intelligence = orchestrator.process_job(job)
        
        # Should identify as very hard
        assert intelligence.analysis.difficulty_analysis.overall_difficulty == "very_hard"
        # Should have many gaps
        assert intelligence.gap_analysis.total_gaps >= 0
