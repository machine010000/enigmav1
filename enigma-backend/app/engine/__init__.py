"""
ENIGMA Engine package.

Exposes the core contracts and the singleton ExecutionEngine.
"""
from app.engine.contracts import (
    ExecutionContext,
    Worker,
    WorkerEvent,
    WorkerResult,
    WorkerStatus,
    EventType,
    EvidenceItem,
)
from app.engine.engine import engine
from app.engine.events import event_bus
from app.engine.capabilities import Capability, capability_registry
from app.engine.registry import register_all, get_registered

__all__ = [
    "ExecutionContext",
    "Worker",
    "WorkerEvent",
    "WorkerResult",
    "WorkerStatus",
    "EventType",
    "EvidenceItem",
    "engine",
    "event_bus",
    "Capability",
    "capability_registry",
    "register_all",
    "get_registered",
]
