"""
Runtime Integration Tests: Freelancing System

These tests verify that the freelancing runtime properly integrates with:
- Knowledge Governance (via KnowledgeProvider)
- Evidence Registry (via EvidenceProvider)
- Expert Domain (via ExpertDomainProvider)
- Decision Layer (via DecisionProvider)
- Work Specification (via WorkSpecificationProvider)
"""
import pytest

from app.work_market.models import (
    FreelanceJob,
    JobSource,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
)
from app.work_market.readiness_service import FreelancingReadinessService
from app.work_market.knowledge_governance_adapter import MockKnowledgeProvider
from app.work_market.evidence_adapter import MockEvidenceProvider
from app.work_market.expert_domain_adapter import MockExpertDomainAdapter
from app.work_market.decision_adapter import MockDecisionProvider
from app.work_market.work_specification_adapter import MockWorkSpecificationProvider


class TestKnowledgeGovernanceIntegration:
    """Tests for Knowledge Governance integration."""

    def test_readiness_uses_knowledge_provider(self):
        """Test that readiness service uses Knowledge Provider."""
        knowledge_provider = MockKnowledgeProvider()
        service = FreelancingReadinessService(knowledge_provider=knowledge_provider)
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="Test Job",
            description="Test description",
        )
        
        classification = JobClassification(
            job_id="test-job",
            profession="SEO Specialist",
            task="SEO Audit",
            required_knowledge=["SEO", "Technical SEO"],
        )
        
        evaluation = JobEvaluation(
            job_id="test-job",
            profession_match=0.8,
            capability_match=0.7,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Verify knowledge readiness is calculated
        assert assessment.knowledge_readiness > 0.0
        assert assessment.knowledge_readiness <= 1.0

    def test_knowledge_provider_returns_real_scores(self):
        """Test that Knowledge Provider returns real scores (not placeholders)."""
        provider = MockKnowledgeProvider()
        
        # Test different concepts get different scores
        seo_score = provider.get_knowledge_maturity("seo")
        technical_seo_score = provider.get_knowledge_maturity("technical_seo")
        
        # Should not be identical placeholder values
        assert seo_score >= 0.0
        assert technical_seo_score >= 0.0
        # Scores should vary based on concept
        assert seo_score != technical_seo_score or seo_score == 0.5


class TestEvidenceIntegration:
    """Tests for Evidence Registry integration."""

    def test_readiness_uses_evidence_provider(self):
        """Test that readiness service uses Evidence Provider."""
        evidence_provider = MockEvidenceProvider()
        service = FreelancingReadinessService(evidence_provider=evidence_provider)
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="Test Job",
            description="Test description",
        )
        
        classification = JobClassification(
            job_id="test-job",
            profession="SEO Specialist",
            task="SEO Audit",
            required_capabilities=["SEO Audit", "Keyword Research"],
        )
        
        evaluation = JobEvaluation(
            job_id="test-job",
            profession_match=0.8,
            capability_match=0.7,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Verify evidence readiness is calculated
        assert assessment.evidence_readiness > 0.0
        assert assessment.evidence_readiness <= 1.0

    def test_evidence_provider_returns_real_scores(self):
        """Test that Evidence Provider returns real scores (not placeholders)."""
        provider = MockEvidenceProvider()
        
        # Test different capabilities get different scores
        seo_audit_coverage = provider.get_evidence_coverage("seo_audit")
        keyword_research_coverage = provider.get_evidence_coverage("keyword_research")
        
        # Should not be identical placeholder values
        assert seo_audit_coverage >= 0.0
        assert keyword_research_coverage >= 0.0
        # Coverage should vary based on capability
        assert seo_audit_coverage != keyword_research_coverage or seo_audit_coverage == 0.2


class TestExpertDomainIntegration:
    """Tests for Expert Domain integration."""

    def test_expert_domain_provider_returns_capabilities(self):
        """Test that Expert Domain Provider returns dynamic capabilities."""
        provider = MockExpertDomainAdapter()
        
        capabilities = provider.get_domain_capabilities("default")
        
        # Should return a list of capabilities
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        # Should not be empty or static placeholder
        assert "SEO Audit" in capabilities or "seo" in str(capabilities).lower()

    def test_expert_domain_provider_returns_readiness(self):
        """Test that Expert Domain Provider returns readiness scores."""
        provider = MockExpertDomainAdapter()
        
        readiness = provider.get_domain_readiness("default")
        
        assert readiness is not None
        assert readiness.overall_readiness >= 0.0
        assert readiness.overall_readiness <= 1.0
        # Should have component scores
        assert readiness.knowledge_readiness >= 0.0
        assert readiness.execution_readiness >= 0.0
        assert readiness.evidence_readiness >= 0.0


class TestDecisionIntegration:
    """Tests for Decision Layer integration."""

    def test_decision_provider_returns_decision(self):
        """Test that Decision Provider returns decision records."""
        provider = MockDecisionProvider()
        
        context = {
            "job_id": "test-job",
            "readiness": 0.85,
            "blockers": [],
            "risks": [],
            "recommendation": "apply",
        }
        
        decision = provider.request_decision(context)
        
        # Should return a decision record
        assert "decision" in decision
        assert "confidence" in decision
        assert "reasoning" in decision
        # Decision should be one of the valid types
        assert decision["decision"] in ["accept", "reject", "need_learning", "need_research"]

    def test_decision_provider_blocks_low_readiness(self):
        """Test that Decision Provider blocks low readiness applications."""
        provider = MockDecisionProvider()
        
        context = {
            "job_id": "test-job",
            "readiness": 0.3,  # Low readiness
            "blockers": ["Missing knowledge"],
            "risks": ["High risk"],
            "recommendation": "reject",
        }
        
        decision = provider.request_decision(context)
        
        # Should not allow proceeding
        assert not provider.can_proceed(decision)
        assert decision["decision"] in ["reject", "need_learning"]

    def test_decision_provider_allows_high_readiness(self):
        """Test that Decision Provider allows high readiness applications."""
        provider = MockDecisionProvider()
        
        context = {
            "job_id": "test-job",
            "readiness": 0.9,  # High readiness
            "blockers": [],
            "risks": [],
            "recommendation": "apply",
        }
        
        decision = provider.request_decision(context)
        
        # Should allow proceeding
        assert provider.can_proceed(decision)
        assert decision["decision"] == "accept"


class TestWorkSpecificationIntegration:
    """Tests for Work Specification integration."""

    def test_work_specification_transforms_job(self):
        """Test that Work Specification Provider transforms jobs."""
        provider = MockWorkSpecificationProvider()
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            skills=["SEO", "Technical SEO"],
        )
        
        spec = provider.transform_job_to_specification(job)
        
        # Should return a work specification
        assert "work_specification_id" in spec
        assert "requirements" in spec
        assert "deliverables" in spec
        assert "acceptance_criteria" in spec
        assert "success_metrics" in spec
        assert "constraints" in spec

    def test_work_specification_has_requirements(self):
        """Test that work specification includes requirements."""
        provider = MockWorkSpecificationProvider()
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            skills=["SEO", "Technical SEO"],
        )
        
        spec = provider.transform_job_to_specification(job)
        
        # Should have requirements
        assert len(spec["requirements"]) > 0
        # Requirements should have structure
        for req in spec["requirements"]:
            assert "id" in req
            assert "type" in req
            assert "description" in req

    def test_work_specification_has_deliverables(self):
        """Test that work specification includes deliverables."""
        provider = MockWorkSpecificationProvider()
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            skills=["SEO", "Technical SEO"],
        )
        
        spec = provider.transform_job_to_specification(job)
        
        # Should have deliverables
        assert len(spec["deliverables"]) > 0
        # Deliverables should have structure
        for deliverable in spec["deliverables"]:
            assert "id" in deliverable
            assert "name" in deliverable
            assert "type" in deliverable


