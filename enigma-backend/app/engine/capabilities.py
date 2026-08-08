"""
Capability Registry — maps capability IDs to Worker implementations.

The Brain communicates with Workers through capabilities, not concrete
class names.  This registry enables the ExecutionEngine to select the
right Worker(s) for a given capability without the Brain ever knowing
which Worker class is behind it.

Architecture Rule 07: The Brain must never know concrete Worker
implementations.  It communicates only through Capabilities, Goals,
and Constraints.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Capability:
    id: str
    description: str
    category: str = "general"
    parameters: Dict[str, Any] = field(default_factory=dict)
    supported_inputs: List[str] = field(default_factory=list)
    supported_outputs: List[str] = field(default_factory=list)
    estimated_cost: Optional[float] = None
    average_time_seconds: Optional[float] = None
    confidence: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    required_models: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "supported_inputs": self.supported_inputs,
            "supported_outputs": self.supported_outputs,
            "estimated_cost": self.estimated_cost,
            "average_time_seconds": self.average_time_seconds,
            "confidence": self.confidence,
            "dependencies": self.dependencies,
            "required_models": self.required_models,
        }


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: Dict[str, Capability] = {}
        self._worker_capabilities: Dict[str, List[str]] = {}

    def register(self, capability: Capability, worker_name: str) -> None:
        self._capabilities[capability.id] = capability
        self._worker_capabilities.setdefault(worker_name, []).append(capability.id)

    def register_worker_capabilities(self, worker_name: str, capability_ids: List[str]) -> None:
        self._worker_capabilities[worker_name] = capability_ids
        for cid in capability_ids:
            if cid not in self._capabilities:
                self._capabilities[cid] = Capability(id=cid, description=f"Capability {cid}")

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> List[Capability]:
        return list(self._capabilities.values())

    def find_worker_for_capability(self, capability_id: str) -> Optional[str]:
        for worker_name, caps in self._worker_capabilities.items():
            if capability_id in caps:
                return worker_name
        return None

    def get_worker_capabilities(self, worker_name: str) -> List[str]:
        return self._worker_capabilities.get(worker_name, [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capabilities": [c.to_dict() for c in self._capabilities.values()],
            "workers": {w: caps for w, caps in self._worker_capabilities.items()},
        }


capability_registry = CapabilityRegistry()
