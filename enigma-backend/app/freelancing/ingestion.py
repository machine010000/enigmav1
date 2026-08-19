"""Durable normalized marketplace opportunity ingestion.

Adapters provide facts; this service owns deterministic identity, deduplication,
and refresh semantics. It never contacts an external marketplace.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import MarketplaceJob


@dataclass(frozen=True)
class NormalizedMarketplaceOpportunity:
    platform: str
    platform_job_id: Optional[str]
    title: str
    description: str
    url: Optional[str] = None
    posted_at: Optional[datetime] = None
    currency: str = "USD"
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_type: Optional[str] = None
    skills: tuple[str, ...] = ()
    category: Optional[str] = None
    provider_metadata: Optional[dict[str, Any]] = None
    raw_metadata: Optional[dict[str, Any]] = None
    ingestion_source: Optional[str] = None


def normalized_fingerprint(opportunity: NormalizedMarketplaceOpportunity) -> str:
    stable = {
        "platform": opportunity.platform.strip().lower(),
        "url": (opportunity.url or "").strip().lower(),
        "title": " ".join(opportunity.title.lower().split()),
        "posted_at": opportunity.posted_at.isoformat() if opportunity.posted_at else "",
        "provider": (opportunity.provider_metadata or {}).get("external_id"),
        "budget_min": opportunity.budget_min,
        "budget_max": opportunity.budget_max,
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class IngestionResult:
    outcome: str
    job: MarketplaceJob


class MarketplaceOpportunityIngestionService:
    """Persist one normalized opportunity with PostgreSQL atomic deduplication."""

    async def ingest(
        self,
        db: AsyncSession,
        *,
        profile_id: str,
        opportunity: NormalizedMarketplaceOpportunity,
    ) -> IngestionResult:
        if not opportunity.platform.strip() or not opportunity.title.strip() or not opportunity.description.strip():
            raise ValueError("platform, title, and description are required")

        platform = opportunity.platform.strip().lower()
        platform_job_id = (opportunity.platform_job_id or "").strip() or None
        fingerprint = normalized_fingerprint(opportunity)
        existing = None
        if platform_job_id:
            existing = await db.scalar(select(MarketplaceJob).where(
                MarketplaceJob.profile_id == profile_id,
                MarketplaceJob.platform == platform,
                MarketplaceJob.platform_job_id == platform_job_id,
            ))
        else:
            existing = await db.scalar(select(MarketplaceJob).where(
                MarketplaceJob.profile_id == profile_id,
                MarketplaceJob.identity_fingerprint == fingerprint,
            ))

        now = datetime.utcnow()
        refreshed_fields = {
            "title": opportunity.title.strip(),
            "description": opportunity.description.strip(),
            "budget_min": opportunity.budget_min,
            "budget_max": opportunity.budget_max,
            "budget_type": opportunity.budget_type,
            "currency": opportunity.currency,
            "client_info": opportunity.provider_metadata or {},
            "skills_required": list(opportunity.skills),
            "job_type": opportunity.category,
            "posted_date": opportunity.posted_at,
            "url": opportunity.url,
            "job_metadata": opportunity.raw_metadata or {},
            "identity_fingerprint": fingerprint,
            "ingestion_source": opportunity.ingestion_source,
        }
        changed = bool(existing and any(getattr(existing, key) != value for key, value in refreshed_fields.items()))
        values = {
            "profile_id": profile_id,
            "job_id": existing.job_id if existing else str(uuid.uuid4()),
            "platform": platform,
            "platform_job_id": platform_job_id or fingerprint,
            **refreshed_fields,
            "lifecycle_status": existing.lifecycle_status if existing else "verification_pending",
            "identity_fingerprint": fingerprint,
            "first_seen_at": existing.first_seen_at if existing else now,
            "last_seen_at": now,
            "ingestion_source": opportunity.ingestion_source,
            "updated_at": now,
        }
        statement = insert(MarketplaceJob).values(**values)
        conflict_columns = ["profile_id", "platform", "platform_job_id"]
        update = {key: values[key] for key in ("title", "description", "budget_min", "budget_max", "budget_type", "currency", "client_info", "skills_required", "job_type", "posted_date", "url", "job_metadata", "identity_fingerprint", "last_seen_at", "ingestion_source", "updated_at")}
        if not platform_job_id:
            # The schema's canonical unique key remains platform_job_id; the
            # fingerprint is used as the deterministic fallback ID.
            conflict_columns = ["profile_id", "platform", "platform_job_id"]
        statement = statement.on_conflict_do_update(index_elements=conflict_columns, set_=update).returning(MarketplaceJob)
        row = (await db.execute(statement)).scalar_one()
        outcome = "CREATED" if existing is None else ("UPDATED" if changed else "EXISTING")
        return IngestionResult(outcome=outcome, job=row)