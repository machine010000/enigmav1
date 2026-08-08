from __future__ import annotations

from typing import List

from app.intelligence.models import Gap
from app.intelligence.reasoning_session import ReasoningSession


class GapEngine:
    def find_gaps(self, context: ReasoningSession) -> List[Gap]:
        return [
            Gap(missing_information="Market definition", importance=0.8, source="academy", blocking=True, confidence=0.7),
            Gap(missing_information="Audience profile", importance=0.9, source="memory", blocking=False, confidence=0.6),
        ]

    def prioritize(self, gaps: List[Gap]) -> List[Gap]:
        return sorted(gaps, key=lambda gap: (not gap.blocking, -gap.importance, -gap.confidence))

    def blocking_gaps(self, gaps: List[Gap]) -> List[Gap]:
        return [gap for gap in gaps if gap.blocking]

    def optional_gaps(self, gaps: List[Gap]) -> List[Gap]:
        return [gap for gap in gaps if not gap.blocking]
