from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import (
    KnowledgeArea,
    DomainConcept,
    DomainEvidence,
    ReasoningPattern,
    DecisionRule,
    DomainKPI,
    ExecutionStandard,
)


class CapabilityPurpose(str, Enum):
    """Purpose categories for capabilities."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    REPORTING = "reporting"
    DIAGNOSIS = "diagnosis"
    PREDICTION = "prediction"


@dataclass(frozen=True)
class CapabilityContract:
    """Contract for a reusable capability within expert domains."""
    capability_id: str
    name: str
    description: str
    purpose: CapabilityPurpose
    required_knowledge_areas: List[str] = field(default_factory=list)
    required_concepts: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)
    required_reasoning_patterns: List[str] = field(default_factory=list)
    required_decision_rules: List[str] = field(default_factory=list)
    required_kpis: List[str] = field(default_factory=list)
    required_inputs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    supported_tasks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class CapabilityRequirement:
    """Represents a requirement for a capability."""
    requirement_id: str
    capability_id: str
    requirement_type: str  # knowledge, concept, evidence, pattern, rule, kpi
    requirement_value: str
    min_level: Optional[int] = None  # For maturity levels
    optional: bool = False


class CapabilityRegistry:
    """Registry for capabilities."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityContract] = {}

    def register(self, capability: CapabilityContract) -> bool:
        """Register a capability."""
        if capability.capability_id in self._capabilities:
            return False
        self._capabilities[capability.capability_id] = capability
        return True

    def get(self, capability_id: str) -> Optional[CapabilityContract]:
        """Get a capability by ID."""
        return self._capabilities.get(capability_id)

    def list_all(self) -> List[CapabilityContract]:
        """List all capabilities."""
        return list(self._capabilities.values())

    def list_by_purpose(self, purpose: CapabilityPurpose) -> List[CapabilityContract]:
        """List capabilities by purpose."""
        return [c for c in self._capabilities.values() if c.purpose == purpose]

    def remove(self, capability_id: str) -> bool:
        """Remove a capability."""
        if capability_id in self._capabilities:
            del self._capabilities[capability_id]
            return True
        return False

    def validate_requirements(
        self,
        capability_id: str,
        available_knowledge_areas: List[str],
        available_concepts: List[str],
        available_evidence: List[str],
    ) -> Dict[str, bool]:
        """Validate if requirements are met for a capability."""
        capability = self.get(capability_id)
        if not capability:
            return {"valid": False, "capability_found": False}

        validation = {
            "valid": True,
            "capability_found": True,
            "knowledge_areas_met": True,
            "concepts_met": True,
            "evidence_met": True,
        }

        required_areas = set(capability.required_knowledge_areas)
        available_areas = set(available_knowledge_areas)
        if not required_areas.issubset(available_areas):
            validation["knowledge_areas_met"] = False
            validation["valid"] = False

        required_concepts = set(capability.required_concepts)
        available_concepts_set = set(available_concepts)
        if not required_concepts.issubset(available_concepts_set):
            validation["concepts_met"] = False
            validation["valid"] = False

        required_evidence = set(capability.required_evidence)
        available_evidence_set = set(available_evidence)
        if not required_evidence.issubset(available_evidence_set):
            validation["evidence_met"] = False
            validation["valid"] = False

        return validation
