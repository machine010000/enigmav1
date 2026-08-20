"""Tests for Freelancer adapter without requiring live credentials.

Uses mocked HTTP responses to validate normalization and error handling.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.freelancing.freelancer_adapter import FreelancerMarketplaceAdapter
from app.freelancing.freelancer_client import (
    FreelancerClient,
    FreelancerClientError,
    FreelancerUnauthorized,
    FreelancerNotFound,
)
from app.freelancing.ingestion import NormalizedMarketplaceOpportunity


# ============================================================================
# Mock API Response Fixtures
# ============================================================================


MOCK_PROJECT_RESPONSE = {
    "project": {
        "id": 12345,
        "title": "Build React Dashboard",
        "description": "Need a React-based analytics dashboard with real-time data",
        "preview_url": "https://www.freelancer.com/projects/react/build-react-dashboard",
        "status": "open",
        "type": "fixed",
        "bid_count": 5,
        "time_submitted": 1692720000,  # 2023-08-22
        "time_free_bids_expire": 1692806400,
        "budget": {"minimum": 500.0, "maximum": 2000.0},
        "currency": {"code": "USD", "sign": "$"},
        "jobs": [
            {"id": 1, "name": "React"},
            {"id": 2, "name": "JavaScript"},
            {"id": 3, "name": "REST API"},
        ],
        "category": {"id": 3, "name": "Web Development"},
        "owner": {
            "id": 98765,
            "username": "acmecorp",
            "display_name": "ACME Corp",
            "location": {"city": "San Francisco", "country": {"name": "United States", "flag_url": "..."}},
            "badge": {"verified": True},
        },
        "attachments": [{"filename": "spec.pdf"}],
    }
}

MOCK_SEARCH_RESPONSE = {
    "projects": [
        {
            "id": 12345,
            "title": "Build React Dashboard",
            "description": "Need a React-based analytics dashboard",
            "preview_url": "https://www.freelancer.com/projects/react/build-react-dashboard",
            "status": "open",
            "type": "fixed",
            "bid_count": 5,
            "time_submitted": 1692720000,
            "budget": {"minimum": 500.0, "maximum": 2000.0},
            "currency": {"code": "USD", "sign": "$"},
            "jobs": [{"id": 1, "name": "React"}, {"id": 2, "name": "JavaScript"}],
            "category": {"id": 3, "name": "Web Development"},
            "owner": {
                "id": 98765,
                "username": "acmecorp",
                "display_name": "ACME Corp",
                "location": {"city": "San Francisco", "country": {"name": "United States"}},
                "badge": {"verified": True},
            },
            "attachments": [],
        },
        {
            "id": 12346,
            "title": "Python Data Scraper",
            "description": "Need Python script to scrape data from website",
            "preview_url": "https://www.freelancer.com/projects/python/data-scraper",
            "status": "open",
            "type": "hourly",
            "bid_count": 3,
            "time_submitted": 1692633600,
            "budget": {"minimum": 50.0, "maximum": 75.0},
            "currency": {"code": "USD", "sign": "$"},
            "jobs": [{"id": 8, "name": "Python"}],
            "category": {"id": 1, "name": "Programming"},
            "owner": {
                "id": 98766,
                "username": "startup_xyz",
                "display_name": "Startup XYZ",
                "location": {"city": "Austin", "country": {"name": "United States"}},
                "badge": {"verified": False},
            },
            "attachments": [],
        },
    ],
    "total_count": 2,
}

MOCK_USER_RESPONSE = {
    "user": {
        "id": 98765,
        "username": "acmecorp",
        "display_name": "ACME Corp",
        "location": {"city": "San Francisco", "country": {"name": "United States", "flag_url": "..."}},
        "badge": {"verified": True, "endorsed": False},
        "profile_description": "Professional development team",
        "registration_date": 1500000000,
    }
}

MOCK_REPUTATION_RESPONSE = {
    "reputation": {
        "rating": 4.8,
        "reviews_count": 23,
        "score": 480,
        "comment_count": 15,
    }
}


# ============================================================================
# Test FreelancerClient
# ============================================================================


@pytest.mark.asyncio
async def test_client_initialization_with_empty_token():
    """Client should reject empty token."""
    with pytest.raises(FreelancerClientError, match="Token is required"):
        FreelancerClient("")

    with pytest.raises(FreelancerClientError, match="Token is required"):
        FreelancerClient("   ")


@pytest.mark.asyncio
async def test_client_sandbox_url():
    """Client should use sandbox URL when requested."""
    client = FreelancerClient("test_token", sandbox=True)
    assert client.base_url == "https://sandbox.api.freelancer.com"

    client_prod = FreelancerClient("test_token", sandbox=False)
    assert client_prod.base_url == "https://api.freelancer.com"


@pytest.mark.asyncio
async def test_client_uses_official_freelancer_auth_header():
    """Client must send the official Freelancer PAT header format."""
    client = FreelancerClient("test_token")

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_client = MagicMock()
        mock_async_client.return_value = mock_client

        await client._get_client()

        mock_async_client.assert_called_once_with(
            base_url="https://api.freelancer.com",
            headers={"Freelancer-OAuth-V1": "test_token"},
            timeout=30.0,
        )


@pytest.mark.asyncio
async def test_client_unauthorized_response():
    """Client should raise FreelancerUnauthorized on 401."""
    client = FreelancerClient("invalid_token")

    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with pytest.raises(FreelancerUnauthorized):
            await client._request("GET", "/projects/123")


@pytest.mark.asyncio
async def test_client_not_found_response():
    """Client should raise FreelancerNotFound on 404."""
    client = FreelancerClient("token")

    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with pytest.raises(FreelancerNotFound):
            await client._request("GET", "/projects/999")


@pytest.mark.asyncio
async def test_client_rate_limit_response():
    """Client should raise FreelancerRateLimited on 429."""
    client = FreelancerClient("token")

    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_request.return_value = mock_response

        with pytest.raises(FreelancerClientError, match="Rate limit"):
            await client._request("GET", "/projects")


# ============================================================================
# Test FreelancerMarketplaceAdapter
# ============================================================================


@pytest.mark.asyncio
async def test_adapter_initialization():
    """Adapter should initialize with valid token."""
    adapter = FreelancerMarketplaceAdapter("test_token")
    assert adapter.token == "test_token"
    assert adapter.sandbox is False
    await adapter.close()


@pytest.mark.asyncio
async def test_adapter_initialization_empty_token():
    """Adapter should reject empty token."""
    with pytest.raises(ValueError, match="token is required"):
        FreelancerMarketplaceAdapter("")


@pytest.mark.asyncio
async def test_adapter_sandbox_mode():
    """Adapter should pass sandbox flag to client."""
    adapter = FreelancerMarketplaceAdapter("test_token", sandbox=True)
    assert adapter.sandbox is True
    assert adapter.client.sandbox is True
    await adapter.close()


@pytest.mark.asyncio
async def test_discover_opportunities_normalization():
    """discover_opportunities should normalize Freelancer projects correctly."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "search_projects", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_SEARCH_RESPONSE

        opportunities = await adapter.discover_opportunities(query="react", limit=50)

        assert len(opportunities) == 2
        assert all(isinstance(o, NormalizedMarketplaceOpportunity) for o in opportunities)

        # First project
        opp1 = opportunities[0]
        assert opp1.platform == "freelancer"
        assert opp1.platform_job_id == "12345"
        assert opp1.title == "Build React Dashboard"
        assert opp1.currency == "USD"
        assert opp1.budget_min == 500.0
        assert opp1.budget_max == 2000.0
        assert opp1.budget_type == "fixed"
        assert "React" in opp1.skills
        assert "JavaScript" in opp1.skills
        assert opp1.category == "Web Development"
        assert opp1.provider_metadata["username"] == "acmecorp"
        assert opp1.provider_metadata["verified"] is True
        assert opp1.posted_at == datetime.utcfromtimestamp(1692720000)

        # Second project
        opp2 = opportunities[1]
        assert opp2.platform_job_id == "12346"
        assert opp2.budget_type == "hourly"
        assert opp2.provider_metadata["verified"] is False

    await adapter.close()


