from app.work_market.models import FreelanceJob, JobSource


def test_freelance_job_is_immutable():
    """FreelanceJob should be immutable (frozen dataclass)."""
    from dataclasses import is_dataclass, fields

    assert is_dataclass(FreelanceJob)

    # Check if frozen
    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="Test",
        description="Test",
    )

    # Should not be able to modify
    try:
        job.title = "Modified"
        assert False, "FreelanceJob should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected


def test_freelance_job_has_required_fields():
    """FreelanceJob should have all required fields."""
    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="Test",
        description="Test",
    )

    assert job.job_id == "test"
    assert job.source == JobSource.UPWORK
    assert job.title == "Test"
    assert job.description == "Test"
    assert job.budget is None
    assert job.currency == "USD"
    assert job.skills == []


def test_freelance_job_to_dict():
    """FreelanceJob should serialize to dict."""
    from datetime import datetime

    job = FreelanceJob(
        job_id="test",
        source=JobSource.UPWORK,
        title="Test",
        description="Test",
        budget=100.0,
        skills=["SEO"],
    )

    job_dict = job.to_dict()

    assert job_dict["job_id"] == "test"
    assert job_dict["source"] == "upwork"
    assert job_dict["title"] == "Test"
    assert job_dict["budget"] == 100.0
    assert job_dict["skills"] == ["SEO"]
