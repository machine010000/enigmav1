from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional

from app.intelligence.context_engine import ContextEngine
from app.intelligence.gap_engine import GapEngine
from app.intelligence.opportunity_engine import OpportunityEngine
from app.intelligence.registry import IntelligenceRegistry
from app.intelligence.reasoning_engine import ReasoningEngine
from app.intelligence.scenario_engine import ScenarioEngine
from app.intelligence.confidence_engine import ConfidenceEngine
from app.intelligence.reasoning_session import ReasoningSession

try:
    from app.profession.service import profession_service
except ImportError:
    profession_service = None

try:
    from app.knowledge_governance import GovernedKnowledge
    GOVERNANCE_AVAILABLE = True
except ImportError:
    GOVERNANCE_AVAILABLE = False


class IntelligenceEngine:
    def __init__(
        self,
        reasoning_engine: Optional[ReasoningEngine] = None,
        scenario_engine: Optional[ScenarioEngine] = None,
        gap_engine: Optional[GapEngine] = None,
        opportunity_engine: Optional[OpportunityEngine] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
    ) -> None:
        self.context_engine = ContextEngine()
        self.reasoning_engine = reasoning_engine
        self.scenario_engine = scenario_engine or ScenarioEngine()
        self.gap_engine = gap_engine or GapEngine()
        self.opportunity_engine = opportunity_engine or OpportunityEngine()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.registry = IntelligenceRegistry()
        self.registry.register("scenario", self.scenario_engine)
        self.registry.register("gap", self.gap_engine)
        self.registry.register("opportunity", self.opportunity_engine)
        self.registry.register("confidence", self.confidence_engine)

    def build_reasoning_session(
        self,
        goal: Optional[str] = None,
        user: Optional[Dict[str, Any]] = None,
        business: Optional[Dict[str, Any]] = None,
        product: Optional[Dict[str, Any]] = None,
        academy: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        knowledge: Optional[Dict[str, Any]] = None,
        research: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        governed_knowledge: Optional[Any] = None,
    ) -> ReasoningSession:
        if goal is None:
            raise ValueError("ReasoningSession requires a goal.")

        session = self.context_engine.build_context(
            goal=goal,
            user=user,
            business=business,
            product=product,
            academy=academy,
            memory=memory,
            knowledge=knowledge,
            research=research,
            constraints=constraints,
            preferences=preferences,
        )

        scenario = self.scenario_engine.detect(session)
        session = replace(session, scenario=scenario)
        gaps = self.gap_engine.find_gaps(session)
        opportunities = self.opportunity_engine.generate(session)
        estimate = self.confidence_engine.estimate(session)

        # Enrich with profession knowledge if profession service is available
        profession_data = {}
        if profession_service is not None:
            session_dict = session.to_dict()
            enriched_dict = profession_service.enrich_session_with_profession(goal, session_dict)
            profession_data = enriched_dict.get("profession", {})

        # Preserve governed knowledge provenance if available
        governed_provenance = {}
        if GOVERNANCE_AVAILABLE and governed_knowledge is not None:
            governed_provenance = governed_knowledge  # Pass through directly

        return replace(
            session,
            gaps=list(gaps),
            opportunities=list(opportunities),
            confidence=estimate.score,
            profession=profession_data,
            governed_knowledge=governed_provenance,
        )

    def reason(self, context: ReasoningSession) -> Any:
        if self.reasoning_engine is None:
            raise ValueError("Reasoning engine not configured")
        return self.reasoning_engine.reason(context)

    def evaluate(self, context: ReasoningSession) -> Any:
        if self.reasoning_engine is None:
            raise ValueError("Reasoning engine not configured")
        return self.reasoning_engine.evaluate(context)

    def summarize(self, context: ReasoningSession) -> str:
        if self.reasoning_engine is None:
            raise ValueError("Reasoning engine not configured")
        return self.reasoning_engine.summarize(context)

    def explain(self, context: ReasoningSession) -> str:
        if self.reasoning_engine is None:
            raise ValueError("Reasoning engine not configured")
        return self.reasoning_engine.explain(context)

    def execute_registry(self, name: str, context: Any, **kwargs: Any) -> Any:
        return self.registry.execute(name, context, **kwargs)
