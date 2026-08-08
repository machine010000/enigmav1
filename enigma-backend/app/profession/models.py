from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Profession:
    """Represents a profession (not a tool or software)."""
    id: str
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "status": self.status,
        }


@dataclass(frozen=True)
class Skill:
    """Represents a professional skill (evaluable capability)."""
    id: str
    name: str
    description: str
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
        }


@dataclass(frozen=True)
class ProfessionTask:
    """Represents a task within a profession."""
    id: str
    name: str
    description: str
    required_skills: List[str] = field(default_factory=list)
    required_knowledge: List[str] = field(default_factory=list)
    expected_deliverables: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_skills": self.required_skills,
            "required_knowledge": self.required_knowledge,
            "expected_deliverables": self.expected_deliverables,
            "success_criteria": self.success_criteria,
        }


@dataclass(frozen=True)
class DecisionPattern:
    """Represents professional decision-making patterns (how to think, not just what to know)."""
    id: str
    name: str
    description: str
    condition: str
    action: str
    rationale: str
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "action": self.action,
            "rationale": self.rationale,
            "category": self.category,
        }


@dataclass(frozen=True)
class ProfessionKnowledge:
    """Contract for profession-specific knowledge (ready for Knowledge Governance)."""
    profession_id: str
    concepts: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    maturity: str = "initial"
    freshness: Optional[datetime] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profession_id": self.profession_id,
            "concepts": self.concepts,
            "evidence_sources": self.evidence_sources,
            "maturity": self.maturity,
            "freshness": self.freshness.isoformat() if self.freshness else None,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ProfessionPack:
    """Complete profession package containing all professional knowledge."""
    profession: Profession
    knowledge: ProfessionKnowledge
    skills: List[Skill] = field(default_factory=list)
    tasks: List[ProfessionTask] = field(default_factory=list)
    decision_patterns: List[DecisionPattern] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)  # Tools are NOT capabilities

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profession": self.profession.to_dict(),
            "knowledge": self.knowledge.to_dict(),
            "skills": [skill.to_dict() for skill in self.skills],
            "tasks": [task.to_dict() for task in self.tasks],
            "decision_patterns": [pattern.to_dict() for pattern in self.decision_patterns],
            "kpis": self.kpis,
            "deliverables": self.deliverables,
            "common_mistakes": self.common_mistakes,
            "best_practices": self.best_practices,
            "tools": self.tools,
        }


class ProfessionDetector(ABC):
    """Detects profession from user goal."""

    @abstractmethod
    def detect(self, goal: str) -> Optional[Profession]:
        """Detect profession from goal. Returns None if no match."""
        pass

    @abstractmethod
    def get_confidence(self, goal: str, profession: Profession) -> float:
        """Return confidence score (0.0 to 1.0) for profession detection."""
        pass


class ProfessionRegistry:
    """Registry for profession packs."""

    def __init__(self) -> None:
        self._packs: Dict[str, ProfessionPack] = {}

    def register(self, pack: ProfessionPack) -> None:
        """Register a profession pack."""
        self._packs[pack.profession.id] = pack

    def get(self, profession_id: str) -> Optional[ProfessionPack]:
        """Get profession pack by ID."""
        return self._packs.get(profession_id)

    def find_by_name(self, name: str) -> Optional[ProfessionPack]:
        """Find profession pack by name."""
        for pack in self._packs.values():
            if pack.profession.name.lower() == name.lower():
                return pack
        return None

    def list_all(self) -> List[Profession]:
        """List all registered professions."""
        return [pack.profession for pack in self._packs.values()]

    def list_active(self) -> List[Profession]:
        """List only active professions."""
        return [pack.profession for pack in self._packs.values() if pack.profession.status == "active"]
