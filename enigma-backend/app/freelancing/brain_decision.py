"""
Brain Decision Boundary — TASK-017

The Brain proposes a readiness decision.
Policy/evidence verifies and may override it.

Design rules (Phase 7 + Phase 15):
  - Brain cannot self-certify READY_TO_APPLY.
  - If Brain proposes READY_TO_APPLY but evidence is insufficient,
    policy overrides to LEARN_FIRST or NOT_READY.
  - The blocking capability is identified as the weakest required capability
    below its threshold.
  - No chain-of-thought is exposed in the public contract.
  - No raw LLM reasoning overwrites canonical confidence values.
  - execution_available flag tells callers whether a worker exists for the
    blocking capability — enabling structured capability gap output.
"""
from __future__ import annotations

from typing import List, Optional

from app.freelancing.contracts import (
    BrainDecisionType,
    BrainReadinessDecision,
    CapabilityMatch,
    OpportunityAssessment,
    ReadinessState,
)
from app.engine.capability_catalog import capability_catalog, CapabilityCatalog
from app.models.enigma_profile import CapabilityStatus


class BrainReadinessEvaluator:
    """
    Translates an OpportunityAssessment into a BrainReadinessDecision.

    The Brain's initial proposal is derived from the assessment's ReadinessState.
    The policy check then validates whether the proposal is supported by evidence.
    If not, the decision is overridden.

    This is the TASK-017 implementation of Phase 15:
    "Brain must not self-certify — policy/evidence can block Brain."
    """

    def __init__(self, catalog: Optional[CapabilityCatalog] = None) -> None:
        self._catalog = catalog or capability_catalog

    def evaluate(self, assessment: OpportunityAssessment) -> BrainReadinessDecision:
        """
        Produce a policy-verified BrainReadinessDecision from an assessment.

        Steps:
        1. Brain proposes based on assessment ReadinessState.
        2. Policy checks evidence against catalog thresholds.
        3. If proposal is READY_TO_APPLY but evidence insufficient → override.
        4. Return decision with override flag and blocking capability.
        """
        # Step 1: Brain's initial proposal from assessment
        brain_proposed = self._brain_propose(assessment)

        # Step 2: Policy verification
        policy_decision, override, blocking, reason = self._policy_verify(
            assessment, brain_proposed
        )

        # Step 3: Determine execution availability for the blocking capability
        exec_available = False
        if blocking:
            entry = self._catalog.get(blocking)
            exec_available = entry.execution_available if entry else False

        return BrainReadinessDecision(
            decision=policy_decision,
            brain_proposed=brain_proposed,
            policy_overridden=override,
            blocking_capability=blocking,
            execution_available=exec_available,
            overall_score=assessment.overall_score,
            readiness=assessment.readiness,
            reasoning=reason,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _brain_propose(self, assessment: OpportunityAssessment) -> BrainDecisionType:
        """
        Map ReadinessState to the Brain's initial proposal.

        The Brain optimistically proposes based on the assessment score.
        Policy may downgrade this.
        """
        if assessment.readiness in (
            ReadinessState.READY_TO_APPLY,
            ReadinessState.HIGH_CONFIDENCE,
        ):
            return BrainDecisionType.READY_TO_APPLY

        if assessment.readiness == ReadinessState.LEARN_FIRST:
            return BrainDecisionType.LEARN_CAPABILITY

        # NOT_READY
        if assessment.missing_capabilities:
            return BrainDecisionType.SKIP_OPPORTUNITY
        return BrainDecisionType.RESEARCH_MORE

    def _policy_verify(
        self,
        assessment: OpportunityAssessment,
        proposed: BrainDecisionType,
    ) -> tuple:
        """
        Policy verification layer.

        Returns (final_decision, overridden, blocking_capability, reason).

        TASK-017 Phase 15: even if Brain proposes READY_TO_APPLY, the policy
        must check that all required capabilities have evidence >= threshold.
        """
        # Find the weakest required capability
        required_matches = [m for m in assessment.capability_matches if m.required]
        blocking = self._find_blocking_capability(required_matches)

        # CASE 1: Missing capabilities (not in catalog) → always NOT_READY
        if assessment.missing_capabilities:
            if proposed == BrainDecisionType.READY_TO_APPLY:
                return (
                    BrainDecisionType.SKIP_OPPORTUNITY,
                    True,
                    assessment.missing_capabilities[0],
                    (
                        f"Policy override: Brain proposed READY_TO_APPLY but "
                        f"'{assessment.missing_capabilities[0]}' is not in the capability catalog."
                    ),
                )
            return (
                BrainDecisionType.SKIP_OPPORTUNITY,
                False,
                assessment.missing_capabilities[0],
                f"Capability '{assessment.missing_capabilities[0]}' is not in catalog.",
            )

        # CASE 2: Weak capabilities exist → at least LEARN_FIRST
        if assessment.weak_capabilities:
            weakest = blocking or assessment.weak_capabilities[0]
            match = self._get_match(assessment, weakest)
            conf = match.confidence if match else 0.0
            thresh = match.minimum_required_confidence if match else 0.65

            if proposed == BrainDecisionType.READY_TO_APPLY:
                return (
                    BrainDecisionType.LEARN_CAPABILITY,
                    True,  # Policy overrode the Brain
                    weakest,
                    (
                        f"Policy override: Brain proposed READY_TO_APPLY but "
                        f"'{weakest}' has confidence {conf:.2f} (threshold {thresh:.2f}). "
                        f"Evidence is insufficient."
                    ),
                )

            # Brain already proposed LEARN/PRACTICE — confirm
            entry = self._catalog.get(weakest)
            exec_avail = entry.execution_available if entry else False
            decision = (
                BrainDecisionType.PRACTICE_CAPABILITY
                if conf > 0
                else BrainDecisionType.LEARN_CAPABILITY
            )
            return (
                decision,
                False,
                weakest,
                (
                    f"Capability '{weakest}' needs {'practice' if conf > 0 else 'learning'}: "
                    f"confidence {conf:.2f} below threshold {thresh:.2f}."
                    + (
                        " No worker available — capability gap identified."
                        if not exec_avail
                        else ""
                    )
                ),
            )

        # CASE 3: All required capabilities pass — Brain's proposal stands
        if proposed == BrainDecisionType.READY_TO_APPLY:
            return (
                BrainDecisionType.READY_TO_APPLY,
                False,
                None,
                (
                    f"All required capabilities meet their confidence thresholds. "
                    f"Overall score: {assessment.overall_score:.0%}."
                ),
            )

        # CASE 4: Score too low despite no explicit gaps
        if assessment.overall_score < 0.5:
            return (
                BrainDecisionType.RESEARCH_MORE,
                proposed != BrainDecisionType.RESEARCH_MORE,
                None,
                f"Overall score {assessment.overall_score:.0%} is too low to proceed.",
            )

        return (
            proposed,
            False,
            None,
            f"Decision follows Brain proposal. Score: {assessment.overall_score:.0%}.",
        )

    def _find_blocking_capability(
        self, required_matches: List[CapabilityMatch]
    ) -> Optional[str]:
        """Return the capability furthest below its threshold (worst gap)."""
        gaps = [(m.confidence - m.minimum_required_confidence, m.capability)
                for m in required_matches if m.gap]
        if not gaps:
            return None
        gaps.sort(key=lambda x: x[0])  # most negative first
        return gaps[0][1]

    def _get_match(
        self,
        assessment: OpportunityAssessment,
        cap_id: str,
    ) -> Optional[CapabilityMatch]:
        for m in assessment.capability_matches:
            if m.capability == cap_id:
                return m
        return None
