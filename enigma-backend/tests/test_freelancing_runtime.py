"""
Runtime Tests: Freelancing Pipeline, Learning, Readiness, and Proposal

These tests verify the runtime behavior of the freelancing system including:
- Job assessment pipeline
- Learning before application flow
- Readiness service behavior
- Proposal preparation integration
"""
import pytest
from datetime import datetime

from app.work_market.models import (
    FreelanceJob,
    JobSource,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
    JobAssessment,
    ApplicationDraft,
    ApplicationStatus,
)
from app.work_market.classifier import JobClassifier
from app.work_market.evaluator import JobEvaluator
from app.work_market.learning_analyzer import LearningAnalyzer
from app.work_market.application_draft_generator import ApplicationDraftGenerator
from app.work_market.readiness_service import FreelancingReadinessService


class TestJobAssessmentPipeline:
    """Tests for the complete job assessment pipeline."""

    def test_complete_assessment_pipeline(self):
        """Test that a job goes through the complete assessment pipeline."""
        # Create a sample job
        job = FreelanceJob(
            job_id="job-1",
            source=JobSource.UPWORK,
            title="SEO Audit for E-commerce",
            description="Need comprehensive SEO audit",
            skills=["SEO", "Technical SEO", "Keyword Research"],
            budget=100.0,
        )
        
        # Step 1: Classify the job
        classifier = JobClassifier()
        classification = classifier.classify(job)
        assert classification.job_id == "job-1"
        assert classification.profession != "UNKNOWN_PROFESSION"
        assert len(classification.required_skills) > 0 or len(classification.required_capabilities) > 0
        
        # Step 2: Evaluate the job
        evaluator = JobEvaluator()
        evaluation = evaluator.evaluate(job, classification)
        assert evaluation.job_id == "job-1"
        assert 0.0 <= evaluation.profession_match <= 1.0
        assert 0.0 <= evaluation.success_probability <= 1.0
        assert evaluation.recommendation in JobRecommendation
        
        # Step 3: Assess readiness
        readiness_service = FreelancingReadinessService()
        assessment = readiness_service.assess_readiness(job, classification, evaluation)
        assert assessment.job_id == "job-1"
        assert 0.0 <= assessment.overall_readiness <= 1.0
        assert isinstance(assessment.blockers, list)
        assert isinstance(assessment.risks, list)
        
        # Verify pipeline consistency
        assert evaluation.recommendation in JobRecommendation
        assert assessment.recommendation in JobRecommendation
        # Both should be valid recommendations (they may differ based on different logic)

    def test_pipeline_with_high_match_job(self):
        """Test pipeline behavior with a high-match job."""
        job = FreelanceJob(
            job_id="job-high-match",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
            skills=["SEO", "Technical SEO"],
            budget=150.0,
        )
        
        classifier = JobClassifier()
        classification = JobClassifier().classify(job)
        evaluation = JobEvaluator().evaluate(job, classification)
        assessment = FreelancingReadinessService().assess_readiness(job, classification, evaluation)
        
        # High match job should have better scores
        assert evaluation.profession_match >= 0.5
        assert assessment.overall_readiness >= 0.5

    def test_pipeline_with_low_match_job(self):
        """Test pipeline behavior with a low-match job."""
        job = FreelanceJob(
            job_id="job-low-match",
            source=JobSource.UPWORK,
            title="Complex Machine Learning Project",
            description="Need ML model development",
            skills=["Python", "Machine Learning", "TensorFlow"],
            budget=500.0,
        )
        
        classifier = JobClassifier()
        classification = classifier.classify(job)
        evaluation = JobEvaluator().evaluate(job, classification)
        assessment = FreelancingReadinessService().assess_readiness(job, classification, evaluation)
        
        # Low match job should have lower scores or blockers
        assert len(assessment.blockers) > 0 or assessment.overall_readiness < 0.7


