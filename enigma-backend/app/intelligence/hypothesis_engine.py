from __future__ import annotations

from typing import List

from app.intelligence.models import Hypothesis, Opportunity
from app.intelligence.reasoning_session import ReasoningSession


class HypothesisEngine:
    def generate(self, context: ReasoningSession) -> List[Hypothesis]:
        return [
            Hypothesis(
                statement="A strong niche focus will improve campaign performance.",
                confidence=0.65,
                supporting_evidence="Academy knowledge shows niche differentiation works for many business models.",
                risk=0.35,
            )
        ]

    def score(self, hypothesis: Hypothesis, opportunity: Opportunity) -> float:
        return hypothesis.confidence * opportunity.impact

    def rank(self, hypotheses: List[Hypothesis], opportunity: Opportunity) -> List[Hypothesis]:
        return sorted(hypotheses, key=lambda h: self.score(h, opportunity), reverse=True)
