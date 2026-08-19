"""Future marketplace adapter boundary.

Adapters retrieve and normalize marketplace facts only. They do not assess,
train, decide, or submit applications.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.freelancing.ingestion import NormalizedMarketplaceOpportunity


class MarketplaceOpportunityAdapter(ABC):
    @abstractmethod
    async def discover_opportunities(self, *, limit: int = 50) -> List[NormalizedMarketplaceOpportunity]:
        """Return normalized facts from a trusted marketplace integration."""
        raise NotImplementedError

    async def fetch_opportunity(self, platform_job_id: str) -> Optional[NormalizedMarketplaceOpportunity]:
        return None

    async def fetch_provider(self, provider_external_id: str) -> Optional[dict]:
        return None