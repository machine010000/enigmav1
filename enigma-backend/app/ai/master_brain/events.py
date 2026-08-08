from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class BrainEventType(Enum):
    GOAL_RECEIVED = "goal_received"
    USER_UNDERSTOOD = "user_understood"
    SCENARIO_IDENTIFIED = "scenario_identified"
    MEMORY_RECALLED = "memory_recalled"
    ACADEMY_READ = "academy_read"
    KNOWLEDGE_READ = "knowledge_read"
    HYPOTHESIS_CREATED = "hypothesis_created"
    GAPS_FOUND = "gaps_found"
    PLAN_CREATED = "plan_created"
    WAITING_RESULTS = "waiting_results"
    DECISION_UPDATED = "decision_updated"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass
class BrainEvent:
    event_type: BrainEventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


class BrainEventBus:
    def __init__(self):
        self.history: List[BrainEvent] = []

    def publish(self, event: BrainEvent) -> None:
        self.history.append(event)

    def last_event(self) -> BrainEvent | None:
        return self.history[-1] if self.history else None

    def all_events(self) -> List[BrainEvent]:
        return list(self.history)

    def clear(self) -> None:
        self.history.clear()
