"""
Controlled Application Package — TASK-050/051

Converts a verified ready_to_apply assessment into a reviewable application
package grounded exclusively in authoritative profile/evidence data, and
provides durable persistence + human-review lifecycle.

Architecture contracts:
  TASK-050 (generation):
  - State stops at READY_FOR_HUMAN_APPROVAL. Never SUBMITTED.
  - Every capability claim traces to a persisted KnowledgeProgress row.
  - Unsupported claims are rejected before the package is returned.
  - Cross-user evidence cannot appear (ownership enforced by DB query).
  - Package generation does NOT touch KnowledgeProgress — not a learning event.
  - Stale assessment protection: readiness is re-evaluated server-side; client
    cannot inject a forged "ready_to_apply" string.
  - AI (LLM) is used for proposal text generation only; deterministic validation
    runs after AI output and can reject or sanitise it.

  TASK-051 (persistence + review):
  - Package is persisted to controlled_application_packages table before return.
  - Fingerprint (SHA-256 of user_id+opportunity_id+sorted_caps) prevents
    duplicate same-intent drafts from identical retries (idempotent draft reuse).
  - Human review endpoint: APPROVE or REJECT from READY_FOR_HUMAN_APPROVAL only.
  - APPROVE triggers a fresh server-side readiness re-check; stale claim detected
    → stale_on_approval_attempt=True, state remains READY_FOR_HUMAN_APPROVAL.
  - REJECT does NOT re-check readiness. State moves to REJECTED immediately.
  - Duplicate/conflicting review blocked: only READY_FOR_HUMAN_APPROVAL can
    transition; already APPROVED/REJECTED returns an explicit error.
  - All reads/reviews scoped to authenticated user_id (ownership isolation).
  - EXTERNAL_SUBMISSION_CALLABLE: NO — no call path to MarketplaceAdapter.
  - Learning is never mutated by generation, retrieval, approval, or rejection.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import gateway
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.engine.capability_catalog import capability_catalog
from app.freelancing.assessment_service import OpportunityAssessmentService
from app.freelancing.contracts import (
    ApplicationMode,
    BrainDecisionType,
    FreelanceOpportunity,
    ReadinessState,
)
from app.models.controlled_application import ControlledApplicationPackageRecord
from app.models.enigma_profile import CapabilityStatus, KnowledgeProgress
from app.models.product import Product
from app.models.user import User

logger = get_logger(__name__)
_settings = get_settings()
_assessment_service = OpportunityAssessmentService()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROPOSAL_MODEL = "meta/llama-3.1-8b-instruct"
PROPOSAL_MAX_TOKENS = 600
PROPOSAL_TIMEOUT = 60
PROPOSAL_TEMPERATURE = 0.3


# ---------------------------------------------------------------------------
# Package state — never transitions past READY_FOR_HUMAN_APPROVAL automatically
# ---------------------------------------------------------------------------

class PackageState(str, Enum):
    READY_FOR_HUMAN_APPROVAL = "READY_FOR_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    # SUBMITTED is intentionally absent from TASK-051.


# ---------------------------------------------------------------------------
# Review decision constants
# ---------------------------------------------------------------------------

REVIEW_APPROVE = "approve"
REVIEW_REJECT = "reject"


# ---------------------------------------------------------------------------
# Domain models (in-process, returned to API callers)
# ---------------------------------------------------------------------------

@dataclass
class CapabilityClaim:
    """
    A single verified capability claim.

    All values are loaded from the authoritative profile snapshot.
    No invented numbers, certifications, or history.
    """
    capability_id: str
    capability_name: str
    status: str
    confidence: float
    evidence_count: int
    successful_executions: int
    threshold: float
    meets_threshold: bool
    claim_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "status": self.status,
            "confidence": round(self.confidence, 4),
            "evidence_count": self.evidence_count,
            "successful_executions": self.successful_executions,
            "threshold": self.threshold,
            "meets_threshold": self.meets_threshold,
            "claim_text": self.claim_text,
        }


@dataclass
class EvidenceSummary:
    """
    Aggregate summary of evidence backing the package.
    """
    capability_id: str
    total_evidence: int
    successful_executions: int
    failed_executions: int
    confidence: float
    threshold: float
    meets_threshold: bool
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "total_evidence": self.total_evidence,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "confidence": round(self.confidence, 4),
            "threshold": self.threshold,
            "meets_threshold": self.meets_threshold,
            "status": self.status,
        }


@dataclass
class ControlledApplicationPackage:
    """
    Reviewable application package.

    After TASK-051 this object always corresponds to a persisted DB row.
    State follows PackageState enum.
    """
    application_id: str
    opportunity_id: str
    opportunity_title: str
    platform: str
    required_capabilities: List[str]
    readiness_decision: str
    readiness_score: float
    matched_capabilities: List[str]
    proposal_text: str
    capability_claims: List[CapabilityClaim]
    evidence_summary: List[EvidenceSummary]
    known_limitations: List[str]
    state: PackageState
    created_at: datetime
    # Review fields (populated after review action)
    reviewed_at: Optional[datetime] = None
    review_decision: Optional[str] = None
    review_note: Optional[str] = None
    # Stale flag (set if APPROVE attempted on stale profile)
    stale_on_approval_attempt: bool = False
    # Persistence note — always truthful
    PERSISTENCE_BOUNDARY: str = (
        "Package is durably persisted in controlled_application_packages table. "
        "State is READY_FOR_HUMAN_APPROVAL until explicitly reviewed. "
        "This package is NOT automatically submitted to any external platform."
    )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "application_id": self.application_id,
            "opportunity_id": self.opportunity_id,
            "opportunity_title": self.opportunity_title,
            "platform": self.platform,
            "required_capabilities": self.required_capabilities,
            "readiness_decision": self.readiness_decision,
            "readiness_score": round(self.readiness_score, 4),
            "matched_capabilities": self.matched_capabilities,
            "proposal_text": self.proposal_text,
            "capability_claims": [c.to_dict() for c in self.capability_claims],
            "evidence_summary": [e.to_dict() for e in self.evidence_summary],
            "known_limitations": self.known_limitations,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "persistence_boundary": self.PERSISTENCE_BOUNDARY,
        }
        if self.reviewed_at:
            d["reviewed_at"] = self.reviewed_at.isoformat()
        if self.review_decision:
            d["review_decision"] = self.review_decision
        if self.review_note:
            d["review_note"] = self.review_note
        if self.stale_on_approval_attempt:
            d["stale_on_approval_attempt"] = True
        return d


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ClaimGroundingError(Exception):
    """Raised when a capability claim cannot be grounded in profile data."""


class ReadinessGateError(Exception):
    """Raised when the opportunity does not meet ready_to_apply."""
    def __init__(
        self,
        message: str,
        decision: str,
        blocking_capability: Optional[str] = None,
    ):
        super().__init__(message)
        self.decision = decision
        self.blocking_capability = blocking_capability


class OwnershipError(Exception):
    """Raised when cross-user data access is attempted."""


class PackageNotFoundError(Exception):
    """Raised when a package is not found (or belongs to another user)."""


class ReviewStateError(Exception):
    """Raised when a review transition is not permitted."""


class StaleReadinessError(Exception):
    """
    Raised when an APPROVE attempt detects the opportunity is no longer
    ready_to_apply based on a fresh server-side assessment.
    """
    def __init__(self, message: str, current_decision: str):
        super().__init__(message)
        self.current_decision = current_decision


# ---------------------------------------------------------------------------
# Claim grounding — deterministic, no AI
# ---------------------------------------------------------------------------

def _ground_claim(
    capability_id: str,
    profile_row: KnowledgeProgress,
) -> CapabilityClaim:
    """
    Build a CapabilityClaim from an authoritative KnowledgeProgress row.

    Allowed safe language based on the capability status only:
      - qualified / proven  → "I can help with …"
      - practicing          → raises ClaimGroundingError (below threshold)
    """
    entry = capability_catalog.get(capability_id)
    if entry is None:
        raise ClaimGroundingError(
            f"Capability '{capability_id}' is not in the catalog — "
            "unsupported claims cannot be included."
        )

    confidence = float(profile_row.confidence or 0.0)
    evidence_count = int(getattr(profile_row, "evidence_count", None) or 0)
    success_count = int(getattr(profile_row, "successful_execution_count", None) or 0)
    fail_count = int(getattr(profile_row, "failed_execution_count", None) or 0)
    status = (
        getattr(profile_row, "capability_status", None)
        or CapabilityStatus.UNKNOWN.value
    )
    threshold = entry.freelance_readiness_threshold
    meets = confidence >= threshold

    if not meets:
        raise ClaimGroundingError(
            f"Capability '{capability_id}' confidence {confidence:.4f} is below "
            f"threshold {threshold} — cannot be claimed in a ready_to_apply package."
        )

    if status in (CapabilityStatus.PROVEN.value, CapabilityStatus.QUALIFIED.value):
        claim_text = (
            f"I can help with {entry.name.lower()}: "
            f"verified across {evidence_count} evidence item(s) with "
            f"{success_count} successful execution(s)."
        )
    elif status == CapabilityStatus.PRACTICING.value:
        # practicing but somehow above threshold — allowed with hedged language
        claim_text = (
            f"I have developing capability in {entry.name.lower()}: "
            f"{evidence_count} evidence item(s) recorded, "
            f"confidence {confidence:.2f} (threshold {threshold})."
        )
    else:
        raise ClaimGroundingError(
            f"Capability '{capability_id}' has status '{status}' which does not "
            "support a positive claim."
        )

    return CapabilityClaim(
        capability_id=capability_id,
        capability_name=entry.name,
        status=status,
        confidence=confidence,
        evidence_count=evidence_count,
        successful_executions=success_count,
        threshold=threshold,
        meets_threshold=meets,
        claim_text=claim_text,
    )


def _build_evidence_summary(
    capability_id: str,
    profile_row: KnowledgeProgress,
) -> EvidenceSummary:
    entry = capability_catalog.get(capability_id)
    threshold = entry.freelance_readiness_threshold if entry else 0.65
    confidence = float(profile_row.confidence or 0.0)
    evidence_count = int(getattr(profile_row, "evidence_count", None) or 0)
    success_count = int(getattr(profile_row, "successful_execution_count", None) or 0)
    fail_count = int(getattr(profile_row, "failed_execution_count", None) or 0)
    status = (
        getattr(profile_row, "capability_status", None)
        or CapabilityStatus.UNKNOWN.value
    )

    return EvidenceSummary(
        capability_id=capability_id,
        total_evidence=evidence_count,
        successful_executions=success_count,
        failed_executions=fail_count,
        confidence=confidence,
        threshold=threshold,
        meets_threshold=confidence >= threshold,
        status=status,
    )


# ---------------------------------------------------------------------------
# Fingerprinting for idempotent draft reuse
# ---------------------------------------------------------------------------

def _opportunity_fingerprint(
    user_id: str,
    opportunity_id: str,
    required_capabilities: List[str],
) -> str:
    """
    SHA-256 hex fingerprint: user_id + opportunity_id + sorted capability list.

    Identical inputs → same fingerprint → existing READY_FOR_HUMAN_APPROVAL
    draft is reused rather than creating a duplicate.
    """
    key = "|".join([
        str(user_id),
        str(opportunity_id),
        ",".join(sorted(required_capabilities)),
    ])
    return hashlib.sha256(key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Proposal generator — AI-assisted, deterministically validated
# ---------------------------------------------------------------------------

def _safe_proposal_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _validate_proposal_text(
    text: str, claims: List[CapabilityClaim]
) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    if not text or not text.strip():
        return "", ["Proposal text was empty — using capability summary fallback."]

    banned_patterns = [
        r"\b\d+\s+years?\s+of\s+experience\b",
        r"\bprevious\s+clients?\b",
        r"\b\$[\d,]+\s+revenue\b",
        r"\bcertif(?:ied|ication)\b",
        r"\brated\b.*\b[\d.]+\s+stars?\b",
        r"\bportfolio\s+of\s+\d+",
        r"\bcompletion\s+rate\b",
        r"\btelesales?\b",
        r"\bpersonal\s+background\b",
        r"\bemployment\s+history\b",
        r"\bhired\s+\d+\s+times?\b",
    ]
    for pattern in banned_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(
                f"Proposal contained fabricated marker (pattern: {pattern!r}) — stripped."
            )
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)

    if claims:
        cap_names = [c.capability_name.lower() for c in claims]
        if not any(name.split()[0] in text.lower() for name in cap_names):
            warnings.append(
                "Proposal text did not reference matched capabilities — "
                "capability summary appended."
            )
            text += "\n\n" + " ".join(c.claim_text for c in claims)

    return text.strip(), warnings


async def _generate_proposal(
    opportunity_title: str,
    opportunity_description: str,
    claims: List[CapabilityClaim],
) -> Tuple[str, List[str]]:
    claim_lines = "\n".join(f"- {c.claim_text}" for c in claims)
    system = (
        "You are writing a concise professional freelance proposal.\n"
        "You must ONLY use information provided to you — do not invent:\n"
        "  - years of experience\n"
        "  - client names or history\n"
        "  - revenue or earnings\n"
        "  - certifications or ratings\n"
        "  - portfolio projects not described here\n"
        "  - completion rates\n"
        "Return JSON only:\n"
        '{"proposal_text": "..."}'
    )
    user = (
        f"Opportunity: {opportunity_title}\n\n"
        f"Description: {opportunity_description[:800]}\n\n"
        f"Verified capability claims to reference:\n{claim_lines}\n\n"
        "Write a concise professional proposal (150–300 words) covering:\n"
        "1. Understanding of the work\n"
        "2. Relevant capability and approach\n"
        "3. Quality / checking methodology\n"
        "4. Brief closing"
    )

    warnings: List[str] = []

    try:
        resp = await asyncio.wait_for(
            gateway.generate(
                system=system,
                user=user,
                temperature=PROPOSAL_TEMPERATURE,
                max_tokens=PROPOSAL_MAX_TOKENS,
                model=PROPOSAL_MODEL,
            ),
            timeout=PROPOSAL_TIMEOUT,
        )
        content = (
            resp.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        parsed = _safe_proposal_json(content)
        if parsed and parsed.get("proposal_text"):
            raw_text = str(parsed["proposal_text"]).strip()
        else:
            raw_text = content.strip()
            # Strip residual JSON wrapper if model returned it unparsed
            raw_text = re.sub(
                r'^[\s\{]*"proposal_text"\s*:\s*"',
                "",
                raw_text,
                flags=re.IGNORECASE,
            ).rstrip('"}').strip()
            if not raw_text:
                warnings.append(
                    "AI response was empty after stripping — using fallback."
                )

    except asyncio.TimeoutError:
        raw_text = ""
        warnings.append(
            "Proposal AI generation timed out — using capability summary fallback."
        )
    except Exception as exc:
        raw_text = ""
        warnings.append(
            f"Proposal AI generation failed ({exc!s}) — using fallback."
        )

    if not raw_text:
        raw_text = (
            f"I can help with {opportunity_title}.\n\n"
            + "\n".join(c.claim_text for c in claims)
            + "\n\nI will review the catalog data systematically, ensuring accuracy "
            "and consistency throughout."
        )

    validated_text, validation_warnings = _validate_proposal_text(raw_text, claims)
    warnings.extend(validation_warnings)
    return validated_text, warnings


# ---------------------------------------------------------------------------
# Ownership check
# ---------------------------------------------------------------------------

async def _verify_ownership(
    db: AsyncSession,
    user_id: str,
    target_id: Optional[str],
) -> Optional[Product]:
    if target_id is None:
        return None

    result = await db.execute(select(Product).where(Product.id == target_id))
    product = result.scalar_one_or_none()

    if product is None:
        raise OwnershipError(f"Product '{target_id}' not found.")
    if str(product.user_id) != str(user_id):
        raise OwnershipError(
            f"Product '{target_id}' does not belong to user '{user_id}'. "
            "Cross-user evidence cannot be included in a package."
        )
    return product


# ---------------------------------------------------------------------------
# DB record helpers
# ---------------------------------------------------------------------------

def _record_to_package(record: ControlledApplicationPackageRecord) -> ControlledApplicationPackage:
    """Hydrate a DB record into the in-process ControlledApplicationPackage."""
    claims = [
        CapabilityClaim(**c) for c in (record.capability_claims_snapshot or [])
    ]
    evidence = [
        EvidenceSummary(**e) for e in (record.evidence_summary_snapshot or [])
    ]
    return ControlledApplicationPackage(
        application_id=record.application_id,
        opportunity_id=record.opportunity_id,
        opportunity_title=record.opportunity_title,
        platform=record.platform,
        required_capabilities=record.required_capabilities or [],
        readiness_decision=record.readiness_decision,
        readiness_score=record.readiness_score,
        matched_capabilities=record.matched_capabilities or [],
        proposal_text=record.proposal_text or "",
        capability_claims=claims,
        evidence_summary=evidence,
        known_limitations=record.known_limitations or [],
        state=PackageState(record.state),
        created_at=record.created_at,
        reviewed_at=record.reviewed_at,
        review_decision=record.review_decision,
        review_note=record.review_note,
        stale_on_approval_attempt=bool(record.stale_on_approval_attempt),
    )


# ---------------------------------------------------------------------------
# Application Package Repository
# ---------------------------------------------------------------------------

class ControlledApplicationPackageRepository:
    """
    Thin async repository for ControlledApplicationPackageRecord.

    All queries are scoped to authenticated user_id — no cross-user reads.
    """

    async def get_by_application_id(
        self, db: AsyncSession, application_id: str, user_id: str
    ) -> Optional[ControlledApplicationPackageRecord]:
        result = await db.execute(
            select(ControlledApplicationPackageRecord).where(
                ControlledApplicationPackageRecord.application_id == application_id,
                ControlledApplicationPackageRecord.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_fingerprint(
        self,
        db: AsyncSession,
        user_id: str,
        fingerprint: str,
    ) -> Optional[ControlledApplicationPackageRecord]:
        """
        Return existing READY_FOR_HUMAN_APPROVAL record with the same fingerprint,
        if any. Used for idempotent draft reuse.
        """
        result = await db.execute(
            select(ControlledApplicationPackageRecord).where(
                ControlledApplicationPackageRecord.user_id == user_id,
                ControlledApplicationPackageRecord.opportunity_fingerprint == fingerprint,
                ControlledApplicationPackageRecord.state
                == PackageState.READY_FOR_HUMAN_APPROVAL.value,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ControlledApplicationPackageRecord]:
        result = await db.execute(
            select(ControlledApplicationPackageRecord)
            .where(ControlledApplicationPackageRecord.user_id == user_id)
            .order_by(ControlledApplicationPackageRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def save(
        self, db: AsyncSession, record: ControlledApplicationPackageRecord
    ) -> None:
        db.add(record)
        await db.flush()  # assign DB-generated values without committing session


_repo = ControlledApplicationPackageRepository()


# ---------------------------------------------------------------------------
# Application Package Service — canonical entry point
# ---------------------------------------------------------------------------

class ControlledApplicationPackageService:
    """
    Builds and manages ControlledApplicationPackage records.

    TASK-051 changes vs TASK-050:
      - build() now persists the package to the DB before returning.
      - Idempotent: repeated identical requests reuse existing READY_FOR_HUMAN_APPROVAL.
      - review() implements the APPROVE/REJECT state machine.
      - get_by_id() and list_for_user() provide read access (user-scoped).
      - APPROVE includes a fresh readiness re-check; stale claims are blocked.
      - No learning mutations in any path.
      - No external submission in any path.
    """

    def __init__(self) -> None:
        self._assessment_service = _assessment_service
        self._repo = _repo

    async def build(
        self,
        *,
        user: User,
        opportunity_title: str,
        opportunity_description: str,
        platform: str,
        required_skills: List[str],
        opportunity_id: Optional[str] = None,
        target_id: Optional[str] = None,
        db: AsyncSession,
    ) -> ControlledApplicationPackage:
        """
        Build and persist a controlled application package.

        Draft replay policy (TASK-051):
          Same user + same opportunity_id + same required_capabilities
          → fingerprint matches an existing READY_FOR_HUMAN_APPROVAL record
          → return the existing package without creating a duplicate.
          If the existing record was already reviewed (APPROVED/REJECTED),
          a new package is created (intentional new draft after review).

        Raises:
            ReadinessGateError   — if assessment is not ready_to_apply
            OwnershipError       — if target_id belongs to another user
            ClaimGroundingError  — if all required capability claims fail grounding
        """
        user_id = str(user.id)

        # --- Step 1: Ownership check ---
        await _verify_ownership(db, user_id, target_id)

        # --- Step 2: Reconstruct opportunity ---
        opp_id = opportunity_id or str(uuid.uuid4())
        opportunity = FreelanceOpportunity(
            opportunity_id=opp_id,
            platform=platform,
            external_id=opp_id,
            title=opportunity_title,
            description=opportunity_description,
            required_skills=required_skills,
            application_mode=ApplicationMode.UNKNOWN,
            user_id=user_id,
        )

        # --- Step 3: Server-side authoritative assessment ---
        requirements, assessment, decision = await self._assessment_service.assess(
            opportunity=opportunity,
            db=db,
        )

        # --- Step 4: Readiness gate ---
        if decision.decision not in (BrainDecisionType.READY_TO_APPLY,) and \
                assessment.readiness not in (
                    ReadinessState.READY_TO_APPLY,
                    ReadinessState.HIGH_CONFIDENCE,
                ):
            raise ReadinessGateError(
                f"Opportunity is not ready_to_apply. "
                f"Current decision: {decision.decision.value}, "
                f"readiness: {assessment.readiness.value}.",
                decision=decision.decision.value,
                blocking_capability=decision.blocking_capability,
            )

        # --- Step 5: Fingerprint + idempotent draft reuse ---
        required_cap_ids = requirements.required_capabilities
        if not required_cap_ids:
            raise ClaimGroundingError(
                "No required capabilities could be extracted. "
                "Cannot build a grounded application package."
            )

        fingerprint = _opportunity_fingerprint(user_id, opp_id, required_cap_ids)
        existing = await self._repo.get_by_fingerprint(db, user_id, fingerprint)
        if existing is not None:
            logger.info(
                "application_package_reused",
                extra={
                    "application_id": existing.application_id,
                    "user_id": user_id,
                    "fingerprint": fingerprint,
                },
            )
            return _record_to_package(existing)

        # --- Step 6: Load authoritative profile rows ---
        profile_rows = await self._load_profile_rows(db, required_cap_ids)

        # --- Step 7: Ground claims deterministically ---
        claims: List[CapabilityClaim] = []
        evidence_summaries: List[EvidenceSummary] = []
        matched_caps: List[str] = []
        grounding_errors: List[str] = []

        for cap_id in required_cap_ids:
            row = profile_rows.get(cap_id)
            if row is None:
                grounding_errors.append(
                    f"No profile row found for capability '{cap_id}'."
                )
                continue
            try:
                claim = _ground_claim(cap_id, row)
                claims.append(claim)
                evidence_summaries.append(_build_evidence_summary(cap_id, row))
                matched_caps.append(cap_id)
            except ClaimGroundingError as e:
                grounding_errors.append(str(e))

        if grounding_errors and not claims:
            raise ClaimGroundingError(
                "All required capability claims failed grounding: "
                + "; ".join(grounding_errors)
            )

        # --- Step 8: Known limitations ---
        known_limitations: List[str] = []
        if grounding_errors:
            known_limitations.extend(grounding_errors)
        for match in assessment.capability_matches:
            if not match.required and match.gap:
                known_limitations.append(
                    f"Optional capability '{match.capability}' is below threshold "
                    f"(confidence {match.confidence:.2f})."
                )
        if not target_id:
            known_limitations.append(
                "No specific product target was provided; proposal is based on "
                "general opportunity description."
            )
        known_limitations.append(
            "Capability evidence is based on controlled text-based verification; "
            "visual or domain-specific validation may require additional review."
        )

        # --- Step 9: AI proposal, validated ---
        proposal_text, proposal_warnings = await _generate_proposal(
            opportunity_title=opportunity_title,
            opportunity_description=opportunity_description,
            claims=claims,
        )
        if proposal_warnings:
            known_limitations.extend(proposal_warnings)

        # --- Step 10: Persist before returning ---
        application_id = f"pkg_{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()

        record = ControlledApplicationPackageRecord(
            application_id=application_id,
            user_id=user.id,
            opportunity_id=opp_id,
            opportunity_title=opportunity_title,
            platform=platform,
            readiness_decision=decision.decision.value,
            readiness_score=assessment.overall_score,
            required_capabilities=required_cap_ids,
            matched_capabilities=matched_caps,
            capability_claims_snapshot=[c.to_dict() for c in claims],
            evidence_summary_snapshot=[e.to_dict() for e in evidence_summaries],
            proposal_text=proposal_text,
            known_limitations=known_limitations,
            opportunity_fingerprint=fingerprint,
            state=PackageState.READY_FOR_HUMAN_APPROVAL.value,
            stale_on_approval_attempt=False,
            created_at=now,
            updated_at=now,
        )
        await self._repo.save(db, record)

        logger.info(
            "application_package_built",
            extra={
                "application_id": application_id,
                "user_id": user_id,
                "readiness_score": round(assessment.overall_score, 3),
                "claims_count": len(claims),
                "state": PackageState.READY_FOR_HUMAN_APPROVAL.value,
            },
        )

        return ControlledApplicationPackage(
            application_id=application_id,
            opportunity_id=opp_id,
            opportunity_title=opportunity_title,
            platform=platform,
            required_capabilities=required_cap_ids,
            readiness_decision=decision.decision.value,
            readiness_score=assessment.overall_score,
            matched_capabilities=matched_caps,
            proposal_text=proposal_text,
            capability_claims=claims,
            evidence_summary=evidence_summaries,
            known_limitations=known_limitations,
            state=PackageState.READY_FOR_HUMAN_APPROVAL,
            created_at=now,
        )

    # ------------------------------------------------------------------
    # Review (APPROVE / REJECT)
    # ------------------------------------------------------------------

    async def review(
        self,
        *,
        user: User,
        application_id: str,
        decision: str,
        note: Optional[str],
        db: AsyncSession,
        # Opportunity context needed for stale re-check on APPROVE
        opportunity_title: Optional[str] = None,
        opportunity_description: Optional[str] = None,
        platform: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
    ) -> ControlledApplicationPackage:
        """
        Apply a human review decision (approve / reject).

        State machine:
          READY_FOR_HUMAN_APPROVAL + approve → APPROVED (if fresh re-check passes)
          READY_FOR_HUMAN_APPROVAL + reject  → REJECTED (no re-check)
          Any other current state            → ReviewStateError

        APPROVE safety:
          A fresh authoritative assessment is run before approving.
          If the opportunity is no longer ready_to_apply:
            - stale_on_approval_attempt=True is recorded
            - state remains READY_FOR_HUMAN_APPROVAL
            - StaleReadinessError is raised

        REJECT safety:
          No readiness re-check. State moves to REJECTED immediately.

        Neither path triggers external submission.
        Neither path mutates KnowledgeProgress.

        Raises:
            PackageNotFoundError  — package not found or belongs to another user
            ReviewStateError      — package is not in READY_FOR_HUMAN_APPROVAL
            StaleReadinessError   — APPROVE attempted but profile no longer ready
        """
        user_id = str(user.id)
        decision_lower = decision.lower()
        if decision_lower not in (REVIEW_APPROVE, REVIEW_REJECT):
            raise ReviewStateError(
                f"Invalid review decision '{decision}'. "
                f"Must be '{REVIEW_APPROVE}' or '{REVIEW_REJECT}'."
            )

        # --- Load record (ownership-scoped) ---
        record = await self._repo.get_by_application_id(db, application_id, user_id)
        if record is None:
            raise PackageNotFoundError(
                f"Application package '{application_id}' not found."
            )

        # --- State check ---
        if record.state != PackageState.READY_FOR_HUMAN_APPROVAL.value:
            raise ReviewStateError(
                f"Package '{application_id}' is in state '{record.state}' "
                f"and cannot be reviewed again. "
                f"Only '{PackageState.READY_FOR_HUMAN_APPROVAL.value}' packages "
                "can be reviewed."
            )

        now = datetime.utcnow()

        if decision_lower == REVIEW_APPROVE:
            # --- Stale readiness re-check ---
            stale = await self._check_stale(
                db=db,
                user_id=user_id,
                opportunity_title=opportunity_title or record.opportunity_title,
                opportunity_description=opportunity_description or record.opportunity_title,
                platform=platform or record.platform,
                required_skills=required_skills or record.required_capabilities,
                opportunity_id=record.opportunity_id,
            )
            if stale:
                record.stale_on_approval_attempt = True
                record.updated_at = now
                await db.flush()
                raise StaleReadinessError(
                    f"Package '{application_id}' cannot be approved: the opportunity "
                    "is no longer ready_to_apply based on the current profile state.",
                    current_decision=stale,
                )

            record.state = PackageState.APPROVED.value

        else:  # reject — no re-check
            record.state = PackageState.REJECTED.value

        record.reviewed_at = now
        record.review_decision = decision_lower
        record.review_note = note
        record.reviewed_by_user_id = user.id
        record.updated_at = now
        await db.flush()

        logger.info(
            "application_package_reviewed",
            extra={
                "application_id": application_id,
                "user_id": user_id,
                "decision": decision_lower,
                "new_state": record.state,
            },
        )

        return _record_to_package(record)

    async def _check_stale(
        self,
        db: AsyncSession,
        user_id: str,
        opportunity_title: str,
        opportunity_description: str,
        platform: str,
        required_skills: List[str],
        opportunity_id: str,
    ) -> Optional[str]:
        """
        Re-run authoritative assessment.
        Returns None if still ready_to_apply; returns the blocking decision string
        if no longer ready.
        """
        try:
            opp = FreelanceOpportunity(
                opportunity_id=opportunity_id,
                platform=platform,
                external_id=opportunity_id,
                title=opportunity_title,
                description=opportunity_description,
                required_skills=list(required_skills),
                application_mode=ApplicationMode.UNKNOWN,
                user_id=user_id,
            )
            _, assessment, decision = await self._assessment_service.assess(
                opportunity=opp, db=db
            )
            is_ready = (
                decision.decision == BrainDecisionType.READY_TO_APPLY
                or assessment.readiness in (
                    ReadinessState.READY_TO_APPLY,
                    ReadinessState.HIGH_CONFIDENCE,
                )
            )
            return None if is_ready else decision.decision.value
        except Exception as exc:
            logger.warning(
                "stale_check_failed",
                extra={"error": str(exc)},
            )
            # If re-check fails, be conservative — treat as stale to prevent
            # approving a potentially invalid package.
            return "assessment_error"

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(
        self,
        *,
        user: User,
        application_id: str,
        db: AsyncSession,
    ) -> ControlledApplicationPackage:
        user_id = str(user.id)
        record = await self._repo.get_by_application_id(db, application_id, user_id)
        if record is None:
            raise PackageNotFoundError(
                f"Application package '{application_id}' not found."
            )
        return _record_to_package(record)

    async def list_for_user(
        self,
        *,
        user: User,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ControlledApplicationPackage]:
        records = await self._repo.list_for_user(
            db, str(user.id), limit=limit, offset=offset
        )
        return [_record_to_package(r) for r in records]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _load_profile_rows(
        self,
        db: AsyncSession,
        capability_ids: List[str],
    ) -> Dict[str, KnowledgeProgress]:
        try:
            result = await db.execute(
                select(KnowledgeProgress).where(
                    KnowledgeProgress.profile_id == "enigma_profile",
                    KnowledgeProgress.domain.in_(capability_ids),
                )
            )
            rows = result.scalars().all()
            return {row.domain: row for row in rows}
        except Exception as exc:
            logger.warning("profile_rows_load_failed", extra={"error": str(exc)})
            return {}
