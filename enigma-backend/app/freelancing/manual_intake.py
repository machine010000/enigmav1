"""Durable, admin-operated manual marketplace opportunity intake.

No method in this module contacts a marketplace or performs submission.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import MarketplaceJob, ManualOpportunitySubmission

PROFILE_ID = "enigma_profile"
EDITABLE_STATES = {"draft", "ready_for_analysis", "analyzed", "proposal_prepared", "approved"}
OUTCOME_STATES = {"manually_submitted", "client_replied", "won", "lost", "withdrawn", "expired"}


class DuplicateOpportunityError(Exception):
    def __init__(self, existing_job_id: str):
        self.existing_job_id = existing_job_id
        super().__init__(f"Duplicate opportunity: {existing_job_id}")


class ManualOpportunityStateError(Exception):
    pass


def normalize_source_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError("source_url must be an absolute HTTP(S) URL")
    host = parts.hostname.lower() if parts.hostname else ""
    port = f":{parts.port}" if parts.port and not (parts.scheme.lower() == "http" and parts.port == 80) and not (parts.scheme.lower() == "https" and parts.port == 443) else ""
    path = parts.path.rstrip("/") or "/"
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")))
    return urlunsplit((parts.scheme.lower(), host + port, path, query, ""))


def fallback_fingerprint(platform: str, title: str, client_info: dict[str, Any]) -> str:
    stable = {
        "platform": platform.strip().lower(),
        "title": " ".join(title.lower().split()),
        "client": client_info.get("name") or client_info.get("username") or client_info.get("id") or "",
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ManualOpportunityService:
    async def find_duplicate(
        self, db: AsyncSession, *, platform: str, external_project_id: Optional[str],
        source_url: Optional[str], title: str, client_info: dict[str, Any], exclude_job_id: Optional[str] = None,
    ) -> Optional[MarketplaceJob]:
        conditions = []
        if external_project_id:
            conditions.append(MarketplaceJob.platform_job_id == external_project_id.strip())
        normalized_url = normalize_source_url(source_url)
        if normalized_url:
            conditions.append(MarketplaceJob.url == normalized_url)
        fingerprint = fallback_fingerprint(platform, title, client_info)
        conditions.append(MarketplaceJob.identity_fingerprint == fingerprint)
        for condition in conditions:
            query = select(MarketplaceJob).where(
                MarketplaceJob.profile_id == PROFILE_ID,
                MarketplaceJob.platform == platform.strip().lower(),
                condition,
            )
            if exclude_job_id:
                query = query.where(MarketplaceJob.job_id != exclude_job_id)
            found = await db.scalar(query)
            if found:
                return found
        return None

    async def create(self, db: AsyncSession, *, actor_id: str, data: dict[str, Any], analyze: bool = False) -> MarketplaceJob:
        duplicate = await self.find_duplicate(
            db, platform=data["platform"], external_project_id=data.get("external_project_id"),
            source_url=data.get("source_url"), title=data["title"], client_info=data.get("client_info") or {},
        )
        if duplicate:
            raise DuplicateOpportunityError(duplicate.job_id)
        now = datetime.utcnow()
        normalized_url = normalize_source_url(data.get("source_url"))
        fingerprint = fallback_fingerprint(data["platform"], data["title"], data.get("client_info") or {})
        job = MarketplaceJob(
            profile_id=PROFILE_ID,
            job_id=str(uuid.uuid4()),
            platform=data["platform"].strip().lower(),
            platform_job_id=(data.get("external_project_id") or fingerprint).strip(),
            title=data["title"].strip(),
            description=data["original_description"],
            original_text=data["original_description"],
            normalized_requirements=data.get("normalized_requirements") or {"requirements": [], "summary": ""},
            budget_type=data.get("budget_type"), budget_min=data.get("budget_min"), budget_max=data.get("budget_max"),
            currency=data["currency"].upper(), skills_required=data.get("required_skills") or [],
            client_info=data.get("client_info") or {}, url=normalized_url,
            source_language=data["source_language"], customer_preferred_language=data["customer_preferred_language"],
            proposal_language=data["proposal_language"], translation_metadata=data.get("translation_metadata") or {},
            ingestion_source="manual", lifecycle_status="ready_for_analysis" if analyze else "draft",
            identity_fingerprint=fingerprint, created_by_user_id=actor_id,
            first_seen_at=now, last_seen_at=now, job_metadata={"ingestion_method": "manual", "no_live_api_connection": True},
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def get(self, db: AsyncSession, job_id: str) -> Optional[MarketplaceJob]:
        return await db.scalar(select(MarketplaceJob).where(
            MarketplaceJob.profile_id == PROFILE_ID, MarketplaceJob.job_id == job_id,
            MarketplaceJob.ingestion_source == "manual",
        ))

    async def list(self, db: AsyncSession) -> list[MarketplaceJob]:
        result = await db.execute(select(MarketplaceJob).where(
            MarketplaceJob.profile_id == PROFILE_ID, MarketplaceJob.ingestion_source == "manual",
        ).order_by(MarketplaceJob.updated_at.desc()))
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, *, job: MarketplaceJob, data: dict[str, Any]) -> MarketplaceJob:
        if job.lifecycle_status not in EDITABLE_STATES:
            raise ManualOpportunityStateError("Opportunity is immutable after manual submission")
        platform = data.get("platform", job.platform)
        title = data.get("title", job.title)
        client_info = data.get("client_info", job.client_info or {})
        external_id = data.get("external_project_id", job.platform_job_id)
        source_url = data.get("source_url", job.url)
        duplicate = await self.find_duplicate(db, platform=platform, external_project_id=external_id, source_url=source_url, title=title, client_info=client_info, exclude_job_id=job.job_id)
        if duplicate:
            raise DuplicateOpportunityError(duplicate.job_id)
        mapping = {
            "platform": "platform", "title": "title", "original_description": "description",
            "normalized_requirements": "normalized_requirements", "budget_type": "budget_type",
            "budget_min": "budget_min", "budget_max": "budget_max", "currency": "currency",
            "required_skills": "skills_required", "client_info": "client_info", "source_language": "source_language",
            "customer_preferred_language": "customer_preferred_language", "proposal_language": "proposal_language",
            "translation_metadata": "translation_metadata", "lifecycle_status": "lifecycle_status",
        }
        for source, target in mapping.items():
            if source in data and data[source] is not None:
                setattr(job, target, data[source])
        if "original_description" in data:
            job.original_text = data["original_description"]
        if "source_url" in data:
            job.url = normalize_source_url(data["source_url"])
        if "external_project_id" in data and data["external_project_id"]:
            job.platform_job_id = data["external_project_id"].strip()
        job.identity_fingerprint = fallback_fingerprint(platform, title, client_info)
        job.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(job)
        return job

    async def record_submission(self, db: AsyncSession, *, job: MarketplaceJob, actor_id: str, data: dict[str, Any]) -> ManualOpportunitySubmission:
        if job.lifecycle_status not in {"approved", "proposal_prepared"}:
            raise ManualOpportunityStateError("Opportunity must have an approved or prepared proposal before manual submission")
        existing = await db.scalar(select(ManualOpportunitySubmission).where(
            ManualOpportunitySubmission.profile_id == PROFILE_ID, ManualOpportunitySubmission.job_id == job.job_id,
        ))
        if existing:
            raise ManualOpportunityStateError("Manual submission snapshot already exists")
        record = ManualOpportunitySubmission(
            profile_id=PROFILE_ID, job_id=job.job_id, created_by_user_id=actor_id,
            marketplace_proposal_id=data.get("marketplace_proposal_id"), submitted_at=data.get("submitted_at") or datetime.utcnow(),
            proposal_text_snapshot=data["proposal_text"], submitted_price=data.get("submitted_price"),
            currency=data["currency"].upper(), delivery_estimate=data.get("delivery_estimate"),
            outcome_status="manually_submitted", admin_notes=data.get("admin_notes"),
        )
        db.add(record)
        job.lifecycle_status = "manually_submitted"
        await db.commit()
        await db.refresh(record)
        return record

    async def update_outcome(self, db: AsyncSession, *, job: MarketplaceJob, outcome: str, notes: Optional[str]) -> ManualOpportunitySubmission:
        if outcome not in OUTCOME_STATES:
            raise ManualOpportunityStateError("Invalid manual submission outcome")
        record = await db.scalar(select(ManualOpportunitySubmission).where(
            ManualOpportunitySubmission.profile_id == PROFILE_ID, ManualOpportunitySubmission.job_id == job.job_id,
        ))
        if not record:
            raise ManualOpportunityStateError("Manual submission snapshot does not exist")
        record.outcome_status = outcome
        if notes is not None:
            record.admin_notes = notes
        record.updated_at = datetime.utcnow()
        job.lifecycle_status = outcome
        await db.commit()
        await db.refresh(record)
        return record