@pytest.mark.asyncio
async def test_discover_opportunities_missing_optional_fields():
    """discover_opportunities should handle missing optional fields gracefully."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    minimal_response = {
        "projects": [
            {
                "id": 999,
                "title": "Minimal Project",
                "description": "Minimal description",
                # Missing: budget, currency, jobs, category, owner, attachments
            }
        ]
    }

    with patch.object(adapter.client, "search_projects", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = minimal_response

        opportunities = await adapter.discover_opportunities()

        assert len(opportunities) == 1
        opp = opportunities[0]
        assert opp.platform_job_id == "999"
        assert opp.title == "Minimal Project"
        assert opp.currency == "USD"  # Default
        assert opp.budget_min is None
        assert opp.budget_max is None
        assert opp.budget_type is None
        assert len(opp.skills) == 0
        assert opp.category is None
        assert opp.provider_metadata is None

    await adapter.close()


@pytest.mark.asyncio
async def test_discover_opportunities_api_error():
    """discover_opportunities should raise FreelancerClientError on API failure."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "search_projects", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = FreelancerClientError("API error")

        with pytest.raises(FreelancerClientError, match="API error"):
            await adapter.discover_opportunities()

    await adapter.close()


@pytest.mark.asyncio
async def test_discover_opportunities_unauthorized():
    """discover_opportunities should raise FreelancerUnauthorized on 401."""
    adapter = FreelancerMarketplaceAdapter("invalid_token")

    with patch.object(adapter.client, "search_projects", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = FreelancerUnauthorized("Token invalid")

        with pytest.raises(FreelancerUnauthorized):
            await adapter.discover_opportunities()

    await adapter.close()


@pytest.mark.asyncio
async def test_fetch_opportunity():
    """fetch_opportunity should return normalized project."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "get_project", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_PROJECT_RESPONSE

        opp = await adapter.fetch_opportunity("12345")

        assert opp is not None
        assert opp.platform_job_id == "12345"
        assert opp.title == "Build React Dashboard"
        assert opp.platform == "freelancer"

    await adapter.close()


@pytest.mark.asyncio
async def test_fetch_opportunity_not_found():
    """fetch_opportunity should return None if project not found."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "get_project", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = FreelancerNotFound("Project not found")

        opp = await adapter.fetch_opportunity("999")

        assert opp is None

    await adapter.close()


@pytest.mark.asyncio
async def test_fetch_opportunity_empty_response():
    """fetch_opportunity should return None if response is empty."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "get_project", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"project": None}

        opp = await adapter.fetch_opportunity("12345")

        assert opp is None

    await adapter.close()


@pytest.mark.asyncio
async def test_fetch_provider():
    """fetch_provider should return normalized user metadata."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "get_user", new_callable=AsyncMock) as mock_user, \
         patch.object(adapter.client, "get_user_reputation", new_callable=AsyncMock) as mock_rep:

        mock_user.return_value = MOCK_USER_RESPONSE
        mock_rep.return_value = MOCK_REPUTATION_RESPONSE

        provider = await adapter.fetch_provider("98765")

        assert provider is not None
        assert provider["external_id"] == "98765"
        assert provider["username"] == "acmecorp"
        assert provider["display_name"] == "ACME Corp"
        assert provider["location_city"] == "San Francisco"
        assert provider["verified"] is True
        assert provider["rating"] == 4.8
        assert provider["review_count"] == 23

    await adapter.close()


@pytest.mark.asyncio
async def test_fetch_provider_reputation_unavailable():
    """fetch_provider should handle missing reputation gracefully."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "get_user", new_callable=AsyncMock) as mock_user, \
         patch.object(adapter.client, "get_user_reputation", new_callable=AsyncMock) as mock_rep:

        mock_user.return_value = MOCK_USER_RESPONSE
        mock_rep.side_effect = FreelancerClientError("Reputation unavailable")

        provider = await adapter.fetch_provider("98765")

        assert provider is not None
        assert provider["rating"] is None
        assert provider["review_count"] is None

    await adapter.close()


@pytest.mark.asyncio
async def test_fetch_provider_not_found():
    """fetch_provider should return None if user not found."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "get_user", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = FreelancerNotFound("User not found")

        provider = await adapter.fetch_provider("999")

        assert provider is None

    await adapter.close()


@pytest.mark.asyncio
async def test_normalization_safe_float():
    """Adapter should safely convert floats."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    # Valid float
    assert adapter._safe_float(123.45) == 123.45
    assert adapter._safe_float("123.45") == 123.45

    # Invalid/None
    assert adapter._safe_float(None) is None
    assert adapter._safe_float("invalid") is None
    assert adapter._safe_float({}) is None


@pytest.mark.asyncio
async def test_deduplication_same_project_twice():
    """Same Freelancer project discovered twice should create same durable row.

    This is verified through the ingestion service contract, not the adapter.
    The adapter should return the same normalized form.
    """
    adapter = FreelancerMarketplaceAdapter("test_token")

    with patch.object(adapter.client, "search_projects", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_SEARCH_RESPONSE

        opp1_list = await adapter.discover_opportunities()
        opp1_list = await adapter.discover_opportunities()

        opp1 = opp1_list[0]
        opp1_again = opp1_list[0]

        # Same project should have same identifier
        assert opp1.platform_job_id == opp1_again.platform_job_id
        assert opp1.platform == opp1_again.platform

    await adapter.close()


@pytest.mark.asyncio
async def test_no_write_methods_exposed():
    """Adapter should not have write methods."""
    adapter = FreelancerMarketplaceAdapter("test_token")

    # Only read methods should be public
    public_methods = [m for m in dir(adapter) if not m.startswith("_") and callable(getattr(adapter, m))]

    # No methods for bidding, messaging, etc.
    forbidden = [
        "create_bid",
        "award_bid",
        "send_message",
        "create_project",
        "create_milestone",
        "post_project",
        "update_project",
        "delete_project",
    ]

    for forbidden_method in forbidden:
        assert forbidden_method not in public_methods, f"Adapter should not expose {forbidden_method}"

    await adapter.close()


@pytest.mark.asyncio
async def test_context_manager():
    """Adapter should support async context manager."""
    async with FreelancerMarketplaceAdapter("test_token") as adapter:
        assert adapter.token == "test_token"
