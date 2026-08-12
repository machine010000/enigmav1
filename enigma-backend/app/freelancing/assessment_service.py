"""
Opportunity Assessment Service — TASK-017

Orchestrates the full assessment pipeline:

  FreelanceOpportunity
      ↓
  RequirementExtractor      (deterministic catalog mapping)
      ↓
  OpportunityRequirements
      ↓
  CapabilityMatcher         (loads live profile from DB, scoped to profile_id)
      ↓
  OpportunityAssessment
      ↓
  BrainReadinessEvaluator   (policy-verified Brain decision)
      ↓
  BrainReadinessDecision

TASK-017 Phase 17 (latency):
  - Requirement extraction is synchronous (deterministic keyword mapping).
  - No LLM calls in this path; latency is bounded by one DB read.
  - If LLM-enhanced extraction is added in a future task it must be:
      a) wrapped with a timeout
      b) fall back to deterministic extraction on timeout
      c) never create false readiness on timeout

TASK-017 Phase 12 (isolation):
  - Profile data is loaded from the single global "enigma_profile".
  - Evidence data in KnowledgeProgress is contributed by all users'
    executions (ENIGMA learns from all usage).
  - The FreelanceOpportunity.user_id ensures the opportunity is tied to
    the requesting user — but the profile itself is global.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.freelancing.contracts import (
    BrainReadinessDecision,
    FreelanceOpportunity,
    OpportunityAssessment,
    OpportunityRequirements,
)
from app.freelancing.requirement_extractor import RequirementExtractor
from app.freelancing.capability_matcher import CapabilityMatcher
from app.freelancing.brain_decision import BrainReadinessEvaluator
from app.engine.capability_catalog import CapabilityCatalog, capability_catalog
from app.models.enigma_profile import KnowledgeProgress
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OpportunityAssessmentService:
    """
    End-to-end opportunity assessment orchestrator.

    Performance target (Phase 21):
      - Without DB: < 5 ms
      - With DB (1 capability row): < 30 ms
      - With DB (10 capability rows): < 80 ms
      No N+1 queries: all KnowledgeProgress rows are loaded in a single query.
    """

    def __init__(
        self,
        catalog: Optional[CapabilityCatalog] = None,
    ) -> None:
        self._catalog = catalog or capability_catalog
        self._extractor = RequirementExtractor(catalog=self._catalog)
        self._matcher = CapabilityMatcher(catalog=self._catalog)
        self._evaluator = BrainReadinessEvaluator(catalog=self._catalog)

    async def assess(
        self,
        opportunity: FreelanceOpportunity,
        db: Optional[AsyncSession] = None,
    ) -> Tuple[OpportunityRequirements, OpportunityAssessment, BrainReadinessDecision]:
        """
        Full assessment pipeline.

        Returns (requirements, assessment, decision).
        Callers may use any of the three outputs.
        """
        t0 = time.monotonic()

        # Step 1: Extract requirements (synchronous, deterministic)
        requirements = self._extractor.extract(opportunity)

        logger.info(
            "assessment_requirements_extracted",
            extra={
                "opportunity_id": opportunity.opportunity_id,
                "required_capabilities": requirements.required_capabilities,
                "unmapped_skills": requirements.unmapped_skills,
            },
        )

        # Step 2: Load profile snapshot from DB (single query, no N+1)
        profile_snapshot = await self._load_profile_snapshot(
            db=db,
            capability_ids=requirements.required_capabilities + requirements.optional_capabilities,
        )

        # Step 3: Match capabilities against profile
        assessment = self._matcher.match(requirements, profile_snapshot)

        # Step 4: Brain decision with policy verification
        decision = self._evaluator.evaluate(assessment)

        duration_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "assessment_complete",
            extra={
                "opportunity_id": opportunity.opportunity_id,
                "readiness": assessment.readiness.value,
                "decision": decision.decision.value,
                "overall_score": round(assessment.overall_score, 3),
                "policy_overridden": decision.policy_overridden,
                "duration_ms": round(duration_ms, 1),
            },
        )

        return requirements, assessment, decision

    async def _load_profile_snapshot(
        self,
        db: Optional[AsyncSession],
        capability_ids: list,
    ) -> Dict[str, Any]:
        """
        Load KnowledgeProgress rows for the requested capabilities.

        Single SELECT query — no N+1.
        Returns {capability_id: {confidence, evidence_count, ...}}.
        Missing rows default to empty dict (capability is UNKNOWN).
        """
        if db is None or not capability_ids:
            return {}

        try:
            result = await db.execute(
                select(KnowledgeProgress).where(
                    KnowledgeProgress.profile_id == "enigma_profile",
                    KnowledgeProgress.domain.in_(capability_ids),
                )
            )
            rows = result.scalars().all()

            snapshot: Dict[str, Any] = {}
            for row in rows:
                snapshot[row.domain] = {
                    "confidence": row.confidence or 0.0,
                    "evidence_count": row.evidence_count or 0,
                    "successful_execution_count": row.successful_execution_count or 0,
                    "failed_execution_count": row.failed_execution_count or 0,
                    "capability_status": row.capability_status or "unknown",
                    "readiness": row.readiness or 0.0,
                    "last_success_at": (
                        row.last_success_at.isoformat() if row.last_success_at else None
                    ),
                }
            return snapshot
        except Exception as e:
            logger.warning(
                "profile_snapshot_load_failed",
                extra={"error_type": type(e).__name__},
            )
            return {}
