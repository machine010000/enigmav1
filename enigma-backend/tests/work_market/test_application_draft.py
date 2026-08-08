from app.work_market.models import FreelanceJob, JobSource
from app.work_market.classifier import JobClassifier
from app.work_market.evaluator import JobEvaluator
from app.work_market.application_draft_generator import ApplicationDraftGenerator


def test_application_draft_from_evaluation():
    """Application draft should be generated from job evaluation."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()
    draft_generator = ApplicationDraftGenerator()

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
    draft = draft_generator.generate_draft(job, classification, evaluation)

    assert draft.job_id == "test"
    assert draft.profession == classification.profession
    assert draft.understanding_of_task
    assert draft.proposed_approach
    assert isinstance(draft.relevant_capabilities, list)
    assert isinstance(draft.deliverables, list)
    assert isinstance(draft.questions_for_client, list)


def test_application_draft_includes_questions():
    """Application draft should include questions for the client."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()
    draft_generator = ApplicationDraftGenerator()

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
    draft = draft_generator.generate_draft(job, classification, evaluation)

    assert len(draft.questions_for_client) > 0


def test_application_draft_includes_risks():
    """Application draft should identify potential risks."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()
    draft_generator = ApplicationDraftGenerator()

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
    draft = draft_generator.generate_draft(job, classification, evaluation)

    assert isinstance(draft.risks, list)
