from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.work_market.models import FreelanceJob, JobSource


@dataclass
class JobDiscoveryQuery:
    """Query parameters for job discovery."""
    keywords: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    source: Optional[JobSource] = None
    limit: int = 10


class JobSourceAdapter(ABC):
    """Abstract adapter for marketplace job sources."""

    @abstractmethod
    def discover_jobs(self, query: JobDiscoveryQuery) -> List[FreelanceJob]:
        """Discover jobs from the marketplace."""
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[FreelanceJob]:
        """Get a specific job by ID."""
        pass

    @abstractmethod
    def normalize_job(self, raw_job: Dict[str, Any]) -> FreelanceJob:
        """Normalize raw job data into FreelanceJob contract."""
        pass


class MockJobSource(JobSourceAdapter):
    """Mock job source for testing and development."""

    def __init__(self) -> None:
        self._jobs: Dict[str, FreelanceJob] = {}
        self._initialize_mock_jobs()

    def _initialize_mock_jobs(self) -> None:
        """Initialize mock job data."""
        # Mock SEO job
        seo_job = FreelanceJob(
            job_id="mock-seo-1",
            source=JobSource.UPWORK,
            title="SEO Audit for E-commerce Website",
            description="Need comprehensive SEO audit for my e-commerce website. Focus on technical SEO, keyword analysis, and competitor research.",
            client_information={
                "name": "Test Client",
                "company": "Test Company",
                "location": "Remote",
            },
            budget=500.0,
            currency="USD",
            deadline=datetime(2024, 2, 1),
            skills=["SEO", "Technical SEO", "Keyword Research", "Competitor Analysis"],
            source_url="https://upwork.com/jobs/mock-seo-1",
        )
        self._jobs[seo_job.job_id] = seo_job

        # Mock Content Writing job
        content_job = FreelanceJob(
            job_id="mock-content-1",
            source=JobSource.FIVERR,
            title="Write 10 Blog Posts About Marketing",
            description="Need 10 engaging blog posts about digital marketing strategies for a marketing agency.",
            client_information={
                "name": "Marketing Agency",
                "company": "Growth Marketing Co",
                "location": "Remote",
            },
            budget=300.0,
            currency="USD",
            deadline=datetime(2024, 1, 15),
            skills=["Content Writing", "Blog Writing", "Marketing", "SEO"],
            source_url="https://fiverr.com/jobs/mock-content-1",
        )
        self._jobs[content_job.job_id] = content_job

        # Mock Web Development job
        web_job = FreelanceJob(
            job_id="mock-web-1",
            source=JobSource.FREELANCER,
            title="Build Landing Page for SaaS Product",
            description="Need a modern, responsive landing page for a SaaS product. Must include pricing section, features, and contact form.",
            client_information={
                "name": "SaaS Startup",
                "company": "TechStartup Inc",
                "location": "Remote",
            },
            budget=1500.0,
            currency="USD",
            deadline=datetime(2024, 3, 1),
            skills=["Web Development", "HTML", "CSS", "JavaScript", "Responsive Design"],
            source_url="https://freelancer.com/jobs/mock-web-1",
        )
        self._jobs[web_job.job_id] = web_job

    def discover_jobs(self, query: JobDiscoveryQuery) -> List[FreelanceJob]:
        """Discover jobs from mock data."""
        jobs = list(self._jobs.values())

        # Filter by source if specified
        if query.source:
            jobs = [job for job in jobs if job.source == query.source]

        # Filter by keywords
        if query.keywords:
            jobs = [
                job
                for job in jobs
                if any(keyword.lower() in job.title.lower() or keyword.lower() in job.description.lower()
                      for keyword in query.keywords)
            ]

        # Filter by skills
        if query.skills:
            jobs = [
                job
                for job in jobs
                if any(skill.lower() in [s.lower() for s in job.skills]
                      for skill in query.skills)
            ]

        # Filter by budget
        if query.budget_min is not None:
            jobs = [job for job in jobs if job.budget and job.budget >= query.budget_min]
        if query.budget_max is not None:
            jobs = [job for job in jobs if job.budget and job.budget <= query.budget_max]

        # Limit results
        return jobs[:query.limit]

    def get_job(self, job_id: str) -> Optional[FreelanceJob]:
        """Get a specific job by ID."""
        return self._jobs.get(job_id)

    def normalize_job(self, raw_job: Dict[str, Any]) -> FreelanceJob:
        """Normalize raw job data into FreelanceJob contract."""
        # For mock data, assume it's already normalized
        # In real adapters, this would transform platform-specific formats
        return FreelanceJob(
            job_id=raw_job.get("job_id", "unknown"),
            source=JobSource(raw_job.get("source", "other")),
            title=raw_job.get("title", ""),
            description=raw_job.get("description", ""),
            client_information=raw_job.get("client_information", {}),
            budget=raw_job.get("budget"),
            currency=raw_job.get("currency", "USD"),
            deadline=raw_job.get("deadline"),
            skills=raw_job.get("skills", []),
            source_url=raw_job.get("source_url", ""),
            discovered_at=raw_job.get("discovered_at", datetime.utcnow()),
            normalized_at=datetime.utcnow(),
            metadata=raw_job.get("metadata", {}),
        )
