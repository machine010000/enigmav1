from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import re

from app.work_market.models import FreelanceJob
from app.expert_domains.work.work_specification import (
    WorkSpecification,
    WorkPriority,
    WorkComplexity,
    WorkStatus,
)


class SEOJobCategory(str, Enum):
    """SEO job categories for classification."""
    SEO_AUDIT = "seo_audit"
    KEYWORD_RESEARCH = "keyword_research"
    TECHNICAL_SEO = "technical_seo"
    LOCAL_SEO = "local_seo"
    ECOMMERCE_SEO = "ecommerce_seo"
    CONTENT_OPTIMIZATION = "content_optimization"
    LINK_BUILDING = "link_building"
    SEO_STRATEGY = "seo_strategy"
    ON_PAGE_SEO = "on_page_seo"
    OFF_PAGE_SEO = "off_page_seo"


@dataclass
class JobClassificationResult:
    """Result of job classification."""
    job_id: str
    category: SEOJobCategory
    confidence: float  # 0.0 to 1.0
    business_goal: str
    business_context: str
    industry: str
    target_audience: str
    expected_outcome: str
    constraints: List[str] = field(default_factory=list)
    priority: WorkPriority = WorkPriority.MEDIUM
    complexity: WorkComplexity = WorkComplexity.MODERATE
    classification_reasons: List[str] = field(default_factory=list)
    classified_at: datetime = field(default_factory=datetime.utcnow)


class JobClassifier(ABC):
    """Contract for classifying marketplace jobs."""

    @abstractmethod
    def classify(self, job: FreelanceJob) -> JobClassificationResult:
        """
        Classify a marketplace job into SEO categories.

        Analyzes:
        - Job title
        - Description
        - Skills
        - Budget
        - Timeline

        Returns classification with confidence and reasoning.
        """
        pass


