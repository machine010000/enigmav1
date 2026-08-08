from __future__ import annotations

from dataclasses import replace

from app.intelligence.models import ContextSummary
from app.intelligence.reasoning_session import ReasoningSession


class ContextEngine:
    def build_context(
        self,
        goal: str,
        user: dict | None = None,
        business: dict | None = None,
        product: dict | None = None,
        academy: dict | None = None,
        memory: dict | None = None,
        knowledge: dict | None = None,
        research: dict | None = None,
        constraints: list[str] | None = None,
        preferences: dict | None = None,
    ) -> ReasoningSession:
        context = ReasoningSession(
            goal=goal,
            user=user or {},
            business=business or {},
            product=product or {},
            academy=academy or {},
            memory=memory or {},
            knowledge=knowledge or {},
            research=research or {},
            constraints=constraints or [],
            preferences=preferences or {},
        )
        return self.enrich(context)

    def summarize(self, context: ReasoningSession) -> ContextSummary:
        summary = " | ".join(
            part
            for part in [
                f"Goal: {context.goal}" if context.goal else None,
                f"Scenario: {context.scenario}" if context.scenario else None,
                f"Topics: {', '.join(context.topics)}" if context.topics else None,
            ]
            if part
        )
        return ContextSummary(summary=summary or "No reasoning context available.")

    def enrich(self, context: ReasoningSession) -> ReasoningSession:
        return replace(
            context,
            topics=list(context.topics or []),
            knowledge=context.knowledge or {},
            gaps=list(context.gaps or []),
            opportunities=list(context.opportunities or []),
            constraints=list(context.constraints or []),
            preferences=context.preferences or {},
        )
