"""
Capability Matcher — TASK-017

Compares OpportunityRequirements against the live ENIGMA capability profile
(KnowledgeProgress from DB) and produces an OpportunityAssessment.

Design rules:
  - Overall score is computed from per-capability matches — never a single
    LLM-generated number.
  - ReadinessState is derived from the scored result — not from LLM assertion.
  - Policy check blocks READY_TO_APPLY if evidence is insufficient,
    regardless of what the Brain proposes.
  - User A's profile data is never used to assess User B's opportunities.
    (Enforced at the service layer — matcher receives data already scoped
    to the correct profile_id.)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.freelancing.contracts import (
    CapabilityMatch,
    OpportunityAssessment,
    OpportunityRequirements,
    ReadinessState,
)
from app.engine.capability_catalog import CapabilityCatalog, capability_catalog
from app.models.enigma_profile import CapabilityStatus


class CapabilityMatcher:
    """
    Matches opportunity requirements against a capability profile.

    profile_snapshot: Dict[capability_id → KnowledgeProgress-like dict]
    The caller is responsible for loading and scoping the profile snapshot.
    """

    def __init__(self, catalog: Optional[CapabilityCatalog] = None) -> None:
        self._catalog = catalog or capability_catalog

    def match(
        self,
        requirements: OpportunityRequirements,
        profile_snapshot: Dict[str, Any],
    ) -> OpportunityAssessment:
        """
        Produce a full OpportunityAssessment.

        Args:
            requirements:     Extracted structured requirements.
            profile_snapshot: {capability_id: {confidence, evidence_count,
                               successful_execution_count, failed_execution_count,
                               capability_status}} scoped to the correct profile.
        """
        matches: List[CapabilityMatch] = []
        missing: List[str] = []
        weak: List[str] = []

        # --- Required capabilities ---
        for cap_id in requirements.required_capabilities:
            match = self._evaluate_capability(
                cap_id=cap_id,
                required=True,
                profile_snapshot=profile_snapshot,
            )
            matches.append(match)
            if not match.in_catalog:
                missing.append(cap_id)
            elif match.gap:
                weak.append(cap_id)

        # --- Optional capabilities (informational only, don't block) ---
        for cap_id in requirements.optional_capabilities:
            match = self._evaluate_capability(
                cap_id=cap_id,
                required=False,
                profile_snapshot=profile_snapshot,
            )
            matches.append(match)

        # --- Compute overall score from required matches only ---
        overall_score = self._compute_overall_score(
            [m for m in matches if m.required]
        )

        # --- Derive readiness from score and gaps ---
        readiness = self._derive_readiness(overall_score, missing, weak)

        # --- Build reasoning summary ---
        reasoning = self._build_reasoning(
            overall_score, readiness, missing, weak, requirements
        )

        return OpportunityAssessment(
            opportunity_id=requirements.opportunity_id,
            overall_score=overall_score,
            readiness=readiness,
            capability_matches=matches,
            missing_capabilities=missing,
            weak_capabilities=weak,
            unmapped_skills=requirements.unmapped_skills,
            risk_flags=requirements.risk_flags,
            reasoning_summary=reasoning,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_capability(
        self,
        cap_id: str,
        required: bool,
        profile_snapshot: Dict[str, Any],
    ) -> CapabilityMatch:
        """Evaluate a single capability against the profile."""
        entry = self._catalog.get(cap_id)
        if entry is None:
            # Unknown capability — not in catalog
            return CapabilityMatch(
                capability=cap_id,
                required=required,
                in_catalog=False,
                execution_available=False,
                profile_status=CapabilityStatus.UNKNOWN.value,
                confidence=0.0,
                evidence_count=0,
                minimum_required_confidence=0.65,
                gap=required,
                reason="Capability not in catalog — cannot be executed or assessed",
            )

        threshold = entry.freelance_readiness_threshold

        # Read from profile snapshot (may be empty if never trained)
        profile_data = profile_snapshot.get(cap_id, {})
        confidence = float(profile_data.get("confidence", 0.0))
        evidence_count = int(profile_data.get("evidence_count", 0))
        success_count = int(profile_data.get("successful_execution_count", 0))
        fail_count = int(profile_data.get("failed_execution_count", 0))
        status_raw = profile_data.get(
            "capability_status", CapabilityStatus.UNKNOWN.value
        )

        # Is this capability meeting the threshold?
        meets_threshold = confidence >= threshold
        gap = required and not meets_threshold

        if not profile_data:
            reason = "No execution evidence yet — capability is UNKNOWN in profile"
        elif not meets_threshold:
            reason = (
                f"Confidence {confidence:.2f} is below required threshold {threshold:.2f} "
                f"({evidence_count} evidence observations)"
            )
        else:
            reason = (
                f"Confidence {confidence:.2f} meets threshold {threshold:.2f} "
                f"({success_count} successful executions)"
            )

        return CapabilityMatch(
            capability=cap_id,
            required=required,
            in_catalog=True,
            execution_available=entry.execution_available,
            profile_status=status_raw,
            confidence=confidence,
            evidence_count=evidence_count,
            successful_executions=success_count,
            failed_executions=fail_count,
            minimum_required_confidence=threshold,
            gap=gap,
            reason=reason,
        )

    def _compute_overall_score(
        self, required_matches: List[CapabilityMatch]
    ) -> float:
        """
        Compute overall score as a weighted average of required capability
        confidence values, normalised by their thresholds.

        A capability at exactly its threshold contributes 1.0 to the score;
        below threshold contributes < 1.0.
        """
        if not required_matches:
            return 0.0

        scores = []
        for m in required_matches:
            if m.minimum_required_confidence > 0:
                ratio = min(1.0, m.confidence / m.minimum_required_confidence)
            else:
                ratio = 1.0 if m.confidence > 0 else 0.0
            scores.append(ratio)

        return sum(scores) / len(scores)

    def _derive_readiness(
        self,
        overall_score: float,
        missing: List[str],
        weak: List[str],
    ) -> ReadinessState:
        """
        Derive ReadinessState deterministically from score and gap lists.

        Policy rules:
          - Any capability not in catalog → NOT_READY
          - Any required capability below threshold → LEARN_FIRST
          - All required capabilities meet threshold:
              score >= 0.85 → HIGH_CONFIDENCE
              else          → READY_TO_APPLY
        """
        if missing:
            return ReadinessState.NOT_READY
        if weak:
            return ReadinessState.LEARN_FIRST
        if overall_score >= 0.85:
            return ReadinessState.HIGH_CONFIDENCE
        return ReadinessState.READY_TO_APPLY

    def _build_reasoning(
        self,
        overall_score: float,
        readiness: ReadinessState,
        missing: List[str],
        weak: List[str],
        requirements: OpportunityRequirements,
    ) -> str:
        parts: List[str] = [
            f"Overall capability score: {overall_score:.0%}.",
            f"Readiness: {readiness.value}.",
        ]
        if missing:
            parts.append(
                f"Missing/unknown capabilities: {', '.join(missing[:3])}."
            )
        if weak:
            parts.append(
                f"Below-threshold capabilities requiring practice: {', '.join(weak[:3])}."
            )
        if requirements.unmapped_skills:
            parts.append(
                f"Unmapped skills (no catalog entry): {', '.join(requirements.unmapped_skills[:3])}."
            )
        if requirements.risk_flags:
            parts.append(f"Risk flags: {', '.join(requirements.risk_flags)}.")
        return " ".join(parts)
