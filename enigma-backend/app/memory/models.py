from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class Episode:
    id: str
    execution_id: str
    decision_id: Optional[str]
    product_id: Optional[str]
    worker: str
    goal: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    execution_time: float = 0.0
    llm_calls: int = 0
    success: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "decision_id": self.decision_id,
            "product_id": self.product_id,
            "worker": self.worker,
            "goal": self.goal,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "llm_calls": self.llm_calls,
            "success": self.success,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class Strategy:
    id: str
    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(slots=True)
class Pattern:
    id: str
    category: str
    description: str
    trigger: str
    outcome: str
    confidence: float = 0.0
    occurrences: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "trigger": self.trigger,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "created_at": self.created_at.isoformat(),
        }
