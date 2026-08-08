from __future__ import annotations

from app.intelligence.models import ConfidenceEstimate
from app.intelligence.reasoning_session import ReasoningSession


class ConfidenceEngine:
    def estimate(self, context: ReasoningSession) -> ConfidenceEstimate:
        base = 0.4
        if context.scenario and context.scenario != "Unknown":
            base += 0.2
        if context.gaps:
            base -= 0.1
        if context.topics:
            base += 0.1

        score = min(max(base, 0.0), 1.0)
        return ConfidenceEstimate(score=score, rationale="Estimated from scenario alignment and available knowledge.")

    def is_confident(self, context: ReasoningSession, threshold: float = 0.5) -> bool:
        return self.estimate(context).score >= threshold
