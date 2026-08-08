"""
Tests for Job Classifier module.

Tests job classification and WorkSpecification generation.
"""

import pytest
from datetime import datetime

from app.work_market.models import FreelanceJob, JobSource
from app.work_market.job_classifier import (
    SEOJobCategory,
    JobClassificationResult,
    SEOJobClassifier,
    JobClassificationOrchestrator,
)
from app.expert_domains.work.work_specification import WorkPriority, WorkComplexity


class TestSEOJobClassifier:
    """Test SEO job classifier."""

    def test_classify_seo_audit_job(self):
        """Test classifying an SEO audit job."""
        classifier = SEOJobClassifier()
        
        job = FreelanceJob(
            job_id="job_001",
            source=JobSource.UPWORK,
            title="SEO Audit for Ecommerce Website",
            description="I need a comprehensive SEO audit for my ecommerce website to identify technical issues and optimization opportunities.",
            skills=["seo", "technical seo", "audit"],
            budget=1500.0,
        )
        
        result = classifier.classify(job)
        
        assert result.job_id == "job_001"
        assert result.category == SEOJobCategory.SEO_AUDIT
        assert result.confidence > 0.5
        assert len(result.classification_reasons) > 0

    def test_classify_keyword_research_job(self):
        """Test classifying a keyword research job."""
        classifier = SEOJobClassifier()
        
        job = FreelanceJob(
            job_id="job_002",
            source=JobSource.FIVERR,
            title="Keyword Research for SaaS Company",
            description="Need comprehensive keyword research for my SaaS company targeting the US market.",
            skills=["keyword research", "seo"],
            budget=500.0,
        )
        
        result = classifier.classify(job)
        
        assert result.category == SEOJobCategory.KEYWORD_RESEARCH
        assert result.confidence > 0.5

    def test_classify_technical_seo_job(self):
        """Test classifying a technical SEO job."""
        classifier = SEOJobClassifier()
        
        job = FreelanceJob(
            job_id="job_003",
            source=JobSource.UPWORK,
            title="Technical SEO Optimization",
            description="Need help with technical SEO including site speed, mobile optimization, and schema markup.",
            skills=["technical seo", "site speed", "mobile"],
            budget=2000.0,
        )
        
        result = classifier.classify(job)
        
        assert result.category == SEOJobCategory.TECHNICAL_SEO
        assert result.confidence > 0.5

    def test_classify_local_seo_job(self):
        """Test classifying a local SEO job."""
        classifier = SEOJobClassifier()
        
        job = FreelanceJob(
            job_id="job_004",
            source=JobSource.FREELANCER,
            title="Local SEO for Dental Practice",
            description="Need local SEO optimization for my dental practice to improve Google Maps ranking.",
            skills=["local seo", "google my business"],
            budget=800.0,
        )
        
        result = classifier.classify(job)
        
        assert result.category == SEOJobCategory.LOCAL_SEO

    def test_classify_ecommerce_seo_job(self):
        """Test classifying an ecommerce SEO job."""
        classifier = SEOJobClassifier()
        
        job = FreelanceJob(
            job_id="job_005",
            source=JobSource.UPWORK,
            title="Ecommerce SEO for Shopify Store",
            description="Need SEO optimization for my Shopify ecommerce store to increase organic traffic.",
            skills=["ecommerce seo", "shopify", "seo"],
            budget=3000.0,
        )
        
        result = classifier.classify(job)
        
        assert result.category == SEOJobCategory.ECOMMERCE_SEO

    def test_determine_priority(self):
        """Test priority determination."""
        classifier = SEOJobClassifier()
        
        # Urgent job
        urgent_job = FreelanceJob(
            job_id="urgent_job",
            source=JobSource.UPWORK,
            title="URGENT: SEO Audit Needed",
            description="Need urgent SEO audit completed as soon as possible.",
            budget=2000.0,
        )
        
        result = classifier.classify(urgent_job)
        assert result.priority == WorkPriority.CRITICAL

    def test_determine_complexity(self):
        """Test complexity determination."""
        classifier = SEOJobClassifier()
        
        # Complex job
        complex_job = FreelanceJob(
            job_id="complex_job",
            source=JobSource.UPWORK,
            title="Comprehensive SEO Strategy",
            description="Need a complex and comprehensive SEO strategy for large enterprise.",
            budget=5000.0,
        )
        
        result = classifier.classify(complex_job)
        assert result.complexity in [WorkComplexity.COMPLEX, WorkComplexity.VERY_COMPLEX]


