"""Freelancer.com marketplace adapter.

Fetches and normalizes opportunities from Freelancer.com official API.
Implements MarketplaceOpportunityAdapter contract.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.freelancing.adapter_contract import MarketplaceOpportunityAdapter
from app.freelancing.freelancer_client import FreelancerClient, FreelancerClientError, FreelancerUnauthorized
from app.freelancing.ingestion import NormalizedMarketplaceOpportunity

logger = logging.getLogger(__name__)


class FreelancerMarketplaceAdapter(MarketplaceOpportunityAdapter):
    """Read-only Freelancer.com marketplace adapter.

    Fetches projects via official API and normalizes to canonical format.
    """

    def __init__(self, token: str, *, sandbox: bool = False):
        """Initialize Freelancer adapter.

        Args:
            token: Freelancer OAuth/personal access token.
            sandbox: Use sandbox environment.

        Raises:
            ValueError: If token is empty.
        """
        if not token or not token.strip():
            raise ValueError("Freelancer token is required")

        self.token = token
        self.sandbox = sandbox
        self.client = FreelancerClient(token, sandbox=sandbox)

    async def close(self):
        """Close HTTP client."""
        await self.client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def discover_opportunities(
        self,
        *,
        query: Optional[str] = None,
        skills: Optional[list[str]] = None,
        limit: int = 50,
    ) -> List[NormalizedMarketplaceOpportunity]:
        """Search for projects on Freelancer and normalize results.

        Args:
            query: Search keywords (title/description).
            skills: Filter by job categories.
            limit: Maximum projects to return (default 50, max 50).

        Returns:
            List of normalized opportunities.

        Raises:
            FreelancerUnauthorized: If token is invalid.
            FreelancerClientError: For API errors.
        """
        limit = min(limit, 50)  # API max is 50

        try:
            result = await self.client.search_projects(query=query, skills=skills, limit=limit)
        except FreelancerUnauthorized:
            logger.error("Freelancer token invalid/expired")
            raise
        except FreelancerClientError as e:
            logger.error(f"Freelancer API error during search: {e}")
            raise

        projects = result.get("projects", [])
        opportunities = []

        for project_data in projects:
            try:
                opportunity = self._normalize_project(project_data)
                opportunities.append(opportunity)
            except Exception as e:
                logger.warning(f"Failed to normalize Freelancer project {project_data.get('id')}: {e}")
                # Skip malformed projects; continue with others

        return opportunities

    async def fetch_opportunity(self, platform_job_id: str) -> Optional[NormalizedMarketplaceOpportunity]:
        """Fetch detailed information for a specific project.

        Args:
            platform_job_id: Freelancer project ID.

        Returns:
            Normalized opportunity or None if not found.
        """
        try:
            result = await self.client.get_project(platform_job_id)
            project_data = result.get("project")
            if not project_data:
                logger.warning(f"Freelancer project {platform_job_id} returned empty data")
                return None

            opportunity = self._normalize_project(project_data)
            return opportunity
        except FreelancerClientError as e:
            logger.error(f"Failed to fetch Freelancer project {platform_job_id}: {e}")
            return None

    async def fetch_provider(self, provider_external_id: str) -> Optional[dict]:
        """Fetch employer/client profile data.

        Args:
            provider_external_id: Freelancer user ID (employer).

        Returns:
            Provider metadata dict or None if not found.
        """
        try:
            user_result = await self.client.get_user(provider_external_id)
            user_data = user_result.get("user")
            if not user_data:
                return None

            # Fetch reputation if available
            reputation = None
            try:
                rep_result = await self.client.get_user_reputation(provider_external_id)
                reputation = rep_result.get("reputation")
            except FreelancerClientError:
                # Reputation may not be available for all users
                pass

            provider_metadata = self._normalize_provider(user_data, reputation)
            return provider_metadata
        except FreelancerClientError as e:
            logger.error(f"Failed to fetch Freelancer user {provider_external_id}: {e}")
            return None

    def _normalize_project(self, project_data: dict) -> NormalizedMarketplaceOpportunity:
        """Normalize a Freelancer project to canonical format.

        Args:
            project_data: Raw project object from Freelancer API.

        Returns:
            Normalized opportunity.
        """
        project_id = str(project_data.get("id", ""))
        title = (project_data.get("title") or "").strip()
        description = (project_data.get("description") or "").strip()
        url = project_data.get("preview_url") or f"https://www.freelancer.com/projects/{project_id}"

        # Parse dates
        posted_at = None
        if project_data.get("time_submitted"):
            try:
                posted_at = datetime.utcfromtimestamp(project_data["time_submitted"])
            except (ValueError, TypeError):
                pass

        # Budget
        budget_min = None
        budget_max = None
        budget_type = None

        budget_data = project_data.get("budget")
        if budget_data:
            if isinstance(budget_data, dict):
                budget_min = self._safe_float(budget_data.get("minimum"))
                budget_max = self._safe_float(budget_data.get("maximum"))
            else:
                budget_max = self._safe_float(budget_data)
            budget_type = project_data.get("type", "fixed")  # fixed, hourly

        currency = (project_data.get("currency") or {}).get("code", "USD")

        # Skills/jobs
        skills = []
        if project_data.get("jobs"):
            for job in project_data["jobs"]:
                if isinstance(job, dict):
                    skill_name = job.get("name")
                else:
                    skill_name = str(job)
                if skill_name:
                    skills.append(skill_name)

        # Category
        category = None
        if project_data.get("category"):
            category_data = project_data["category"]
            if isinstance(category_data, dict):
                category = category_data.get("name")
            else:
                category = str(category_data)

        # Provider/client metadata
        employer_data = project_data.get("owner", {})
        provider_metadata = None
        if employer_data:
            # Extract verified status from badge
            badge_data = employer_data.get("badge", {})
            verified = False
            if isinstance(badge_data, dict):
                verified = badge_data.get("verified", False)

            provider_metadata = {
                "external_id": str(employer_data.get("id", "")),
                "username": employer_data.get("username"),
                "display_name": employer_data.get("display_name"),
                "location": employer_data.get("location", {}).get("city"),
                "country": employer_data.get("location", {}).get("country", {}).get("name"),
                "verified": verified,
            }

        # Raw metadata
        raw_metadata = {
            "freelancer_project_id": project_id,
            "project_type": project_data.get("type"),
            "status": project_data.get("status"),
            "bid_count": project_data.get("bid_count"),
            "time_free_bids_expire": project_data.get("time_free_bids_expire"),
            "attachments": len(project_data.get("attachments", [])),
        }

        return NormalizedMarketplaceOpportunity(
            platform="freelancer",
            platform_job_id=project_id,
            title=title,
            description=description,
            url=url,
            posted_at=posted_at,
            currency=currency,
            budget_min=budget_min,
            budget_max=budget_max,
            budget_type=budget_type,
            skills=tuple(skills),
            category=category,
            provider_metadata=provider_metadata,
            raw_metadata=raw_metadata,
            ingestion_source="freelancer.com",
        )

    def _normalize_provider(self, user_data: dict, reputation_data: Optional[dict] = None) -> dict:
        """Normalize Freelancer user/employer to provider metadata.

        Args:
            user_data: Raw user object from Freelancer API.
            reputation_data: Optional reputation object.

        Returns:
            Normalized provider metadata.
        """
        provider = {
            "external_id": str(user_data.get("id", "")),
            "username": user_data.get("username"),
            "display_name": user_data.get("display_name"),
            "location_city": user_data.get("location", {}).get("city"),
            "location_country": user_data.get("location", {}).get("country", {}).get("name"),
            "verified": user_data.get("badge", {}).get("verified", False) if isinstance(user_data.get("badge"), dict) else False,
            "rating": None,
            "review_count": None,
        }

        # Add reputation data if available
        if reputation_data:
            provider["rating"] = self._safe_float(reputation_data.get("rating"))
            provider["review_count"] = reputation_data.get("reviews_count")

        return provider

    def _safe_float(self, value: any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