class TestLearningBeforeApplication:
    """Tests for the learning before application flow."""

    def test_learning_requirement_generation(self):
        """Test that learning requirements are generated for jobs with gaps."""
        job = FreelanceJob(
            job_id="job-learning",
            source=JobSource.UPWORK,
            title="Advanced SEO Audit",
            description="Need advanced SEO with technical implementation",
            skills=["SEO", "Technical SEO", "Schema Markup"],
            budget=200.0,
        )
        
        classification = JobClassification(
            job_id="job-learning",
            profession="SEO Specialist",
            task="Advanced SEO Audit",
            required_skills=["Schema Markup", "Technical SEO"],
            required_knowledge=["Schema Markup", "Core Web Vitals"],
            required_capabilities=["Advanced SEO Audit"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-learning",
            profession_match=0.6,
            skill_match=0.5,
            knowledge_match=0.4,
            capability_match=0.5,
            missing_knowledge=["Schema Markup", "Core Web Vitals"],
            missing_capabilities=["Advanced SEO Audit"],
            recommendation=JobRecommendation.LEARN_FIRST,
        )
        
        analyzer = LearningAnalyzer()
        learning_req = analyzer.create_learning_requirement(evaluation)
        
        assert learning_req is not None
        assert learning_req.job_id == "job-learning"
        assert len(learning_req.missing_knowledge) > 0 or len(learning_req.missing_capabilities) > 0

    def test_learning_flow_blocks_application(self):
        """Test that learning requirement blocks application until resolved."""
        job = FreelanceJob(
            job_id="job-blocked",
            source=JobSource.UPWORK,
            title="Specialized SEO Task",
            description="Need specialized SEO work",
            skills=["SEO"],
            budget=100.0,
        )
        
        classification = JobClassification(
            job_id="job-blocked",
            profession="SEO Specialist",
            task="Specialized SEO",
            required_knowledge=["Specialized Technique"],
            required_capabilities=["Specialized SEO"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-blocked",
            profession_match=0.5,
            knowledge_match=0.3,
            capability_match=0.3,
            missing_knowledge=["Specialized Technique"],
            missing_capabilities=["Specialized SEO"],
            recommendation=JobRecommendation.LEARN_FIRST,
        )
        
        readiness_service = FreelancingReadinessService()
        assessment = readiness_service.assess_readiness(job, classification, evaluation)
        
        # Should not be able to apply
        assert readiness_service.can_apply(assessment) is False
        assert len(assessment.blockers) > 0
        assert assessment.recommendation == JobRecommendation.LEARN_FIRST


class TestReadinessService:
    """Tests for FreelancingReadinessService behavior."""

    def test_readiness_thresholds(self):
        """Test that readiness service respects configured thresholds."""
        service = FreelancingReadinessService()
        
        # Check that thresholds are defined
        assert "profession_match" in service._readiness_thresholds
        assert "skill_match" in service._readiness_thresholds
        assert "knowledge_match" in service._readiness_thresholds
        assert "capability_match" in service._readiness_thresholds
        assert "overall_readiness" in service._readiness_thresholds
        
        # Check that thresholds are reasonable (0.0 to 1.0)
        for key, threshold in service._readiness_thresholds.items():
            assert 0.0 <= threshold <= 1.0

    def test_readiness_components_weighting(self):
        """Test that readiness components are properly weighted."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-weighting",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
        )
        
        classification = JobClassification(
            job_id="job-weighting",
            profession="SEO Specialist",
            task="SEO Audit",
        )
        
        evaluation = JobEvaluation(
            job_id="job-weighting",
            profession_match=0.8,
            skill_match=0.7,
            knowledge_match=0.6,
            capability_match=0.7,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Overall readiness should be weighted average of components
        assert 0.0 <= assessment.overall_readiness <= 1.0
        # Should be reasonable (not too far from individual components)
        assert assessment.overall_readiness >= min(0.5, evaluation.profession_match, evaluation.capability_match)
        assert assessment.overall_readiness <= max(0.9, evaluation.profession_match, evaluation.capability_match)

    def test_blocker_identification(self):
        """Test that blockers are correctly identified."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-blockers",
            source=JobSource.UPWORK,
            title="Complex Job",
            description="Complex job requiring many skills",
        )
        
        classification = JobClassification(
            job_id="job-blockers",
            profession="Unknown",
            task="Complex Task",
            required_knowledge=["Knowledge1", "Knowledge2", "Knowledge3"],
            required_capabilities=["Capability1", "Capability2"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-blockers",
            profession_match=0.3,
            capability_match=0.3,
            missing_knowledge=["Knowledge1", "Knowledge2", "Knowledge3"],
            missing_capabilities=["Capability1", "Capability2"],
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should have blockers
        assert len(assessment.blockers) > 0
        # Should mention missing knowledge
        assert any("knowledge" in blocker.lower() for blocker in assessment.blockers)

    def test_risk_identification(self):
        """Test that risks are correctly identified."""
        service = FreelancingReadinessService()
        
        job = FreelanceJob(
            job_id="job-risks",
            source=JobSource.UPWORK,
            title="High Risk Job",
            description="Complex job with tight deadline",
        )
        
        classification = JobClassification(
            job_id="job-risks",
            profession="SEO Specialist",
            task="Complex Task",
            complexity="high",
            estimated_effort="high",
        )
        
        evaluation = JobEvaluation(
            job_id="job-risks",
            risk_score=0.8,
            complexity_score=0.8,
            effort_score=0.8,
        )
        
        assessment = service.assess_readiness(job, classification, evaluation)
        
        # Should have risks
        assert len(assessment.risks) > 0
        # Should mention complexity or effort
        assert any("complexity" in risk.lower() or "effort" in risk.lower() for risk in assessment.risks)


class TestProposalPreparation:
    """Tests for proposal preparation integration."""

    def test_proposal_draft_generation(self):
        """Test that proposal drafts are generated for ready jobs."""
        job = FreelanceJob(
            job_id="job-proposal",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need comprehensive SEO audit",
            skills=["SEO", "Technical SEO"],
            budget=100.0,
        )
        
        classification = JobClassification(
            job_id="job-proposal",
            profession="SEO Specialist",
            task="SEO Audit",
            required_skills=["SEO", "Technical SEO"],
            required_capabilities=["SEO Audit"],
            expected_deliverables=["SEO Report", "Recommendations"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-proposal",
            profession_match=0.8,
            skill_match=0.7,
            knowledge_match=0.6,
            capability_match=0.7,
            recommendation=JobRecommendation.APPLY,
        )
        
        generator = ApplicationDraftGenerator()
        draft = generator.generate_draft(job, classification, evaluation)
        
        assert draft is not None
        assert draft.job_id == "job-proposal"
        assert len(draft.understanding_of_task) > 0
        assert len(draft.proposed_approach) > 0
        assert len(draft.deliverables) > 0
        assert 0.0 <= draft.confidence <= 1.0

    def test_proposal_includes_relevant_capabilities(self):
        """Test that proposal includes relevant capabilities."""
        job = FreelanceJob(
            job_id="job-capabilities",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
        )
        
        classification = JobClassification(
            job_id="job-capabilities",
            profession="SEO Specialist",
            task="SEO Audit",
            required_capabilities=["SEO Audit", "Keyword Research"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-capabilities",
            profession_match=0.8,
            capability_match=0.7,
        )
        
        generator = ApplicationDraftGenerator()
        draft = generator.generate_draft(job, classification, evaluation)
        
        # Should include relevant capabilities
        assert len(draft.relevant_capabilities) > 0

    def test_proposal_includes_deliverables(self):
        """Test that proposal includes expected deliverables."""
        job = FreelanceJob(
            job_id="job-deliverables",
            source=JobSource.UPWORK,
            title="SEO Audit",
            description="Need SEO audit",
        )
        
        classification = JobClassification(
            job_id="job-deliverables",
            profession="SEO Specialist",
            task="SEO Audit",
            expected_deliverables=["SEO Report", "Action Plan", "Competitor Analysis"],
        )
        
        evaluation = JobEvaluation(
            job_id="job-deliverables",
            profession_match=0.8,
        )
        
        generator = ApplicationDraftGenerator()
        draft = generator.generate_draft(job, classification, evaluation)
        
        # Should include deliverables
        assert len(draft.deliverables) > 0


class TestApplicationStateTransitions:
    """Tests for application state machine transitions."""

    def test_application_initial_state(self):
        """Test that applications start in DISCOVERED state."""
        from app.work_market.models import Application, ApplicationStatus
        
        application = Application(
            application_id="app-1",
            job_id="job-1",
            platform="upwork",
        )
        
        assert application.status == ApplicationStatus.DISCOVERED

    def test_application_state_progression(self):
        """Test that applications can progress through states."""
        from app.work_market.models import Application, ApplicationStatus
        from datetime import datetime
        
        # Simulate state progression
        states = [
            ApplicationStatus.DISCOVERED,
            ApplicationStatus.ASSESSED,
            ApplicationStatus.LEARNING,
            ApplicationStatus.READY,
            ApplicationStatus.DRAFTED,
            ApplicationStatus.REVIEW_REQUIRED,
            ApplicationStatus.APPROVED,
            ApplicationStatus.SUBMITTED,
        ]
        
        for i, state in enumerate(states):
            application = Application(
                application_id=f"app-{i}",
                job_id="job-1",
                platform="upwork",
                status=state,
            )
            assert application.status == state

    def test_application_final_states(self):
        """Test that applications can reach final states."""
        from app.work_market.models import Application, ApplicationStatus
        
        final_states = [
            ApplicationStatus.WON,
            ApplicationStatus.LOST,
            ApplicationStatus.WITHDRAWN,
        ]
        
        for state in final_states:
            application = Application(
                application_id=f"app-{state.value}",
                job_id="job-1",
                platform="upwork",
                status=state,
            )
            assert application.status == state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
