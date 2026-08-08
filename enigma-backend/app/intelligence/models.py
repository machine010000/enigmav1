from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class ContextSummary:
    summary: str = ""

    def __str__(self) -> str:
        return self.summary


@dataclass
class ConfidenceEstimate:
    score: float = 0.0
    rationale: str = ""


@dataclass
class Hypothesis:
    id: str
    statement: str
    confidence: float = 0.0
    required_evidence: List[str] = field(default_factory=list)
    status: str = "draft"
    priority: int = 0
    supporting_evidence: str = ""
    risk: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Opportunity:
    title: str
    description: str
    impact: float = 0.0
    difficulty: float = 0.0
    confidence: float = 0.0
    reason: str = ""


@dataclass
class Gap:
    missing_information: str
    importance: float = 0.0
    source: str = ""
    blocking: bool = False
    confidence: float = 0.0

    def __hash__(self) -> int:
        return hash((
            self.missing_information,
            self.importance,
            self.source,
            self.blocking,
            self.confidence,
        ))
