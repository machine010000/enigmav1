"""Offline-testable orchestration for read-only Freelancer discovery."""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.freelancing.adapter_contract import MarketplaceOpportunityAdapter
from app.freelancing.freelancer_adapter import FreelancerMarketplaceAdapter
from app.freelancing.ingestion import (
    MarketplaceOpportunityIngestionService,
    NormalizedMarketplaceOpportunity,
)

logger = logging.getLogger(__name__)
PROFILE_ID = "enigma_profile"


class FreelancerNotConfiguredError(RuntimeError):
    """Raised when an administrator requests sync without an environment token."""


@dataclass(frozen=True)
class FreelancerConnectionStatus:
    platform: str
    state: str
    configured: bool
    sandbox: bool
    last_sync_at: Optional[str] = None
    last_error_code: Optional[str] = None


@dataclass(frozen=True)
class FreelancerSyncSummary:
    state: str
    created: int
    updated: int
    existing: int
    skipped: int
    failed: int
    discovered: int
    completed_at: str
    query_applied: bool
    skills_count: int
    limit: int

    def to_dict(self) -> dict:
        return asdict(self)


AdapterFactory = Callable[[str, bool], MarketplaceOpportunityAdapter]


class FreelancerDiscoveryService:
    """Connect the configured adapter to durable opportunity ingestion."""

    def __init__(
        self,
        settings: Settings,
        *,
        adapter_factory: Optional[AdapterFactory] = None,
        ingestion_service: Optional[MarketplaceOpportunityIngestionService] = None,
    ) -> None:
        self.settings = settings
        self._adapter_factory = adapter_factory or (
            lambda token, sandbox: FreelancerMarketplaceAdapter(token, sandbox=sandbox)
        )
        self._ingestion = ingestion_service or MarketplaceOpportunityIngestionService()
        self._last_summary: Optional[FreelancerSyncSummary] = None
        self._last_error_code: Optional[str] = None

    def connection_status(self) -> FreelancerConnectionStatus:
        configured = bool(self.settings.FREELANCER_API_TOKEN.strip())
        if not configured:
            state = "not_configured"
        elif self._last_error_code:
            state = "error"
        elif self._last_summary:
            state = "connected"
        else:
            state = "configured"
        return FreelancerConnectionStatus(
            platform="freelancer",
            state=state,
            configured=configured,
            sandbox=self.settings.FREELANCER_SANDBOX,
            last_sync_at=self._last_summary.completed_at if self._last_summary else None,
            last_error_code=self._last_error_code,
        )

    def last_summary(self) -> Optional[dict]:
        return self._last_summary.to_dict() if self._last_summary else None

    def record_upstream_error(self, code: str) -> None:
        self._last_error_code = code

    async def sync(
        self,
        db: AsyncSession,
        *,
        query: Optional[str],
        skills: list[str],
        limit: int,
    ) -> dict:
        token = self.settings.FREELANCER_API_TOKEN.strip()
        if not token:
            raise FreelancerNotConfiguredError("Freelancer integration is not configured")

        adapter = self._adapter_factory(token, self.settings.FREELANCER_SANDBOX)
        counts = {"created": 0, "updated": 0, "existing": 0, "skipped": 0, "failed": 0}
        try:
            opportunities = await adapter.discover_opportunities(
                query=query or None,
                skills=skills or None,
                limit=limit,
            )
            counts["skipped"] += int(getattr(adapter, "discovery_skipped_count", 0))
            for opportunity in opportunities:
                if not self._valid_opportunity(opportunity):
                    counts["skipped"] += 1
                    continue
                try:
                    async with db.begin_nested():
                        result = await self._ingestion.ingest(
                            db,
                            profile_id=PROFILE_ID,
                            opportunity=opportunity,
                        )
                    counts[result.outcome.lower()] += 1
                except ValueError:
                    counts["skipped"] += 1
                except Exception as exc:
                    counts["failed"] += 1
                    logger.warning(
                        "freelancer_record_ingestion_failed",
                        extra={"error_type": type(exc).__name__, "platform": "freelancer"},
                    )

            await db.commit()
            completed_at = datetime.utcnow().isoformat()
            summary = FreelancerSyncSummary(
                state="partial_failure" if counts["failed"] or counts["skipped"] else "success",
                discovered=len(opportunities) + int(getattr(adapter, "discovery_skipped_count", 0)),
                completed_at=completed_at,
                query_applied=bool(query),
                skills_count=len(skills),
                limit=limit,
                **counts,
            )
            self._last_summary = summary
            self._last_error_code = None
            logger.info(
                "freelancer_sync_completed",
                extra={"platform": "freelancer", **summary.to_dict()},
            )
            return summary.to_dict()
        except Exception:
            await db.rollback()
            raise
        finally:
            close = getattr(adapter, "close", None)
            if close:
                await close()

    @staticmethod
    def _valid_opportunity(opportunity: object) -> bool:
        return bool(
            isinstance(opportunity, NormalizedMarketplaceOpportunity)
            and opportunity.platform.strip().lower() == "freelancer"
            and opportunity.title.strip()
            and opportunity.description.strip()
        )
