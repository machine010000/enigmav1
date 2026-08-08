from app.work_market.models import FreelanceJob, JobSource
from app.work_market.classifier import JobClassifier


def test_task_mapping():
    """Jobs should map to correct tasks."""
    classifier = JobClassifier()

    seo_job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need comprehensive SEO audit",
    )

    classification = classifier.classify(seo_job)

    assert classification.task == "SEO Audit"


def test_unknown_task_mapping():
    """Jobs without matching task keywords should map to UNKNOWN_TASK."""
    classifier = JobClassifier()

    unknown_job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="Random Task",
        description="Something unrelated",
    )

    classification = classifier.classify(unknown_job)

    assert classification.task == "UNKNOWN_TASK"
