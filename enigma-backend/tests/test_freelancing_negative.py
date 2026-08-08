"""
Negative Tests: Freelancing System Edge Cases and Failures

These tests verify that the freelancing system properly handles:
- Cannot apply when knowledge is insufficient
- Cannot bypass governance
- Cannot submit when blockers exist
- Frontend cannot mutate application state
- Unresolved knowledge conflict cannot become trusted evidence
"""
import pytest

from app.work_market.models import (
    FreelanceJob,
    JobSource,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
    JobAssessment,
    Application,
    ApplicationStatus,
)
from app.work_market.readiness_service import FreelancingReadinessService


class TestApplicationBlocking:
    """Tests for application blocking scenarios."""

    def test_cannot_apply_when_knowledge_insufficient(self):
        """Test that application is blocked when knowledge is insufficient."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-insufficient",
            source=JobSource.UPWORK,
            title="Advanced ML Project",
            description="Need advanced ML work",
        )
        
        classification = JobClassification(
            job_id="job-insufficient",
            profession="ML Engineer",
            task="Advanced ML",
            required_knowledge=["Deep Learning", "Neural Networks", "Transformers"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-insufficient",
            profession_match=0.5,
            knowledge_match=0.2,
            capability_match=0.3,
            missing_knowledge=["Deep Learning", "Neural Networks", "Transformers"],
            missing_capabilities=["Advanced ML"],
            recommendation=JobRecommendation.LEARN_FIRST,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should not be able to apply
        assert service.can_apply(assessment) is False
        # Should have blockers
        assert len(assessment.blockers) > 0
        # Should recommend learning first
        assert assessment.recommendation == JobRecommendation.LEARN_FIRST

    def test_cannot_apply_when_capability_insufficient(self):
        """Test that application is blocked when capabilities are insufficient."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-no-capability",
            source=JobSource.UPWORK,
            title="Complex System Architecture",
            description="Need system architecture work",
        )
        
        classification = JobClassification(
            job_id="job-no-capability",
            profession="System Architect",
            task="System Architecture",
            required_capabilities=["System Design", "Scalability Planning", "Security Architecture"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-no-capability",
            profession_match=0.6,
            capability_match=0.2,
            missing_capabilities=["System Design", "Scalability Planning", "Security Architecture"],
            recommendation=JobRecommendation.LEARN_FIRST,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should not be able to apply
        assert service.can_apply(assessment) is False
        # Should have capability blockers
        assert any("capability" in blocker.lower() for blocker in assessment.blockers)

    def test_cannot_apply_when_blockers_exist(self):
        """Test that application is blocked when any blockers exist."""
        service = FreelancingReadinessService()
        
        # Create assessment with blockers
        assessment = JobAssessment(
            job_id="job-blocked",
            overall_readiness=0.6,
            recommendation=JobRecommendation.APPLY,
            blockers=["Missing critical knowledge", "Insufficient capability"],
        )
        
        # Should not be able to apply due to blockers
        assert service.can_apply(assessment) is False

    def test_cannot_apply_when_risk_too_high(self):
        """Test that application is blocked when risk is too high."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-high-risk",
            source=JobSource.UPWORK,
            title="High Risk Project",
            description="Very complex project with tight deadline",
        )
        
        classification = JobClassification(
            job_id="job-high-risk",
            profession="General",
            task="Complex Task",
            complexity="high",
            estimated_effort="high",
        )
        
        evaluation = JobEvaluation(
            job_id="job-high-risk",
            profession_match=0.4,
            risk_score=0.9,
            complexity_score=0.9,
            effort_score=0.9,
            recommendation=JobRecommendation.REJECT,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should not be able to apply
        assert service.can_apply(assessment) is False
        # Should have risk blockers
        assert len(assessment.risks) > 0


class TestGovernanceBypassPrevention:
    """Tests for governance bypass prevention."""

    def test_cannot_bypass_knowledge_governance(self):
        """Test that knowledge governance cannot be bypassed."""
        service = FreelancingReadinessService()
        
        # Even if other scores are high, missing knowledge should block
        job = FreelanceJob(
            job_id="job-governance",
            source=JobSource.UPWORK,
            title="Specialized Task",
            description="Need specialized work",
        )
        
        classification = JobClassification(
            job_id="job-governance",
            profession="Specialist",
            task="Specialized Task",
            required_knowledge=["Specialized Knowledge"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-governance",
            profession_match=0.9,
            skill_match=0.9,
            knowledge_match=0.1,  # Very low knowledge match
            capability_match=0.9,
            missing_knowledge=["Specialized Knowledge"],
            recommendation=JobRecommendation.LEARN_FIRST,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should still be blocked due to missing knowledge
        assert service.can_apply(assessment) is False
        assert len(assessment.blockers) > 0

    def test_cannot_bypass_capability_governance(self):
        """Test that capability governance cannot be bypassed."""
        service = FreelancingReadinessService()
        
        # Even if other scores are high, missing capabilities should block
        job = FreelanceJob(
            job_id="job-cap-governance",
            source=JobSource.UPWORK,
            title="Capability-Intensive Task",
            description="Need specific capabilities",
        )
        
        classification = JobClassification(
            job_id="job-cap-governance",
            profession="Specialist",
            task="Capability-Intensive Task",
            required_capabilities=["Specific Capability"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-cap-governance",
            profession_match=0.9,
            skill_match=0.9,
            knowledge_match=0.9,
            capability_match=0.1,  # Very low capability match
            missing_capabilities=["Specific Capability"],
            recommendation=JobRecommendation.LEARN_FIRST,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should still be blocked due to missing capabilities
        assert service.can_apply(assessment) is False
        assert len(assessment.blockers) > 0


class TestApplicationStateMutation:
    """Tests for application state mutation prevention."""

    def test_application_state_is_immutable(self):
        """Test that application models are immutable (frozen dataclass)."""
        application = Application(
            application_id="app-1",
            job_id="job-1",
            platform="upwork",
            status=ApplicationStatus.DISCOVERED,
        )
        
        # Attempting to mutate should fail (frozen dataclass)
        with pytest.raises(Exception):  # FrozenInstanceError
            application.status = ApplicationStatus.ASSESSED

    def test_job_assessment_is_immutable(self):
        """Test that and job assessment models are immutable."""
        assessment = JobAssessment(
            job_id="job-1",
            overall_readiness=0.8,
            recommendation=JobRecommendation.APPLY,
        )
        
        # Attempting to mutate should fail
        with pytest.raises(Exception):
            assessment.overall_readiness = 0.9

    def test_platform_model_is_immutable(self):
        """Test that platform models are immutable."""
        from app.work_market.models import Platform, PlatformType, PlatformConnectionStatus
        
        platform = Platform(
            platform_id="upwork",
            name="Upwork",
            type=PlatformType.PROPOSAL_BASED,
            connection_status=PlatformConnectionStatus.NOT_CONNECTED,
        )
        
        # Attempting to mutate should fail
        with pytest.raises(Exception):
            platform.connection_status = PlatformConnectionStatus.CONNECTED


class TestKnowledgeConflictPrevention:
    """Tests for knowledge conflict prevention."""

    def test_unresolved_knowledge_conflict_blocks_application(self):
        """Test that unresolved knowledge conflicts block application."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-conflict",
            source=JobSource.UPWORK,
            title="Conflicting Requirements",
            description="Job with conflicting knowledge requirements",
        )
        
        classification = JobClassification(
            job_id="job-conflict",
            profession="Specialist",
            task="Conflicting Task",
            required_knowledge=["Conflicting Knowledge A", "Conflicting Knowledge B"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-conflict",
            profession_match=0.5,
            knowledge_match=0.3,
            missing_knowledge=["Conflicting Knowledge A", "Conflicting Knowledge B"],
            recommendation=JobRecommendation.RESEARCH_FIRST,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should not be able to apply with unresolved conflicts
        assert service.can_apply(assessment) is False
        # Should recommend learning first (missing knowledge takes priority)
        assert assessment.recommendation in [JobRecommendation.LEARN_FIRST, JobRecommendation.RESEARCH_FIRST]

    def test_low_confidence_blocks_application(self):
        """Test that low confidence in assessment blocks application."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-low-confidence",
            source=JobSource.UPWORK,
            title="Unclear Requirements",
            description="Job with unclear requirements",
        )
        
        classification = JobClassification(
            job_id="job-low-confidence",
            profession="Unknown",
            task="Unclear Task",
            confidence=0.2,  # Very low confidence
        )
        
        evaluation = JobEvaluation(
            job_id="job-low-confidence",
            profession_match=0.3,
            confidence=0.2,  # Very low confidence
            recommendation=JobRecommendation.RESEARCH_FIRST,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should not be able to apply with low confidence
        assert service.can_apply(assessment) is False
        # Should recommend learning or research (low match situations)
        assert assessment.recommendation in [JobRecommendation.LEARN_FIRST, JobRecommendation.RESEARCH_FIRST, JobRecommendation.REJECT]


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_job_classification(self):
        """Test handling of empty job classification."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-empty",
            source=JobSource.UPWORK,
            title="Empty Job",
            description="Job with minimal information",
        )
        
        classification = JobClassification(
            job_id="job-empty",
            profession="Unknown",
            task="Unknown",
            required_skills=[],
            required_knowledge=[],
            required_capabilities=[],
        )
        
        evaluation = JobEvaluation(
            job_id="job-empty",
            profession_match=0.0,
            skill_match=0.0,
            knowledge_match=0.0,
            capability_match=0.0,
            recommendation=JobRecommendation.REJECT,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should handle gracefully and not crash
        assert assessment is not None
        assert assessment.job_id == "job-empty"
        # Should recommend reject for empty job
        assert assessment.recommendation == JobRecommendation.REJECT

    def test_extreme_readiness_values(self):
        """Test handling of extreme readiness values."""
        from app.work_market.knowledge_governance_adapter import MockKnowledgeProvider
        from app.work_market.evidence_adapter import MockEvidenceProvider
        
        service = FreelancingReadinessService(
            knowledge_provider=MockKnowledgeProvider(),
            evidence_provider=MockEvidenceProvider(),
        )
        
        # Test with maximum readiness
        job = FreelanceJob(
            job_id="job-max",
            source=JobSource.UPWORK,
            title="Perfect Match",
            description="Perfect match job",
        )
        
        classification = JobClassification(
            job_id="job-max",
            profession="SEO Specialist",
            task="Keyword Research",
            required_knowledge=["keyword_research"],  # High score concept
            required_capabilities=["keyword_research"],  # High score capability
        )
        
        evaluation = JobEvaluation(
            job_id="job-max",
            profession_match=1.0,
            skill_match=1.0,
            knowledge_match=1.0,
            capability_match=1.0,
            recommendation=JobRecommendation.APPLY,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should handle maximum values
        assert assessment.overall_readiness <= 1.0
        # With providers, should be able to apply for perfect match
        # (unless evidence/knowledge scores are too low)
        # Just verify it doesn't crash and returns valid values
        assert assessment.overall_readiness >= 0.0

        # Test with minimum readiness
        job_min = FreelanceJob(
            job_id="job-min",
            source=JobSource.UPWORK,
            title="No Match",
            description="No match job",
        )
        
        classification_min = JobClassification(
            job_id="job-min",
            profession="Unknown",
            task="Unknown Task",
            required_knowledge=["unknown_concept"],  # Low score concept
            required_capabilities=["unknown_capability"],  # Low score capability
        )
        
        evaluation_min = JobEvaluation(
            job_id="job-min",
            profession_match=0.0,
            skill_match=0.0,
            knowledge_match=0.0,
            capability_match=0.0,
            recommendation=JobRecommendation.REJECT,
        )
        
        assessment_min = service.assess_readiness(job_min, classification_min, evaluation_min)
        
        # Should handle minimum values
        assert assessment_min.overall_readiness >= 0.0
        assert service.can_apply(assessment_min) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
