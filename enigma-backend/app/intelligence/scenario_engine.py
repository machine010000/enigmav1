from __future__ import annotations

from typing import List

from app.intelligence.reasoning_session import ReasoningSession


class ScenarioEngine:
    SUPPORTED_SCENARIOS: List[str] = [
        "Affiliate Seller",
        "Own Brand",
        "Dropshipping",
        "Local Store",
        "Digital Product",
        "Service Provider",
        "Content Creator",
        "Investor",
    ]

    def detect(self, context: ReasoningSession) -> str:
        goal = getattr(context, "goal", "") or ""
        if not goal:
            scenario = "Unknown"
        else:
            lowered = goal.lower()
            if "affiliate" in lowered:
                scenario = "Affiliate Seller"
            elif "brand" in lowered:
                scenario = "Own Brand"
            elif "dropship" in lowered:
                scenario = "Dropshipping"
            elif "local" in lowered or "store" in lowered:
                scenario = "Local Store"
            elif "digital" in lowered or "course" in lowered:
                scenario = "Digital Product"
            elif "service" in lowered or "consult" in lowered:
                scenario = "Service Provider"
            elif "content" in lowered or "creator" in lowered:
                scenario = "Content Creator"
            elif "invest" in lowered or "fund" in lowered:
                scenario = "Investor"
            else:
                scenario = "Own Brand"

        try:
            setattr(context, "scenario", scenario)
        except (AttributeError, TypeError):
            pass
        return scenario

    def score(self, context: ReasoningSession) -> float:
        scenario = getattr(context, "scenario", None) or ""
        return 1.0 if scenario in self.SUPPORTED_SCENARIOS else 0.0

    def explain(self, context: ReasoningSession) -> str:
        scenario = getattr(context, "scenario", None) or "Unknown"
        goal = getattr(context, "goal", "") or ""
        return f"Detected scenario '{scenario}' from goal '{goal}'."
