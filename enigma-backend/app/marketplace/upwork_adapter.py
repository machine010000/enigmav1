"""
Upwork Marketplace Adapter.

Implements the MarketplaceAdapter interface for Upwork's GraphQL API.
Uses OAuth 2.0 authentication and normalizes all Upwork-specific data
to the platform-agnostic contracts.

Authentication: OAuth 2.0 Authorization Code Grant
API: GraphQL
Documentation: https://developer.upwork.com/
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.marketplace.contracts import (
    MarketplaceAdapter,
    MarketplacePlatform,
    MarketplaceAccount,
    NormalizedJob,
    NormalizedApplication,
    PlatformCapability,
    PlatformCost,
    PlatformLimits,
    AccountStatus,
    ApplicationStatus,
    CreditType,
    PlatformError,
)
from app.marketplace.upwork_economics import UpworkEconomicsEngine


@dataclass
class UpworkCredentials:
    """Upwork OAuth 2.0 credentials."""
    client_id: str
    client_secret: str
    redirect_uri: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class UpworkAdapter(MarketplaceAdapter):
    """
    Upwork implementation of MarketplaceAdapter.
    
    Handles OAuth 2.0 authentication, GraphQL API calls,
    and normalization of Upwork data to platform-agnostic format.
    """

    # Upwork API endpoints
    AUTH_URL = "https://www.upwork.com/ab/account-security/oauth2/authorize"
    TOKEN_URL = "https://www.upwork.com/api/v3/oauth2/token"
    GRAPHQL_URL = "https://api.upwork.com/graphql"

    def __init__(self, credentials: Optional[UpworkCredentials] = None) -> None:
        """
        Initialize Upwork adapter.
        
        Args:
            credentials: Upwork credentials. If None, will try to load from env vars.
        """
        if credentials:
            self._credentials = credentials
        else:
            self._credentials = self._load_credentials_from_env()
        
        self._authenticated = False
        self._account: Optional[MarketplaceAccount] = None
        self._client = httpx.AsyncClient(timeout=30.0)
        self._economics_engine = UpworkEconomicsEngine()

    @property
    def platform(self) -> MarketplacePlatform:
        """Get the platform this adapter handles."""
        return MarketplacePlatform.UPWORK

    @property
    def capabilities(self) -> List[PlatformCapability]:
        """Get the capabilities supported by this adapter."""
        return [
            PlatformCapability.JOB_DISCOVERY,
            PlatformCapability.JOB_RETRIEVAL,
            PlatformCapability.APPLICATION_SUBMISSION,
            PlatformCapability.APPLICATION_STATUS_TRACKING,
            PlatformCapability.CREDIT_MANAGEMENT,
            PlatformCapability.ACCOUNT_STATUS_CHECK,
        ]

    def _load_credentials_from_env(self) -> UpworkCredentials:
        """Load credentials from environment variables."""
        return UpworkCredentials(
            client_id=os.getenv("UPWORK_CLIENT_ID", ""),
            client_secret=os.getenv("UPWORK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("UPWORK_REDIRECT_URI", "http://localhost:8000/callback"),
        )

    async def authenticate(self, credentials: Dict[str, Any]) -> MarketplaceAccount:
        """
        Authenticate with Upwork using OAuth 2.0.
        
        Args:
            credentials: Dict with access_token and refresh_token (if already authenticated)
                        or authorization_code for first-time authentication
            
        Returns:
            MarketplaceAccount with authentication status
        """
        if "access_token" in credentials:
            # Direct token authentication
            self._credentials.access_token = credentials["access_token"]
            self._credentials.refresh_token = credentials.get("refresh_token")
        elif "authorization_code" in credentials:
            # Exchange authorization code for access token
            await self._exchange_code_for_token(credentials["authorization_code"])
        else:
            raise ValueError("Credentials must contain access_token or authorization_code")

        self._authenticated = True
        self._account = await self._get_account_info()
        
        return self._account

    async def _exchange_code_for_token(self, authorization_code: str) -> None:
        """Exchange authorization code for access token."""
        response = await self._client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": authorization_code,
                "client_id": self._credentials.client_id,
                "client_secret": self._credentials.client_secret,
                "redirect_uri": self._credentials.redirect_uri,
            },
        )
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        token_data = response.json()
        self._credentials.access_token = token_data["access_token"]
        self._credentials.refresh_token = token_data.get("refresh_token")
        # Token expires in 24 hours
        self._credentials.token_expires_at = datetime.utcnow()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using refresh token."""
        if not self._credentials.refresh_token:
            raise RuntimeError("No refresh token available")
        
        response = await self._client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._credentials.refresh_token,
                "client_id": self._credentials.client_id,
                "client_secret": self._credentials.client_secret,
            },
        )
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        token_data = response.json()
        self._credentials.access_token = token_data["access_token"]
        self._credentials.refresh_token = token_data.get("refresh_token")
        self._credentials.token_expires_at = datetime.utcnow()

    async def _get_account_info(self) -> MarketplaceAccount:
        """Get account information from Upwork."""
        # GraphQL query for account info
        query = """
        query {
            me {
                id
                profile {
                    displayName
                }
                accountStatus {
                    status
                }
                finance {
                    connects {
                        total
                        available
                    }
                }
            }
        }
        """
        
        response = await self._make_graphql_request(query)
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        data = response.json()
        me = data.get("data", {}).get("me", {})
        
        # Map Upwork status to our AccountStatus
        upwork_status = me.get("accountStatus", {}).get("status", "unknown")
        status = self._map_upwork_status(upwork_status)
        
        # Get connects info
        connects = me.get("finance", {}).get("connects", {})
        connects_available = connects.get("available", 0)
        connects_total = connects.get("total", 0)
        
        return MarketplaceAccount(
            platform=self.platform,
            account_id=str(me.get("id", "")),
            username=me.get("profile", {}).get("displayName", ""),
            status=status,
            is_authenticated=True,
            limits=PlatformLimits(
                credits_available=float(connects_available),
                credits_total=float(connects_total),
                credit_type=CreditType.CONNECTS,
                daily_application_limit=50,  # Upwork default
                monthly_application_limit=200,  # Upwork default
            ),
            last_synced_at=datetime.utcnow(),
        )

    def _map_upwork_status(self, upwork_status: str) -> AccountStatus:
        """Map Upwork status to AccountStatus enum."""
        status_map = {
            "active": AccountStatus.ACTIVE,
            "suspended": AccountStatus.SUSPENDED,
            "restricted": AccountStatus.RESTRICTED,
            "verification_pending": AccountStatus.VERIFICATION_PENDING,
        }
        return status_map.get(upwork_status.lower(), AccountStatus.UNKNOWN)

    async def get_account_status(self) -> MarketplaceAccount:
        """Get current account status."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        self._account = await self._get_account_info()
        return self._account

    async def discover_jobs(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[NormalizedJob]:
        """
        Discover jobs on Upwork.
        
        Args:
            query: Search query
            filters: Platform-specific filters (category, job_type, etc.)
            limit: Maximum number of jobs to return
            
        Returns:
            List of normalized jobs
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        # GraphQL query for job search
        graphql_query = """
        query($searchQuery: String!, $limit: Int!) {
            jobs(search: $searchQuery, limit: $limit) {
                id
                title
                description
                budget {
                    min
                    max
                    currency
                    type
                }
                skills {
                    name
                }
                jobType
                duration
                client {
                    id
                    displayName
                    reviews {
                        rating
                    }
                }
                createdDate
                connectsRequired
            }
        }
        """
        
        variables = {
            "searchQuery": query,
            "limit": limit,
        }
        
        response = await self._make_graphql_request(graphql_query, variables)
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        data = response.json()
        jobs_data = data.get("data", {}).get("jobs", [])
        
        return [self._normalize_job(job_data) for job_data in jobs_data]

    async def get_job(self, platform_job_id: str) -> NormalizedJob:
        """Get a specific job from Upwork."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        # GraphQL query for specific job
        query = """
        query($jobId: String!) {
            job(id: $jobId) {
                id
                title
                description
                budget {
                    min
                    max
                    currency
                    type
                }
                skills {
                    name
                }
                jobType
                duration
                client {
                    id
                    displayName
                    reviews {
                        rating
                    }
                }
                createdDate
                connectsRequired
            }
        }
        """
        
        variables = {"jobId": platform_job_id}
        
        response = await self._make_graphql_request(query, variables)
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        data = response.json()
        job_data = data.get("data", {}).get("job")
        
        if not job_data:
            raise ValueError(f"Job {platform_job_id} not found")
        
        return self._normalize_job(job_data)

    def _normalize_job(self, job_data: Dict[str, Any]) -> NormalizedJob:
        """Normalize Upwork job data to NormalizedJob."""
        budget = job_data.get("budget", {})
        client = job_data.get("client", {})
        reviews = client.get("reviews", {})
        
        return NormalizedJob(
            job_id=f"upwork_{job_data.get('id', '')}",
            platform=self.platform,
            platform_job_id=str(job_data.get("id", "")),
            title=job_data.get("title", ""),
            description=job_data.get("description", ""),
            budget_min=budget.get("min"),
            budget_max=budget.get("max"),
            budget_type=budget.get("type"),
            currency=budget.get("currency", "USD"),
            client_info={
                "id": client.get("id"),
                "name": client.get("displayName"),
                "rating": reviews.get("rating"),
            },
            skills_required=[skill.get("name") for skill in job_data.get("skills", [])],
            job_type=job_data.get("jobType"),
            duration=job_data.get("duration"),
            posted_date=self._parse_upwork_date(job_data.get("createdDate")),
            url=f"https://www.upwork.com/jobs/{job_data.get('id', '')}",
            platform_cost=PlatformCost(
                credit_type=CreditType.CONNECTS,
                amount=float(job_data.get("connectsRequired", 0)),
                currency="USD",
                is_free=job_data.get("connectsRequired", 0) == 0,
            ),
        )

    def _parse_upwork_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Upwork date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    async def submit_application(
        self,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """Submit an application to Upwork."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        # GraphQL mutation for application submission
        mutation = """
        mutation($jobId: String!, $coverLetter: String!, $bidAmount: Float!) {
            submitApplication(
                jobId: $jobId
                coverLetter: $coverLetter
                bidAmount: $bidAmount
            ) {
                id
                status
                submittedAt
            }
        }
        """
        
        variables = {
            "jobId": application.platform_job_id,
            "coverLetter": application.proposal_text,
            "bidAmount": application.bid_amount,
        }
        
        response = await self._make_graphql_request(mutation, variables)
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        data = response.json()
        app_data = data.get("data", {}).get("submitApplication", {})
        
        application.platform_application_id = str(app_data.get("id", ""))
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = self._parse_upwork_date(app_data.get("submittedAt"))
        
        return application

    async def get_application_status(
        self,
        platform_application_id: str,
    ) -> ApplicationStatus:
        """Get the status of an application."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        query = """
        query($applicationId: String!) {
            application(id: $applicationId) {
                status
            }
        }
        """
        
        variables = {"applicationId": platform_application_id}
        
        response = await self._make_graphql_request(query, variables)
        
        if response.status_code != 200:
            raise self._handle_api_error(response)
        
        data = response.json()
        status = data.get("data", {}).get("application", {}).get("status", "unknown")
        
        return self._map_upwork_application_status(status)

    def _map_upwork_application_status(self, upwork_status: str) -> ApplicationStatus:
        """Map Upwork application status to ApplicationStatus enum."""
        status_map = {
            "submitted": ApplicationStatus.SUBMITTED,
            "accepted": ApplicationStatus.ACCEPTED,
            "rejected": ApplicationStatus.REJECTED,
            "withdrawn": ApplicationStatus.WITHDRAWN,
        }
        return status_map.get(upwork_status.lower(), ApplicationStatus.UNKNOWN)

    async def get_platform_cost(self, platform_job_id: str) -> PlatformCost:
        """Get the cost to apply to a job."""
        job = await self.get_job(platform_job_id)
        return job.platform_cost or PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=0.0,
            currency="USD",
            is_free=True,
        )

    async def check_limits(self) -> PlatformLimits:
        """Check current platform limits."""
        account = await self.get_account_status()
        return account.limits

    async def get_economics_engine(self) -> UpworkEconomicsEngine:
        """
        Get the economics engine for Upwork.

        Returns:
            UpworkEconomicsEngine instance with current account data
        """
        account = await self.get_account_status()
        
        # Update economics engine with current account data
        account_data = {
            "connects_available": account.limits.credits_available,
            "connects_total": account.limits.credits_total,
            "daily_applications_used": account.metadata.get("daily_applications_used", 0),
            "daily_application_limit": account.limits.daily_application_limit or 50,
            "monthly_applications_used": account.metadata.get("monthly_applications_used", 0),
            "monthly_application_limit": account.limits.monthly_application_limit or 200,
        }
        
        self._economics_engine.update_account_data(account_data)
        return self._economics_engine

    async def _make_graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make a GraphQL request to Upwork API."""
        if not self._credentials.access_token:
            raise RuntimeError("No access token available")
        
        headers = {
            "Authorization": f"Bearer {self._credentials.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        return await self._client.post(
            self.GRAPHQL_URL,
            json=payload,
            headers=headers,
        )

    def _handle_api_error(self, response: httpx.Response) -> PlatformError:
        """Handle Upwork API errors and convert to PlatformError."""
        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = error_data.get("code", f"HTTP_{response.status_code}")
        except:
            error_message = f"HTTP {response.status_code} error"
            error_code = f"HTTP_{response.status_code}"
        
        # Determine error type
        is_auth_error = response.status_code == 401
        is_rate_limit = response.status_code == 429
        is_retriable = response.status_code in (429, 500, 502, 503, 504)
        
        return PlatformError(
            platform=self.platform,
            error_code=error_code,
            error_message=error_message,
            is_retriable=is_retriable,
            is_auth_error=is_auth_error,
            is_rate_limit=is_rate_limit,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
