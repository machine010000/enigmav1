from app.work_market.models import FreelanceJob, JobSource, JobRecommendation
from app.work_market.classifier import JobClassifier
from app.work_market.evaluator import JobEvaluator
from app.work_market.learning_analyzer import LearningAnalyzer


def test_learning_requirement_from_evaluation():
    """Job evaluation should create learning requirements."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()
    learning_analyzer = LearningAnalyzer()

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
    learning_req = learning_analyzer.create_learning_requirement(evaluation)

    assert learning_req.job_id == "test"
    assert isinstance(learning_req.missing_knowledge, list)
    assert isinstance(learning_req.missing_skills, list)
    assert isinstance(learning_req.missing_capabilities, list)
    assert isinstance(learning_req.research_tasks, list)
    assert isinstance(learning_req.academy_modules, list)


def test_learning_requirement_generates_research_tasks():
    """Learning requirement should generate research tasks."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()
    learning_analyzer = LearningAnalyzer()

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
    learning_req = learning_analyzer.create_learning_requirement(evaluation)

    if evaluation.missing_knowledge:
        assert len(learning_req.research_tasks) > 0


def test_learning_requirement_suggests_academy_modules():
    """Learning requirement should suggest academy modules."""
    classifier = JobClassifier()
    evaluator = JobEvaluator()
    learning_analyzer = LearningAnalyzer()

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
    learning_req = learning_analyzer.create_learning_requirement(evaluation)

    if evaluation.missing_knowledge:
        assert len(learning_req.academy_modules) > 0
