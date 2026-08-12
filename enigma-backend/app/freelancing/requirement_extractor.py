"""
Requirement Extractor — TASK-017

Converts a FreelanceOpportunity into structured OpportunityRequirements.

Design rules:
  - LLM output (if used) is validated against the CapabilityCatalog.
  - Unknown/hallucinated capability names become unmapped_skills — they
    never silently become executable capabilities.
  - The extractor is synchronous-first.  LLM enhancement is optional and
    bounded (TASK-017 Phase 17 latency guidance).
  - If the LLM times out or errors, the extractor falls back to deterministic
    keyword mapping.  No false readiness is created on timeout.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.freelancing.contracts import FreelanceOpportunity, OpportunityRequirements
from app.engine.capability_catalog import capability_catalog, CapabilityCatalog


class RequirementExtractor:
    """
    Converts a FreelanceOpportunity into structured OpportunityRequirements.

    Phase 1 (TASK-017): deterministic keyword mapping only.
    Future phases may add bounded LLM enhancement (with catalog validation).
    """

    def __init__(self, catalog: Optional[CapabilityCatalog] = None) -> None:
        self._catalog = catalog or capability_catalog

    def extract(self, opportunity: FreelanceOpportunity) -> OpportunityRequirements:
        """
        Extract structured requirements from a normalised opportunity.

        All extracted capability names are validated against the catalog.
        Unknown names go into unmapped_skills — never into required_capabilities.
        """
        combined_text = (
            f"{opportunity.title} {opportunity.description} "
            f"{' '.join(opportunity.required_skills)} "
            f"{' '.join(opportunity.preferred_skills)}"
        ).lower()

        required_capabilities, optional_capabilities, unmapped_skills = (
            self._map_skills_to_capabilities(
                opportunity.required_skills,
                opportunity.preferred_skills,
                combined_text,
            )
        )

        complexity = self._estimate_complexity(combined_text, opportunity)
        deliverables = self._extract_deliverables(combined_text, required_capabilities)
        constraints = self._extract_constraints(opportunity)
        risk_flags = self._detect_risk_flags(combined_text, opportunity)
        confidence = self._compute_extraction_confidence(
            required_capabilities, unmapped_skills, opportunity
        )

        return OpportunityRequirements(
            opportunity_id=opportunity.opportunity_id,
            required_capabilities=required_capabilities,
            optional_capabilities=optional_capabilities,
            unmapped_skills=unmapped_skills,
            estimated_complexity=complexity,
            deliverables=deliverables,
            constraints=constraints,
            risk_flags=risk_flags,
            confidence_in_analysis=confidence,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_skills_to_capabilities(
        self,
        required_skills: List[str],
        preferred_skills: List[str],
        combined_text: str,
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Map raw skill tags and text to catalog capability IDs.

        Returns (required_capabilities, optional_capabilities, unmapped_skills).
        A skill that resolves to a catalog entry → capability_id.
        A skill that does NOT resolve → unmapped_skills.
        """
        required: List[str] = []
        optional: List[str] = []
        unmapped: List[str] = []
        seen: set = set()

        def _try_map(skill: str, dest: List[str]) -> None:
            entry = self._catalog.resolve(skill)
            if entry and entry.capability_id not in seen:
                seen.add(entry.capability_id)
                dest.append(entry.capability_id)
            elif not entry and skill.strip() and skill.lower() not in unmapped:
                unmapped.append(skill)

        for skill in required_skills:
            _try_map(skill, required)

        for skill in preferred_skills:
            _try_map(skill, optional)

        # Also scan the combined text for catalog keywords not caught by skill tags
        for entry in self._catalog.list_all():
            if entry.capability_id in seen:
                continue
            # Check aliases and name in text
            triggers = [entry.capability_id.replace("_", " ")] + list(entry.aliases)
            for trigger in triggers:
                if trigger.lower() in combined_text:
                    seen.add(entry.capability_id)
                    required.append(entry.capability_id)
                    break

        return required, optional, unmapped

    def _estimate_complexity(
        self,
        text: str,
        opportunity: FreelanceOpportunity,
    ) -> str:
        high_signals = [
            "comprehensive", "complex", "full", "enterprise", "large",
            "multiple", "strategy", "advanced", "complete overhaul",
        ]
        low_signals = [
            "simple", "quick", "basic", "minor", "small", "one page",
            "single page", "few",
        ]
        high_score = sum(1 for s in high_signals if s in text)
        low_score = sum(1 for s in low_signals if s in text)

        budget = opportunity.budget_max or opportunity.budget_min or 0
        if budget > 2000:
            high_score += 2
        elif budget < 200:
            low_score += 1

        if high_score > low_score and high_score >= 2:
            return "high"
        if low_score > high_score and low_score >= 2:
            return "low"
        return "medium"

    def _extract_deliverables(
        self,
        text: str,
        capabilities: List[str],
    ) -> List[str]:
        deliverables: List[str] = []
        patterns = [
            r"(?:deliverables?|you will|i need|i want|provide|create|write|produce)(?:\s+a)?\s+([^.,;!\n]{10,60})",
        ]
        for pattern in patterns:
            for m in re.findall(pattern, text, re.IGNORECASE):
                cleaned = m.strip()
                if cleaned and cleaned not in deliverables:
                    deliverables.append(cleaned)

        # Fall back to capability-derived defaults
        if not deliverables:
            for cap in capabilities[:3]:
                entry = self._catalog.get(cap)
                if entry:
                    deliverables.append(f"{entry.name} output")

        return deliverables[:6]  # cap at 6

    def _extract_constraints(self, opportunity: FreelanceOpportunity) -> List[str]:
        constraints: List[str] = []
        if opportunity.budget_max:
            constraints.append(f"Budget up to {opportunity.currency} {opportunity.budget_max:.0f}")
        elif opportunity.budget_min:
            constraints.append(f"Budget from {opportunity.currency} {opportunity.budget_min:.0f}")
        return constraints

    def _detect_risk_flags(
        self,
        text: str,
        opportunity: FreelanceOpportunity,
    ) -> List[str]:
        flags: List[str] = []
        risk_patterns = {
            "urgent_deadline": ["urgent", "asap", "immediately", "today", "rush"],
            "unpaid_trial": ["test task", "test project", "free sample", "trial work"],
            "scope_creep": ["ongoing", "unlimited revisions", "as needed", "etc"],
            "ambiguous_scope": ["something like", "similar to", "you know what i mean"],
        }
        for flag_name, keywords in risk_patterns.items():
            if any(kw in text for kw in keywords):
                flags.append(flag_name)

        if opportunity.budget_max and opportunity.budget_max < 20:
            flags.append("very_low_budget")

        return flags

    def _compute_extraction_confidence(
        self,
        required_capabilities: List[str],
        unmapped_skills: List[str],
        opportunity: FreelanceOpportunity,
    ) -> float:
        """
        Estimate how confident we are in the extraction result.
        Higher if most skills mapped, lower if many unmapped.
        """
        total_skills = (
            len(opportunity.required_skills) + len(opportunity.preferred_skills) + 1
        )
        mapped = len(required_capabilities)
        unmapped = len(unmapped_skills)

        base = 0.6
        mapping_ratio = mapped / total_skills
        confidence = base + mapping_ratio * 0.3 - (unmapped / total_skills) * 0.2
        return max(0.1, min(1.0, confidence))
