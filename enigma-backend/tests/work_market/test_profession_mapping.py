from app.work_market.models import FreelanceJob, JobSource
from app.work_market.classifier import JobClassifier


def test_profession_mapping():
    """Jobs should map to correct professions."""
    classifier = JobClassifier()

    seo_job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
    )

    classification = classifier.classify(seo_job)

    assert classification.profession == "SEO Specialist"


def test_unknown_profession_mapping():
    """Jobs without matching keywords should map to UNKNOWN_PROFESSION."""
    classifier = JobClassifier()

    unknown_job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="Random Task",
        description="Something unrelated",
    )

    classification = classifier.classify(unknown_job)

    assert classification.profession == "UNKNOWN_PROFESSION"


def test_profession_confidence():
    """Classification should include confidence score."""
    classifier = JobClassifier()

    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
        skills=["SEO", "Technical SEO"],
    )

    classification = classifier.classify(job)

    assert 0.0 <= classification.confidence <= 1.0
