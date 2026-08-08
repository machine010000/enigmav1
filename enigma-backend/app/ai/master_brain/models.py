from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
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


class Planner(ABC):
    def build_execution_plan(self, context: Any) -> Dict[str, Any]:
        raise NotImplementedError("Planner.build_execution_plan must be implemented by a subclass")

