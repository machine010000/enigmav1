from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.work_market.models import FreelanceJob, JobClassification


class JobClassifier:
    """Classifies jobs into profession, task, and requirements."""

    def __init__(self) -> None:
        # Simple keyword-based classification rules
        self._profession_keywords = {
            "SEO Specialist": ["seo", "search engine optimization", "audit", "keyword", "ranking"],
            "Content Writer": ["write", "blog", "content", "article", "copy"],
            "Web Developer": ["web", "website", "landing page", "frontend", "backend", "html", "css", "javascript"],
            "Social Media Manager": ["social media", "instagram", "facebook", "twitter", "linkedin", "marketing"],
            "Digital Marketer": ["marketing", "ads", "campaign", "funnel", "conversion"],
        }

        self._task_keywords = {
            "SEO Audit": ["audit", "analysis", "review", "assessment"],
            "Content Creation": ["write", "create", "blog", "article", "content"],
            "Website Development": ["build", "develop", "create", "landing page", "website"],
            "Social Media Management": ["manage", "post", "schedule", "engage", "growth"],
            "Marketing Campaign": ["campaign", "ads", "run", "launch", "promote"],
        }

    def classify(self, job: FreelanceJob) -> JobClassification:
        """Classify a job into profession, task, and requirements."""
        # Determine profession
        profession = self._determine_profession(job)
        task = self._determine_task(job)
        required_skills = self._extract_skills(job)
        required_knowledge = self._determine_knowledge(profession, task)
        required_capabilities = self._determine_capabilities(profession, task)
        expected_deliverables = self._determine_deliverables(task)
        expected_kpis = self._determine_kpis(task)
        complexity = self._determine_complexity(job)
        estimated_effort = self._determine_effort(job)
        confidence = self._calculate_confidence(job, profession, task)

        return JobClassification(
            job_id=job.job_id,
            profession=profession,
            task=task,
            required_skills=required_skills,
            required_knowledge=required_knowledge,
            required_capabilities=required_capabilities,
            expected_deliverables=expected_deliverables,
            expected_kpis=expected_kpis,
            complexity=complexity,
            estimated_effort=estimated_effort,
            confidence=confidence,
        )

    def _determine_profession(self, job: FreelanceJob) -> str:
        """Determine the profession based on job title and description."""
        text = f"{job.title} {job.description}".lower()

        for profession, keywords in self._profession_keywords.items():
            if any(keyword in text for keyword in keywords):
                return profession

        return "UNKNOWN_PROFESSION"

    def _determine_task(self, job: FreelanceJob) -> str:
        """Determine the specific task based on job content."""
        text = f"{job.title} {job.description}".lower()

        for task, keywords in self._task_keywords.items():
            if any(keyword in text for keyword in keywords):
                return task

        return "UNKNOWN_TASK"

    def _extract_skills(self, job: FreelanceJob) -> List[str]:
        """Extract skills from job."""
        return job.skills

    def _determine_knowledge(self, profession: str, task: str) -> List[str]:
        """Determine required knowledge based on profession and task."""
        knowledge_map = {
            "SEO Specialist": ["Technical SEO", "Keyword Research", "Competitor Analysis", "On-page SEO", "Off-page SEO"],
            "Content Writer": ["SEO Writing", "Copywriting", "Content Strategy", "Audience Research"],
            "Web Developer": ["HTML", "CSS", "JavaScript", "Responsive Design", "Web Standards"],
            "Social Media Manager": ["Platform Algorithms", "Content Strategy", "Audience Engagement", "Analytics"],
            "Digital Marketer": ["Paid Advertising", "Funnel Optimization", "Conversion Optimization", "Analytics"],
        }

        return knowledge_map.get(profession, [])

    def _determine_capabilities(self, profession: str, task: str) -> List[str]:
        """Determine required capabilities based on profession and task."""
        capability_map = {
            "SEO Specialist": ["Website Analysis", "Keyword Research", "Competitor Analysis", "Technical Diagnosis"],
            "Content Writer": ["Content Creation", "SEO Writing", "Research", "Copywriting"],
            "Web Developer": ["Frontend Development", "Backend Development", "Responsive Design", "API Integration"],
            "Social Media Manager": ["Content Scheduling", "Community Management", "Analytics", "Growth Hacking"],
            "Digital Marketer": ["Campaign Management", "Ad Creation", "Funnel Building", "Conversion Tracking"],
        }

        return capability_map.get(profession, [])

    def _determine_deliverables(self, task: str) -> List[str]:
        """Determine expected deliverables based on task."""
        deliverable_map = {
            "SEO Audit": ["SEO Audit Report", "Keyword Analysis", "Competitor Analysis", "Recommendations"],
            "Content Creation": ["Blog Posts", "Articles", "Social Media Content", "Copy"],
            "Website Development": ["Landing Page", "Responsive Design", "Functional Website", "Deployment"],
            "Social Media Management": ["Social Media Calendar", "Posts", "Engagement Report", "Growth Metrics"],
            "Marketing Campaign": ["Campaign Strategy", "Ad Creatives", "Launch Plan", "Performance Report"],
        }

        return deliverable_map.get(task, ["Deliverables"])

    def _determine_kpis(self, task: str) -> List[str]:
        """Determine expected KPIs based on task."""
        kpi_map = {
            "SEO Audit": ["SEO Score Improvement", "Keyword Rankings", "Technical Issues Fixed"],
            "Content Creation": ["Content Quality", "SEO Performance", "Engagement Metrics"],
            "Website Development": ["Page Load Speed", "Mobile Responsiveness", "User Experience"],
            "Social Media Management": ["Follower Growth", "Engagement Rate", "Reach"],
            "Marketing Campaign": ["ROI", "Conversion Rate", "Cost per Acquisition"],
        }

        return kpi_map.get(task, ["Success Metrics"])

    def _determine_complexity(self, job: FreelanceJob) -> str:
        """Determine job complexity based on budget and description."""
        if job.budget and job.budget > 1000:
            return "high"
        elif job.budget and job.budget > 300:
            return "medium"
        return "low"

    def _determine_effort(self, job: FreelanceJob) -> str:
        """Determine estimated effort based on complexity and deadline."""
        complexity = self._determine_complexity(job)
        if complexity == "high":
            return "high"
        elif complexity == "medium":
            return "medium"
        return "low"

    def _calculate_confidence(self, job: FreelanceJob, profession: str, task: str) -> float:
        """Calculate confidence in classification."""
        if profession == "UNKNOWN_PROFESSION" or task == "UNKNOWN_TASK":
            return 0.3

        # Higher confidence if skills match profession keywords
        profession_keywords = self._profession_keywords.get(profession, [])
        skill_match = any(skill.lower() in [k.lower() for k in profession_keywords]
                        for skill in job.skills)

        if skill_match:
            return 0.8

        return 0.6
