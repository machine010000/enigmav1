from app.work_market.models import FreelanceJob, JobSource
from app.work_market.adapters import MockJobSource, JobDiscoveryQuery


def test_mock_job_source_discovers_jobs():
    """MockJobSource should discover jobs."""
    source = MockJobSource()
    query = JobDiscoveryQuery()

    jobs = source.discover_jobs(query)

    assert len(jobs) > 0
    assert all(isinstance(job, FreelanceJob) for job in jobs)


def test_mock_job_source_filters_by_source():
    """MockJobSource should filter jobs by source."""
    source = MockJobSource()
    query = JobDiscoveryQuery(source=JobSource.UPWORK)

    jobs = source.discover_jobs(query)

    assert all(job.source == JobSource.UPWORK for job in jobs)


def test_mock_job_source_filters_by_keywords():
    """MockJobSource should filter jobs by keywords."""
    source = MockJobSource()
    query = JobDiscoveryQuery(keywords=["SEO"])

    jobs = source.discover_jobs(query)

    assert len(jobs) > 0
    assert all("seo" in job.title.lower() or "seo" in job.description.lower() for job in jobs)


def test_mock_job_source_gets_specific_job():
    """MockJobSource should get a specific job by ID."""
    source = MockJobSource()
    job = source.get_job("mock-seo-1")

    assert job is not None
    assert job.job_id == "mock-seo-1"
    assert job.title == "SEO Audit for E-commerce Website"


def test_mock_job_source_normalizes_job():
    """MockJobSource should normalize raw job data."""
    source = MockJobSource()
    raw_job = {
        "job_id": "test",
        "source": "upwork",
        "title": "Test",
        "description": "Test",
        "budget": 100.0,
    }

    job = source.normalize_job(raw_job)

    assert isinstance(job, FreelanceJob)
    assert job.job_id == "test"
    assert job.source == JobSource.UPWORK
    assert job.normalized_at is not None
