from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class Hypothesis:
    id: str
    statement: str
    confidence: float
    required_evidence: List[str] = field(default_factory=list)
    status: str = "draft"

    @classmethod
    def generate(
        cls,
        statement: str,
        confidence: float = 0.0,
        required_evidence: Optional[List[str]] = None,
    ) -> "Hypothesis":
        return cls(
            id=statement.lower().replace(" ", "_")[:64],
            statement=statement,
            confidence=confidence,
            required_evidence=list(required_evidence or []),
            status="draft",
        )

    def update(self, confidence: Optional[float] = None, required_evidence: Optional[List[str]] = None) -> None:
        if confidence is not None:
            self.confidence = confidence
        if required_evidence is not None:
            self.required_evidence = list(required_evidence)

    def reject(self) -> None:
        self.status = "rejected"

    def confirm(self) -> None:
        self.status = "confirmed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "confidence": self.confidence,
            "required_evidence": self.required_evidence,
            "status": self.status,
        }


class BrainAction(str, Enum):
    """Types of actions MasterBrain can request."""
    CHAT = "chat"
    ANSWER = "answer"
    EXECUTE_CAPABILITY = "execute_capability"
    FINISH = "finish"
    RECOMMEND_NEXT_ACTION = "recommend_next_action"


@dataclass
class BrainDecision:
    """
    Structured decision from MasterBrain.
    
    Distinguishes between conversational responses and capability execution requests.
    The Brain decides WHAT capability is required, not WHICH concrete worker implements it.
    """
    action: BrainAction
    intent: str
    capability: Optional[str] = None
    target: Optional[str] = None  # e.g., product_id
    reasoning_summary: str = ""
    execution_required: bool = False
    execution_input: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    next_action: Optional[str] = None  # For RECOMMEND_NEXT_ACTION
    next_action_reasoning: Optional[str] = None  # Explanation for next action
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value if isinstance(self.action, BrainAction) else self.action,
            "intent": self.intent,
            "capability": self.capability,
            "target": self.target,
            "reasoning_summary": self.reasoning_summary,
            "execution_required": self.execution_required,
            "execution_input": self.execution_input,
            "confidence": self.confidence,
            "next_action": self.next_action,
            "next_action_reasoning": self.next_action_reasoning,
        }


class Planner(ABC):
    def build_execution_plan(self, context: Any) -> Dict[str, Any]:
        raise NotImplementedError("Planner.build_execution_plan must be implemented by a subclass")

