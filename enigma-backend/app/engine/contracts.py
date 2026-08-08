"""
ENIGMA Engine — Core Contracts

This module defines the fundamental building blocks of the Execution Engine:

- WorkerStatus      : life-cycle states a worker execution can be in
- EventType         : event categories emitted for the Live Console
- WorkerEvent       : a single live event payload (worker, type, message, data)
- WorkerResult      : the structured return value of every Worker
- ExecutionContext  : the shared context passed into every Worker
- Worker            : the abstract base class that defines the Worker Contract

The Evidence-First Architecture principle is baked into WorkerResult via the
``evidence`` list — every decision carries its supporting proof so the Brain
can trace, review, and re-evaluate it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional


class WorkerStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class EventType(Enum):
    WORKER_REGISTERED = "worker_registered"
    EXECUTION_STARTED = "execution_started"
    PROGRESS = "progress"
    VERIFICATION_STARTED = "verification_started"
    RESEARCH_STARTED = "research_started"
    AUDIENCE_STARTED = "audience_started"
    KEYWORD_STARTED = "keyword_started"
    FINISHED = "finished"
    ERROR = "error"

    # allow arbitrary string event types
    @classmethod
    def _missing_(cls, value: object) -> Optional["EventType"]:
        """Return None for unknown strings so callers can still pass custom types."""
        return None


@dataclass
class WorkerEvent:
    worker_name: str
    type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class EvidenceItem:
    worker: str
    field: str
    value: Any
    source: str = ""
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker": self.worker,
            "field": self.field,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WorkerResult:
    worker_name: str
    status: WorkerStatus
    result: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    execution_time: float = 0.0
    llm_calls: int = 0
    memory_usage_mb: Optional[float] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "worker_name": self.worker_name,
            "status": self.status.value if isinstance(self.status, WorkerStatus) else self.status,
            "result": self.result,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "execution_time": round(self.execution_time, 4),
            "llm_calls": self.llm_calls,
            "memory_usage_mb": round(self.memory_usage_mb, 4) if self.memory_usage_mb is not None else None,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }
        return d


@dataclass
class ExecutionContext:
    """
    Unified execution context passed to every Worker.

    Pipeline:  User -> User Brain -> Execution Engine -> Worker -> Result -> Dashboard -> Brain

    Fields:
        user      : authenticated user info
        product   : product being analysed (if any)
        memory    : mutable scratch-space the worker can read/write for cross-worker state
        knowledge : accumulated MasterKnowledge entries
        settings  : runtime settings / config
        history   : previous WorkerResult summaries for this session
        execution_id : unique identifier for this execution chain
        emit      : callable to emit a WorkerEvent for the Live Console
    """
    user: Dict[str, Any] = field(default_factory=dict)
    product: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    memory_engine: Optional[Any] = None
    knowledge: List[Dict[str, Any]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    execution_id: str = ""
    emit: Optional[Callable[[WorkerEvent], "Awaitable[None]"]] = None

    # ---- convenience helpers -------------------------------------------------

    def recall(self, key: str, default: Any = None) -> Any:
        """Read a value from memory."""
        return self.memory.get(key, default)

    def remember(self, key: str, value: Any) -> None:
        """Write a value to memory for downstream workers."""
        self.memory[key] = value

    def add_history(self, result: "WorkerResult") -> None:
        """Append a WorkerResult summary to the history list."""
        self.history.append({
            "worker_name": result.worker_name,
            "status": result.status.value if isinstance(result.status, WorkerStatus) else result.status,
            "confidence": result.confidence,
            "result": result.result,
            "execution_time": result.execution_time,
        })

    def get_knowledge(self, category: str) -> List[Dict[str, Any]]:
        """Filter knowledge entries by category."""
        return [k for k in self.knowledge if k.get("category") == category]

    def record_episode(self, worker_name: str, result: "WorkerResult", decision_id: Optional[str] = None, product_id: Optional[str] = None, goal: Optional[str] = None) -> Any:
        """Create an episode from a worker result using the shared memory engine."""
        memory_engine = self.memory_engine
        if memory_engine is None:
            return None

        episode = memory_engine.store_episode(
            type(
                "EpisodeStub",
                (),
                {
                    "id": f"episode-{len(memory_engine.episodes) + 1}",
                    "execution_id": self.execution_id or "",
                    "decision_id": decision_id,
                    "product_id": product_id,
                    "worker": worker_name,
                    "goal": goal or "",
                    "inputs": self.product or {},
                    "outputs": result.result,
                    "evidence": result.evidence,
                    "confidence": result.confidence,
                    "execution_time": result.execution_time,
                    "llm_calls": result.llm_calls,
                    "success": result.status.value == "success" if hasattr(result.status, "value") else bool(result.status == "success"),
                },
            )()
        )
        return episode


class Worker(ABC):
    """
    Worker Contract.

    Every Worker MUST define:
        - ``name``           : unique identifier string
        - ``input_schema``   : list of expected input keys (for discoverability)
        - ``output_schema``  : list of output keys the Worker produces
        - ``description``    : human-readable purpose

    The Worker receives an ExecutionContext and returns a WorkerResult.
    Workers ARE independently executable — they can be invoked directly
    without the Engine, and each carries its own evidence.
    """

    name: str = ""
    description: str = ""
    input_schema: List[str] = []
    output_schema: List[str] = []

    @abstractmethod
    async def run(self, context: ExecutionContext) -> WorkerResult:
        """Execute the worker logic and return a WorkerResult."""
        raise NotImplementedError

    # ---- optional hooks (override in subclasses) -----------------------------

    async def setup(self, context: ExecutionContext) -> None:
        """Called before run(). Default no-op."""

    async def teardown(self, context: ExecutionContext) -> None:
        """Called after run(). Default no-op."""
