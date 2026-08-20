"""Read-only Freelancer.com official REST API client.

Direct REST wrapper around official Freelancer API endpoints.
No marketplace write operations (bids, messages, projects, milestones) are exposed.

Official API: https://developers.freelancer.com/
Sandbox: sandbox.api.freelancer.com
Production: api.freelancer.com
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class FreelancerClientError(Exception):
    """Freelancer API client error."""

    pass


class FreelancerUnauthorized(FreelancerClientError):
    """OAuth token missing, invalid, or expired."""

    pass


class FreelancerNotFound(FreelancerClientError):
    """Resource not found."""

    pass


class FreelancerRateLimited(FreelancerClientError):
    """Rate limit exceeded."""

    pass


class FreelancerClient:
    """Read-only Freelancer.com API client.
    
    Supports:
    - Project search and detail
    - User/employer detail
    - Reputation data
    - Job skills/categories
    
    Does NOT support:
    - Bidding
    - Messaging
    - Creating projects
    - Milestones
    - Any marketplace write operations
    """

    def __init__(
        self,
        token: str,
        *,
        sandbox: bool = False,
        timeout: float = 30.0,
    ):
        """Initialize Freelancer client.

        Args:
            token: OAuth access token or personal access token.
            sandbox: Use sandbox.api.freelancer.com instead of production.
            timeout: HTTP request timeout in seconds.
        """
        if not token or not token.strip():
            raise FreelancerClientError("Token is required and must not be empty")

        self.token = token.strip()
        self.timeout = timeout
        self.sandbox = sandbox
        self.base_url = "https://sandbox.api.freelancer.com" if sandbox else "https://api.freelancer.com"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-load async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Freelancer-OAuth-V1": self.token},
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make authenticated request to Freelancer API.

        Args:
            method: HTTP method (GET, etc).
            endpoint: API endpoint path (e.g. /projects/search).
            params: Query parameters.

        Returns:
            Parsed JSON response body.

        Raises:
            FreelancerUnauthorized: If token is invalid/expired.
            FreelancerNotFound: If resource not found.
            FreelancerRateLimited: If rate limited.
            FreelancerClientError: For other API errors.
        """
        client = await self._get_client()
        try:
            response = await client.request(method, endpoint, params=params)
        except httpx.TimeoutException as e:
            raise FreelancerClientError(f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise FreelancerClientError(f"Request failed: {e}") from e

        if response.status_code == 401:
            raise FreelancerUnauthorized("OAuth token is invalid or expired")
        elif response.status_code == 404:
            raise FreelancerNotFound(f"Resource not found: {endpoint}")
        elif response.status_code == 429:
            raise FreelancerRateLimited("Rate limit exceeded; retry after delay")
        elif response.status_code >= 400:
            try:
                error_body = response.json()
                error_msg = error_body.get("message") or error_body.get("error") or response.text
            except Exception:
                error_msg = response.text
            raise FreelancerClientError(f"API error {response.status_code}: {error_msg}")

        try:
            return response.json()
        except Exception as e:
            raise FreelancerClientError(f"Invalid JSON response: {e}") from e

    async def search_projects(
        self,
        *,
        query: Optional[str] = None,
        skills: Optional[list[str]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """Search for projects.

        Args:
            query: Search text (project title/description).
            skills: Filter by skills (job categories).
            limit: Number of results (max 50).
            offset: Pagination offset.
            sort_by: Sort order (e.g. 'time_submitted', 'rating').

        Returns:
            API response with projects list and metadata.
        """
        params = {"limit": min(limit, 50), "offset": offset}
        if query:
            params["query"] = query
        if skills:
            params["skills"] = ",".join(skills)
        if sort_by:
            params["sort_by"] = sort_by

        result = await self._request("GET", "/projects/search", params=params)
        return result

    async def get_project(self, project_id: str) -> dict[str, Any]:
        """Fetch detailed project information.

        Args:
            project_id: Freelancer project ID.

        Returns:
            Project detail object.
        """
        result = await self._request("GET", f"/projects/{project_id}")
        return result

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Fetch user/employer profile.

        Args:
            user_id: Freelancer user ID.

        Returns:
            User detail object.
        """
        result = await self._request("GET", f"/users/{user_id}")
        return result

    async def get_user_reputation(self, user_id: str) -> dict[str, Any]:
        """Fetch user reputation/review data.

        Args:
            user_id: Freelancer user ID.

        Returns:
            Reputation object.
        """
        result = await self._request("GET", f"/users/{user_id}/reputation")
        return result

    async def get_jobs(self) -> dict[str, Any]:
        """Fetch available job categories/skills.

        Returns:
            Jobs/categories list.
        """
        result = await self._request("GET", "/jobs")
        return result

    async def get_currencies(self) -> dict[str, Any]:
        """Fetch supported currencies.

        Returns:
            Currencies list.
        """
        result = await self._request("GET", "/currencies")
        return result

    async def get_categories(self) -> dict[str, Any]:
        """Fetch project categories.

        Returns:
            Categories list.
        """
        result = await self._request("GET", "/categories")
        return result
