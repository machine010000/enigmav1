from app.work_market.models import FreelanceJob, JobSource, JobRecommendation
from app.work_market.classifier import JobClassifier
from app.work_market.evaluator import JobEvaluator


def test_job_evaluation_produces_scores():
    """Job evaluation should produce all required scores."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()

    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
        budget=500.0,
        skills=["SEO"],
    )

    classification = classifier.classify(job)
    evaluation = evaluator.evaluate(job, classification)

    assert 0.0 <= evaluation.profession_match <= 1.0
    assert 0.0 <= evaluation.skill_match <= 1.0
    assert 0.0 <= evaluation.knowledge_match <= 1.0
    assert 0.0 <= evaluation.capability_match <= 1.0
    assert 0.0 <= evaluation.complexity_score <= 1.0
    assert 0.0 <= evaluation.effort_score <= 1.0
    assert 0.0 <= evaluation.earning_score <= 1.0
    assert 0.0 <= evaluation.success_probability <= 1.0
    assert 0.0 <= evaluation.risk_score <= 1.0
    assert 0.0 <= evaluation.confidence <= 1.0


def test_job_evaluation_produces_recommendation():
    """Job evaluation should produce a recommendation."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()

    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
        budget=500.0,
        skills=["SEO"],
    )

    classification = classifier.classify(job)
    evaluation = evaluator.evaluate(job, classification)

    assert evaluation.recommendation in JobRecommendation


def test_job_evaluation_provides_reason():
    """Job evaluation should provide a reason for recommendation."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()

    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
        budget=500.0,
        skills=["SEO"],
    )

    classification = classifier.classify(job)
    evaluation = evaluator.evaluate(job, classification)

    assert evaluation.reason
    assert len(evaluation.reason) > 0


def test_job_evaluation_identifies_missing_items():
    """Job evaluation should identify missing knowledge, skills, and capabilities."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()

    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
        budget=500.0,
        skills=["SEO"],
    )

    classification = classifier.classify(job)
    evaluation = evaluator.evaluate(job, classification)

    # Should have some missing items (as we don't track full knowledge/capabilities yet)
    assert isinstance(evaluation.missing_knowledge, list)
    assert isinstance(evaluation.missing_skills, list)
    assert isinstance(evaluation.missing_capabilities, list)
