from app.work_market.models import FreelanceJob, JobSource
from app.work_market.classifier import JobClassifier


def test_capability_mapping():
    """Jobs should extract required capabilities."""
    classifier = JobClassifier()

    seo_job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="SEO Audit",
        description="Need SEO audit",
    )

    classification = classifier.classify(seo_job)

    assert len(classification.required_capabilities) > 0
    assert "Website Analysis" in classification.required_capabilities or "Keyword Research" in classification.required_capabilities
