from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReasoningSession:
    goal: str = ""
    scenario: str = ""
    user: Dict[str, Any] = field(default_factory=dict)
    business: Dict[str, Any] = field(default_factory=dict)
    product: Dict[str, Any] = field(default_factory=dict)
    academy: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    knowledge: Dict[str, Any] = field(default_factory=dict)
    research: Dict[str, Any] = field(default_factory=dict)
    profession: Dict[str, Any] = field(default_factory=dict)
    governed_knowledge: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    decision: Optional[Dict[str, Any]] = None
    execution_plan: Optional[Dict[str, Any]] = None
    reflection: Optional[Dict[str, Any]] = None
    learning: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    knowledge_gaps: List[Dict[str, Any]] = field(default_factory=list)
    opportunities: List[Dict[str, Any]] = field(default_factory=list)
    gaps: List[Any] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def with_decision(self, decision: Dict[str, Any]) -> "ReasoningSession":
        return replace(self, decision=decision)

    def with_plan(self, plan: Dict[str, Any]) -> "ReasoningSession":
        return replace(self, execution_plan=plan)

    def with_assumptions(self, assumptions: List[str]) -> "ReasoningSession":
        return replace(self, assumptions=list(assumptions))

    def with_profession(self, profession: Dict[str, Any]) -> "ReasoningSession":
        return replace(self, profession=profession)

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "scenario": self.scenario,
            "user": self.user,
            "business": self.business,
            "product": self.product,
            "academy": self.academy,
            "memory": self.memory,
            "knowledge": self.knowledge,
            "research": self.research,
            "profession": self.profession,
            "governed_knowledge": self.governed_knowledge,
            "evidence": self.evidence,
            "hypotheses": self.hypotheses,
            "assumptions": self.assumptions,
            "conflicts": self.conflicts,
            "alternatives": self.alternatives,
            "decision": self.decision,
            "execution_plan": self.execution_plan,
            "reflection": self.reflection,
            "learning": self.learning,
            "confidence": self.confidence,
            "knowledge_gaps": self.knowledge_gaps,
            "opportunities": self.opportunities,
            "gaps": self.gaps,
            "topics": self.topics,
            "constraints": self.constraints,
            "preferences": self.preferences,
            "risks": self.risks,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
        }