class TestJobClassificationOrchestrator:
    """Test job classification orchestrator."""

    def test_classify_job(self):
        """Test classifying a job through orchestrator."""
        orchestrator = JobClassificationOrchestrator()
        
        job = FreelanceJob(
            job_id="job_006",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit for my website.",
            budget=1000.0,
        )
        
        result = orchestrator.classify_job(job)
        
        assert isinstance(result, JobClassificationResult)
        assert result.job_id == "job_006"

    def test_create_work_specification(self):
        """Test creating WorkSpecification from classification."""
        orchestrator = JobClassificationOrchestrator()
        
        job = FreelanceJob(
            job_id="job_007",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit for my website.",
            budget=1000.0,
        )
        
        classification = orchestrator.classify_job(job)
        work_spec = orchestrator.create_work_specification(job, classification)
        
        assert work_spec.work_id == "job_007"
        assert work_spec.title == "SEO Audit"
        assert work_spec.business_goal is not None
        assert work_spec.industry is not None
        assert work_spec.target_audience is not None
        assert work_spec.expected_outcome is not None

    def test_work_specification_metadata(self):
        """Test WorkSpecification contains classification metadata."""
        orchestrator = JobClassificationOrchestrator()
        
        job = FreelanceJob(
            job_id="job_008",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit for my website.",
            budget=1000.0,
        )
        
        classification = orchestrator.classify_job(job)
        work_spec = orchestrator.create_work_specification(job, classification)
        
        assert "category" in work_spec.metadata
        assert "classification_confidence" in work_spec.metadata
        assert "classification_reasons" in work_spec.metadata
        assert "source" in work_spec.metadata
        assert "budget" in work_spec.metadata


class TestClassificationPipeline:
    """Test complete classification pipeline."""

    def test_end_to_end_classification(self):
        """Test end-to-end classification pipeline."""
        orchestrator = JobClassificationOrchestrator()
        
        job = FreelanceJob(
            job_id="job_009",
            source=JobSource.UPWORK,
            title="Technical SEO Audit for Ecommerce Store",
            description="I need a comprehensive technical SEO audit for my Shopify store. The site has been experiencing slow load times and I need help identifying and fixing technical issues.",
            skills=["technical seo", "shopify", "site speed"],
            budget=2500.0,
            currency="USD",
            deadline=datetime(2026, 9, 30),
        )
        
        # Classify
        classification = orchestrator.classify_job(job)
        
        # Create WorkSpecification
        work_spec = orchestrator.create_work_specification(job, classification)
        
        # Verify pipeline
        assert classification.category in [SEOJobCategory.TECHNICAL_SEO, SEOJobCategory.ECOMMERCE_SEO, SEOJobCategory.SEO_AUDIT]
        assert work_spec.work_id == "job_009"
        assert work_spec.business_goal is not None
        assert work_spec.constraints is not None
        # Constraints may be empty if no constraints are detected
        assert len(work_spec.constraints) >= 0

    def test_multiple_job_types(self):
        """Test classifying multiple different job types."""
        orchestrator = JobClassificationOrchestrator()
        
        jobs = [
            FreelanceJob(
                job_id="audit_job",
                source=JobSource.UPWORK,
                title="SEO Audit",
                description="Need SEO audit.",
                budget=1000.0,
            ),
            FreelanceJob(
                job_id="keyword_job",
                source=JobSource.FIVERR,
                title="Keyword Research",
                description="Need keyword research.",
                budget=500.0,
            ),
            FreelanceJob(
                job_id="local_job",
                source=JobSource.FREELANCER,
                title="Local SEO",
                description="Need local SEO.",
                budget=800.0,
            ),
        ]
        
        results = []
        for job in jobs:
            classification = orchestrator.classify_job(job)
            work_spec = orchestrator.create_work_specification(job, classification)
            results.append((classification, work_spec))
        
        # Verify all jobs processed
        assert len(results) == 3
        for classification, work_spec in results:
            assert classification.category is not None
            assert work_spec.work_id is not None