class SEOJobClassifier(JobClassifier):
    """
    Classifies marketplace jobs into SEO categories.

    Uses keyword analysis and pattern matching to determine job type.
    """

    def __init__(self) -> None:
        self._category_keywords = self._initialize_category_keywords()
        self._industry_keywords = self._initialize_industry_keywords()

    def _initialize_category_keywords(self) -> Dict[SEOJobCategory, List[str]]:
        """Initialize keywords for each SEO category."""
        return {
            SEOJobCategory.SEO_AUDIT: [
                "audit", "analysis", "review", "assessment", "health check",
                "site audit", "technical audit", "seo audit", "website audit",
            ],
            SEOJobCategory.KEYWORD_RESEARCH: [
                "keyword", "research", "keywords", "keyword research", "keyword analysis",
                "search terms", "keyword strategy", "keyword discovery",
            ],
            SEOJobCategory.TECHNICAL_SEO: [
                "technical", "speed", "performance", "crawl", "index", "schema",
                "structured data", "canonical", "redirect", "robots.txt", "sitemap",
                "core web vitals", "page speed", "mobile optimization",
            ],
            SEOJobCategory.LOCAL_SEO: [
                "local", "google business", "gmb", "google my business", "maps",
                "local search", "local ranking", "citation", "nap", "local seo",
            ],
            SEOJobCategory.ECOMMERCE_SEO: [
                "ecommerce", "e-commerce", "shopify", "woocommerce", "product",
                "product page", "category page", "online store", "ecommerce seo",
            ],
            SEOJobCategory.CONTENT_OPTIMIZATION: [
                "content", "optimization", "on-page", "on page", "meta", "title",
                "description", "content writing", "blog", "article", "content strategy",
            ],
            SEOJobCategory.LINK_BUILDING: [
                "link", "backlink", "link building", "backlinks", "off-page",
                "off page", "authority", "domain authority", "guest post", "outreach",
            ],
            SEOJobCategory.SEO_STRATEGY: [
                "strategy", "plan", "roadmap", "consulting", "advisory",
                "seo strategy", "seo plan", "consultation",
            ],
            SEOJobCategory.ON_PAGE_SEO: [
                "on-page", "on page", "meta tags", "title tags", "internal linking",
                "image optimization", "url structure", "header tags",
            ],
            SEOJobCategory.OFF_PAGE_SEO: [
                "off-page", "off page", "link building", "social signals",
                "brand mentions", "digital pr", "off-page seo",
            ],
        }

    def _initialize_industry_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for industry detection."""
        return {
            "ecommerce": ["ecommerce", "e-commerce", "shopify", "woocommerce", "magento", "online store"],
            "saas": ["saas", "software", "app", "platform", "subscription"],
            "healthcare": ["health", "medical", "doctor", "clinic", "hospital"],
            "finance": ["finance", "financial", "banking", "investment", "insurance"],
            "real_estate": ["real estate", "property", "housing", "realtor"],
            "technology": ["tech", "software", "startup", "saaS", "app"],
            "education": ["education", "school", "university", "course", "learning"],
            "retail": ["retail", "store", "shop", "shopping", "e-commerce"],
            "b2b": ["b2b", "business to business", "enterprise", "corporate"],
            "b2c": ["b2c", "business to consumer", "consumer", "retail"],
        }

    def classify(self, job: FreelanceJob) -> JobClassificationResult:
        """Classify a marketplace job into SEO categories."""
        # Analyze job text
        title_lower = job.title.lower()
        description_lower = job.description.lower()
        skills_lower = " ".join(job.skills).lower()
        combined_text = f"{title_lower} {description_lower} {skills_lower}"

        # Determine category
        category, confidence, reasons = self._determine_category(combined_text, title_lower)

        # Extract business information
        business_goal = self._extract_business_goal(combined_text, category)
        business_context = self._extract_business_context(combined_text, job.description)
        industry = self._detect_industry(combined_text)
        target_audience = self._detect_target_audience(combined_text)
        expected_outcome = self._extract_expected_outcome(combined_text, category)

        # Determine priority and complexity
        priority = self._determine_priority(job, combined_text)
        complexity = self._determine_complexity(job, combined_text, category)

        # Extract constraints
        constraints = self._extract_constraints(combined_text, job.deadline, job.budget)

        return JobClassificationResult(
            job_id=job.job_id,
            category=category,
            confidence=confidence,
            business_goal=business_goal,
            business_context=business_context,
            industry=industry,
            target_audience=target_audience,
            expected_outcome=expected_outcome,
            constraints=constraints,
            priority=priority,
            complexity=complexity,
            classification_reasons=reasons,
        )

    def _determine_category(
        self,
        combined_text: str,
        title_lower: str,
    ) -> tuple[SEOJobCategory, float, List[str]]:
        """Determine the best matching category."""
        category_scores: Dict[SEOJobCategory, float] = {}
        reasons: List[str] = []

        for category, keywords in self._category_keywords.items():
            score = 0.0
            matched_keywords = []

            for keyword in keywords:
                if keyword in combined_text:
                    # Title matches count more
                    weight = 2.0 if keyword in title_lower else 1.0
                    score += weight
                    matched_keywords.append(keyword)

            if score > 0:
                category_scores[category] = score
                reasons.append(f"Matched {len(matched_keywords)} keywords for {category.value}: {', '.join(matched_keywords[:3])}")

        if not category_scores:
            # Default to SEO_AUDIT if no clear match
            return SEOJobCategory.SEO_AUDIT, 0.3, ["No clear category match, defaulting to SEO audit"]

        # Get best category
        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]

        # Normalize confidence
        max_possible = max(category_scores.values())
        confidence = min(1.0, best_score / max_possible) if max_possible > 0 else 0.5

        return best_category, confidence, reasons

    def _extract_business_goal(self, combined_text: str, category: SEOJobCategory) -> str:
        """Extract the business goal from the job."""
        # Look for goal-related phrases
        goal_patterns = [
            r"(?:goal|objective|aim|purpose|want|need|looking for)(?:\s+(?:to|is|are))?\s+([^.!?]+)",
            r"(?:improve|increase|boost|grow|enhance)(?:\s+(\w+)){1,3}",
        ]

        for pattern in goal_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                return matches[0].strip() if isinstance(matches[0], str) else " ".join(matches[0])

        # Default goal based on category
        category_goals = {
            SEOJobCategory.SEO_AUDIT: "Identify and fix SEO issues",
            SEOJobCategory.KEYWORD_RESEARCH: "Find target keywords for optimization",
            SEOJobCategory.TECHNICAL_SEO: "Improve technical SEO performance",
            SEOJobCategory.LOCAL_SEO: "Increase local search visibility",
            SEOJobCategory.ECOMMERCE_SEO: "Drive organic traffic to products",
            SEOJobCategory.CONTENT_OPTIMIZATION: "Optimize content for search engines",
            SEOJobCategory.LINK_BUILDING: "Build high-quality backlinks",
            SEOJobCategory.SEO_STRATEGY: "Develop comprehensive SEO strategy",
            SEOJobCategory.ON_PAGE_SEO: "Optimize on-page elements",
            SEOJobCategory.OFF_PAGE_SEO: "Improve off-page signals",
        }

        return category_goals.get(category, "Improve search engine visibility")

    def _extract_business_context(self, combined_text: str, description: str) -> str:
        """Extract business context from the job."""
        # Use first few sentences of description as context
        sentences = re.split(r'[.!?]', description)
        if sentences:
            return sentences[0].strip()
        return "SEO optimization project"

    def _detect_industry(self, combined_text: str) -> str:
        """Detect the industry from the job."""
        industry_scores: Dict[str, int] = {}

        for industry, keywords in self._industry_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                industry_scores[industry] = score

        if industry_scores:
            return max(industry_scores, key=industry_scores.get)

        return "general"

    def _detect_target_audience(self, combined_text: str) -> str:
        """Detect target audience from the job."""
        audience_keywords = {
            "b2b": ["b2b", "business", "enterprise", "corporate"],
            "b2c": ["b2c", "consumer", "retail", "individual"],
            "local": ["local", "near me", "area", "region"],
            "national": ["national", "country-wide", "nationwide"],
            "international": ["international", "global", "worldwide"],
        }

        for audience, keywords in audience_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return audience

        return "general"

    def _extract_expected_outcome(self, combined_text: str, category: SEOJobCategory) -> str:
        """Extract expected outcome from the job."""
        # Look for outcome-related phrases
        outcome_patterns = [
            r"(?:expect|want|need|goal)(?:\s+(?:to|is))?\s+([^.!?]+)",
            r"(?:result|outcome|deliverable)(?:\s+(?:is|are))?\s+([^.!?]+)",
        ]

        for pattern in outcome_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                return matches[0].strip() if isinstance(matches[0], str) else " ".join(matches[0])

        # Default outcome based on category
        category_outcomes = {
            SEOJobCategory.SEO_AUDIT: "Comprehensive SEO audit report with actionable recommendations",
            SEOJobCategory.KEYWORD_RESEARCH: "List of target keywords with search volume and competition data",
            SEOJobCategory.TECHNICAL_SEO: "Improved technical SEO performance and Core Web Vitals",
            SEOJobCategory.LOCAL_SEO: "Increased local search visibility and Google Maps ranking",
            SEOJobCategory.ECOMMERCE_SEO: "Increased organic traffic and product page rankings",
            SEOJobCategory.CONTENT_OPTIMIZATION: "Optimized content pages with improved search rankings",
            SEOJobCategory.LINK_BUILDING: "High-quality backlinks from relevant websites",
            SEOJobCategory.SEO_STRATEGY: "Comprehensive SEO strategy document",
            SEOJobCategory.ON_PAGE_SEO: "Optimized on-page elements for better rankings",
            SEOJobCategory.OFF_PAGE_SEO: "Improved off-page signals and authority",
        }

        return category_outcomes.get(category, "Improved search engine rankings")

    def _determine_priority(self, job: FreelanceJob, combined_text: str) -> WorkPriority:
        """Determine priority based on job characteristics."""
        # Check for urgency indicators
        urgency_keywords = ["urgent", "asap", "immediately", "emergency", "critical"]
        if any(keyword in combined_text for keyword in urgency_keywords):
            return WorkPriority.CRITICAL

        # Check for high importance
        importance_keywords = ["important", "priority", "key", "essential"]
        if any(keyword in combined_text for keyword in importance_keywords):
            return WorkPriority.HIGH

        # Check budget for priority indication
        if job.budget:
            if job.budget > 5000:
                return WorkPriority.HIGH
            elif job.budget > 1000:
                return WorkPriority.MEDIUM
            else:
                return WorkPriority.LOW

        return WorkPriority.MEDIUM

    def _determine_complexity(
        self,
        job: FreelanceJob,
        combined_text: str,
        category: SEOJobCategory,
    ) -> WorkComplexity:
        """Determine complexity based on job characteristics."""
        # Check for complexity indicators
        complexity_keywords = {
            "complex": ["complex", "complicated", "advanced", "comprehensive", "full"],
            "simple": ["simple", "basic", "quick", "easy", "minor"],
        }

        for keyword in complexity_keywords["complex"]:
            if keyword in combined_text:
                return WorkComplexity.VERY_COMPLEX

        for keyword in complexity_keywords["simple"]:
            if keyword in combined_text:
                return WorkComplexity.SIMPLE

        # Category-based complexity
        category_complexity = {
            SEOJobCategory.SEO_AUDIT: WorkComplexity.COMPLEX,
            SEOJobCategory.SEO_STRATEGY: WorkComplexity.VERY_COMPLEX,
            SEOJobCategory.TECHNICAL_SEO: WorkComplexity.COMPLEX,
            SEOJobCategory.ECOMMERCE_SEO: WorkComplexity.COMPLEX,
            SEOJobCategory.KEYWORD_RESEARCH: WorkComplexity.MODERATE,
            SEOJobCategory.CONTENT_OPTIMIZATION: WorkComplexity.MODERATE,
            SEOJobCategory.LINK_BUILDING: WorkComplexity.COMPLEX,
            SEOJobCategory.LOCAL_SEO: WorkComplexity.MODERATE,
            SEOJobCategory.ON_PAGE_SEO: WorkComplexity.MODERATE,
            SEOJobCategory.OFF_PAGE_SEO: WorkComplexity.COMPLEX,
        }

        return category_complexity.get(category, WorkComplexity.MODERATE)

    def _extract_constraints(
        self,
        combined_text: str,
        deadline: Optional[datetime],
        budget: Optional[float],
    ) -> List[str]:
        """Extract constraints from the job."""
        constraints = []

        if deadline:
            constraints.append(f"Deadline: {deadline.strftime('%Y-%m-%d')}")

        if budget:
            constraints.append(f"Budget: ${budget:.2f}")

        # Look for constraint keywords
        constraint_patterns = [
            r"(?:must|should|need to|require)(?:\s+(?:not|only))?\s+([^.!?]+)",
            r"(?:constraint|limitation|restriction)(?:\s+(?:is|are))?\s+([^.!?]+)",
        ]

        for pattern in constraint_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                constraint = match.strip() if isinstance(match, str) else " ".join(match)
                if len(constraint) > 10:  # Filter out very short matches
                    constraints.append(constraint)

        return constraints


class JobClassificationOrchestrator:
    """
    Orchestrates job classification and WorkSpecification generation.
    """

    def __init__(self) -> None:
        self._classifier = SEOJobClassifier()

    def classify_job(self, job: FreelanceJob) -> JobClassificationResult:
        """Classify a marketplace job."""
        return self._classifier.classify(job)

    def create_work_specification(
        self,
        job: FreelanceJob,
        classification: JobClassificationResult,
    ) -> WorkSpecification:
        """
        Create a WorkSpecification from classification result.

        This is the bridge between marketplace jobs and expert domains.
        """
        return WorkSpecification(
            work_id=job.job_id,
            title=job.title,
            description=job.description,
            business_goal=classification.business_goal,
            business_context=classification.business_context,
            industry=classification.industry,
            target_audience=classification.target_audience,
            expected_outcome=classification.expected_outcome,
            constraints=classification.constraints,
            priority=classification.priority,
            complexity=classification.complexity,
            required_capabilities=[],  # Will be populated by JobMapper
            optional_capabilities=[],
            recommended_capabilities=[],
            required_tasks=[],  # Will be populated by JobMapper
            optional_tasks=[],
            suggested_tasks=[],
            status=WorkStatus.DRAFT,
            metadata={
                "source": job.source.value,
                "source_url": job.source_url,
                "budget": job.budget,
                "currency": job.currency,
                "deadline": job.deadline.isoformat() if job.deadline else None,
                "skills": job.skills,
                "client_information": job.client_information,
                "category": classification.category.value,
                "classification_confidence": classification.confidence,
                "classification_reasons": classification.classification_reasons,
            },
        )
