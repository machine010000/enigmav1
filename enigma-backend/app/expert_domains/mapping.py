from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MappingType(str, Enum):
    """Types of mappings."""
    PROFESSION_TO_CAPABILITY = "profession_to_capability"
    CAPABILITY_TO_TASK = "capability_to_task"
    PROFESSION_TO_TASK = "profession_to_task"
    DOMAIN_TO_PROFESSION = "domain_to_profession"


@dataclass(frozen=True)
class ProfessionMapping:
    """Represents a mapping between professions and domain components."""
    mapping_id: str
    mapping_type: MappingType
    profession_id: str
    target_id: str  # capability_id, task_id, or domain_id
    required: bool = True
    priority: str = "medium"  # low, medium, high, critical
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Profession:
    """Represents a profession."""
    profession_id: str
    name: str
    description: str
    category: str
    parent_profession: Optional[str] = None
    required_domains: List[str] = field(default_factory=list)
    supported_capabilities: List[str] = field(default_factory=list)
    supported_tasks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class CapabilityTaskMapping:
    """Mapping between capabilities and tasks."""
    mapping_id: str
    capability_id: str
    task_id: str
    required: bool = True
    usage_frequency: str = "medium"  # low, medium, high
    complexity: str = "medium"  # low, medium, high
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProfessionMappingRegistry:
    """Registry for profession mappings."""

    def __init__(self) -> None:
        self._mappings: Dict[str, ProfessionMapping] = {}
        self._professions: Dict[str, Profession] = {}
        self._capability_task_mappings: Dict[str, CapabilityTaskMapping] = {}

    def add_mapping(self, mapping: ProfessionMapping) -> bool:
        """Add a profession mapping."""
        if mapping.mapping_id in self._mappings:
            return False
        self._mappings[mapping.mapping_id] = mapping
        return True

    def get_mapping(self, mapping_id: str) -> Optional[ProfessionMapping]:
        """Get a mapping by ID."""
        return self._mappings.get(mapping_id)

    def get_mappings_by_profession(self, profession_id: str) -> List[ProfessionMapping]:
        """Get all mappings for a profession."""
        return [m for m in self._mappings.values() if m.profession_id == profession_id]

    def get_mappings_by_type(
        self,
        mapping_type: MappingType,
    ) -> List[ProfessionMapping]:
        """Get mappings by type."""
        return [m for m in self._mappings.values() if m.mapping_type == mapping_type]

    def add_profession(self, profession: Profession) -> bool:
        """Add a profession."""
        if profession.profession_id in self._professions:
            return False
        self._professions[profession.profession_id] = profession
        return True

    def get_profession(self, profession_id: str) -> Optional[Profession]:
        """Get a profession by ID."""
        return self._professions.get(profession_id)

    def list_professions(self) -> List[Profession]:
        """List all professions."""
        return list(self._professions.values())

    def add_capability_task_mapping(self, mapping: CapabilityTaskMapping) -> bool:
        """Add a capability-task mapping."""
        if mapping.mapping_id in self._capability_task_mappings:
            return False
        self._capability_task_mappings[mapping.mapping_id] = mapping
        return True

    def get_capability_task_mapping(self, mapping_id: str) -> Optional[CapabilityTaskMapping]:
        """Get a capability-task mapping by ID."""
        return self._capability_task_mappings.get(mapping_id)

    def get_tasks_for_capability(self, capability_id: str) -> List[str]:
        """Get all tasks that require a capability."""
        mappings = [
            m for m in self._capability_task_mappings.values()
            if m.capability_id == capability_id
        ]
        return [m.task_id for m in mappings]

    def get_capabilities_for_task(self, task_id: str) -> List[str]:
        """Get all capabilities required for a task."""
        mappings = [
            m for m in self._capability_task_mappings.values()
            if m.task_id == task_id
        ]
        return [m.capability_id for m in mappings]

    def get_profession_capabilities(self, profession_id: str) -> List[str]:
        """Get all capabilities for a profession."""
        profession = self.get_profession(profession_id)
        if not profession:
            return []
        return profession.supported_capabilities

    def get_profession_tasks(self, profession_id: str) -> List[str]:
        """Get all tasks for a profession."""
        profession = self.get_profession(profession_id)
        if not profession:
            return []
        return profession.supported_tasks

    def get_profession_domains(self, profession_id: str) -> List[str]:
        """Get all domains required for a profession."""
        profession = self.get_profession(profession_id)
        if not profession:
            return []
        return profession.required_domains

    def remove_mapping(self, mapping_id: str) -> bool:
        """Remove a mapping."""
        if mapping_id in self._mappings:
            del self._mappings[mapping_id]
            return True
        return False

    def remove_profession(self, profession_id: str) -> bool:
        """Remove a profession."""
        if profession_id in self._professions:
            del self._professions[profession_id]
            return True
        return False

    def remove_capability_task_mapping(self, mapping_id: str) -> bool:
        """Remove a capability-task mapping."""
        if mapping_id in self._capability_task_mappings:
            del self._capability_task_mappings[mapping_id]
            return True
        return False

    def validate_profession_requirements(
        self,
        profession_id: str,
        available_domains: List[str],
        available_capabilities: List[str],
    ) -> Dict[str, bool]:
        """Validate if profession requirements are met."""
        profession = self.get_profession(profession_id)
        if not profession:
            return {"valid": False, "profession_found": False}

        required_domains = set(profession.required_domains)
        available_domains_set = set(available_domains)
        required_capabilities = set(profession.supported_capabilities)
        available_capabilities_set = set(available_capabilities)

        validation = {
            "valid": True,
            "profession_found": True,
            "domains_met": required_domains.issubset(available_domains_set),
            "capabilities_met": required_capabilities.issubset(available_capabilities_set),
            "missing_domains": list(required_domains - available_domains_set),
            "missing_capabilities": list(required_capabilities - available_capabilities_set),
        }

        if not validation["domains_met"]:
            validation["valid"] = False
        if not validation["capabilities_met"]:
            validation["valid"] = False

        return validation
