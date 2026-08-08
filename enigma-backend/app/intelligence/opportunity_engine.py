from __future__ import annotations

from typing import List

from app.intelligence.models import Opportunity
from app.intelligence.reasoning_session import ReasoningSession


class OpportunityEngine:
    def generate(self, context: ReasoningSession) -> List[Opportunity]:
        return [
            Opportunity(
                title="Validate target market",
                description="Evaluate the target market fit based on available academy and research knowledge.",
                impact=0.7,
                difficulty=0.4,
                confidence=0.6,
                reason="Derived from academy and market signals.",
            ),
        ]

    def prioritize(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        return sorted(opportunities, key=lambda opp: (opp.confidence, opp.impact), reverse=True)

    def estimate_roi(self, opportunity: Opportunity) -> float:
        return opportunity.impact * opportunity.confidence

    def estimate_risk(self, opportunity: Opportunity) -> float:
        return opportunity.difficulty * (1.0 - opportunity.confidence)