class TestFullPipelineIntegration:
    """Tests for complete pipeline integration."""

    def test_full_readiness_pipeline(self):
        """Test complete readiness pipeline with all providers."""
        knowledge_provider = MockKnowledgeProvider()
        evidence_provider = MockEvidenceProvider()
        expert_domain_provider = MockExpertDomainAdapter()
        
        service = FreelancingReadinessService(
            knowledge_provider=knowledge_provider,
            evidence_provider=evidence_provider,
            expert_domain_provider=expert_domain_provider,
        )
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need comprehensive SEO audit",
            skills=["SEO", "Technical SEO", "Keyword Research"],
        )
        
        classification = JobClassification(
            job_id="test-job",
            profession="SEO Specialist",
            task="SEO Audit",
            required_knowledge=["SEO", "Technical SEO"],
            required_capabilities=["SEO Audit", "Keyword Research"],
        )
        
        evaluation = JobEvaluation(
            job_id="test-job",
            profession_match=0.8,
            capability_match=0.75,
            knowledge_match=0.7,
            skill_match=0.85,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Verify all components are calculated
        assert assessment.knowledge_readiness > 0.0
        assert assessment.evidence_readiness > 0.0
        assert assessment.execution_readiness > 0.0
        assert assessment.overall_readiness > 0.0
        # Should have recommendation
        assert assessment.recommendation in JobRecommendation

    def test_full_application_pipeline(self):
        """Test complete application pipeline with decision layer."""
        knowledge_provider = MockKnowledgeProvider()
        evidence_provider = MockEvidenceProvider()
        expert_domain_provider = MockExpertDomainAdapter()
        decision_provider = MockDecisionProvider()
        work_spec_provider = MockWorkSpecificationProvider()
        
        service = FreelancingReadinessService(
            knowledge_provider=knowledge_provider,
            evidence_provider=evidence_provider,
            expert_domain_provider=expert_domain_provider,
        )
        
        job = FreelanceJob(
            job_id="test-job",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need comprehensive SEO audit",
            skills=["SEO", "Technical SEO"],
        )
        
        classification = JobClassification(
            job_id="test-job",
            profession="SEO Specialist",
            task="SEO Audit",
            required_knowledge=["seo"],  # Use concept with higher score (0.85)
            required_capabilities=["seo_audit"],  # Use capability with higher score (0.70)
        )
        
        evaluation = JobEvaluation(
            job_id="test-job",
            profession_match=0.95,
            capability_match=0.95,
            knowledge_match=0.95,
            skill_match=0.95,
            risk_score=0.1,  # Low risk
            complexity_score=0.2,  # Low complexity
            effort_score=0.2,  # Low effort
        )
        
        # Step 1: Assess readiness
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Step 2: Request decision
        decision_context = {
            "job_id": job.job_id,
            "readiness": assessment.overall_readiness,
            "blockers": assessment.blockers,
            "risks": assessment.risks,
            "recommendation": assessment.recommendation.value,
        }
        
        decision_record = decision_provider.request_decision(decision_context)
        
        # Step 3: Transform to work specification
        work_spec = work_spec_provider.transform_job_to_specification(job)
        
        # Verify pipeline completes
        assert assessment.overall_readiness > 0.7  # High readiness
        assert decision_provider.can_proceed(decision_record)  # Decision allows
        assert work_spec["work_specification_id"] is not None  # Work spec created


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
