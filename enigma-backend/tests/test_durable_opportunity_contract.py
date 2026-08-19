from datetime import datetime

from app.freelancing.adapter_contract import MarketplaceOpportunityAdapter
from app.freelancing.ingestion import NormalizedMarketplaceOpportunity, normalized_fingerprint


def test_fallback_fingerprint_is_deterministic_and_normalized():
    first = NormalizedMarketplaceOpportunity(
        platform=" UpWork ", platform_job_id=None, title="SEO  Audit", description="desc",
        url="HTTPS://example.test/job/1", posted_at=datetime(2026, 1, 1),
        provider_metadata={"external_id": "client-1"}, budget_max=100,
    )
    second = NormalizedMarketplaceOpportunity(
        platform="upwork", platform_job_id=None, title="seo audit", description="other",
        url="https://example.test/job/1", posted_at=datetime(2026, 1, 1),
        provider_metadata={"external_id": "client-1"}, budget_max=100,
    )
    assert normalized_fingerprint(first) == normalized_fingerprint(second)


def test_adapter_contract_has_no_decision_or_submission_methods():
    names = set(dir(MarketplaceOpportunityAdapter))
    assert "discover_opportunities" in names
    assert "fetch_opportunity" in names
    assert "fetch_provider" in names
    assert "submit_application" not in names
    assert "assess" not in names