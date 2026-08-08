from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CompatibilityType(str, Enum):
    """Types of compatibility relationships."""
    COMPATIBLE = "compatible"
    DEPENDS_ON = "depends_on"
    RECOMMENDED_TOGETHER = "recommended_together"
    CONFLICTS_WITH = "conflicts_with"
    ENHANCES = "enhances"
    REQUIRES = "requires"


@dataclass(frozen=True)
class CompatibilityRelationship:
    """Represents a compatibility relationship between domains."""
    relationship_id: str
    source_domain: str
    target_domain: str
    relationship_type: CompatibilityType
    strength: float = 1.0  # 0.0 to 1.0
    description: str = ""
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class CompatibilityMatrix:
    """Matrix representing compatibility between domains."""
    matrix_id: str
    domain_id: str
    relationships: List[CompatibilityRelationship] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompatibilityRegistry:
    """Registry for compatibility relationships."""

    def __init__(self) -> None:
        self._relationships: Dict[str, CompatibilityRelationship] = {}
        self._matrices: Dict[str, CompatibilityMatrix] = {}

    def add_relationship(self, relationship: CompatibilityRelationship) -> bool:
        """Add a compatibility relationship."""
        if relationship.relationship_id in self._relationships:
            return False
        self._relationships[relationship.relationship_id] = relationship
        return True

    def get_relationship(self, relationship_id: str) -> Optional[CompatibilityRelationship]:
        """Get a relationship by ID."""
        return self._relationships.get(relationship_id)

    def get_relationships_between(
        self,
        source_domain: str,
        target_domain: str,
    ) -> List[CompatibilityRelationship]:
        """Get relationships between two domains."""
        return [
            r for r in self._relationships.values()
            if r.source_domain == source_domain and r.target_domain == target_domain
        ]

    def get_domain_relationships(
        self,
        domain_id: str,
        relationship_type: Optional[CompatibilityType] = None,
    ) -> List[CompatibilityRelationship]:
        """Get all relationships for a domain."""
        relationships = [
            r for r in self._relationships.values()
            if r.source_domain == domain_id or r.target_domain == domain_id
        ]

        if relationship_type:
            relationships = [r for r in relationships if r.relationship_type == relationship_type]

        return relationships

    def add_matrix(self, matrix: CompatibilityMatrix) -> bool:
        """Add a compatibility matrix."""
        if matrix.matrix_id in self._matrices:
            return False
        self._matrices[matrix.matrix_id] = matrix
        return True

    def get_matrix(self, matrix_id: str) -> Optional[CompatibilityMatrix]:
        """Get a matrix by ID."""
        return self._matrices.get(matrix_id)

    def get_domain_matrix(self, domain_id: str) -> Optional[CompatibilityMatrix]:
        """Get the compatibility matrix for a domain."""
        return next(
            (m for m in self._matrices.values() if m.domain_id == domain_id),
            None,
        )

    def check_compatibility(
        self,
        source_domain: str,
        target_domain: str,
    ) -> Dict[str, Any]:
        """Check compatibility between two domains."""
        relationships = self.get_relationships_between(source_domain, target_domain)

        result = {
            "compatible": True,
            "relationships": [],
            "conflicts": [],
            "dependencies": [],
            "recommendations": [],
        }

        for rel in relationships:
            result["relationships"].append({
                "type": rel.relationship_type.value,
                "strength": rel.strength,
                "description": rel.description,
            })

            if rel.relationship_type == CompatibilityType.CONFLICTS_WITH:
                result["conflicts"].append(rel.relationship_id)
                result["compatible"] = False
            elif rel.relationship_type == CompatibilityType.DEPENDS_ON:
                result["dependencies"].append(rel.relationship_id)
            elif rel.relationship_type == CompatibilityType.RECOMMENDED_TOGETHER:
                result["recommendations"].append(rel.relationship_id)

        return result

    def get_dependencies(self, domain_id: str) -> List[str]:
        """Get all domains that the given domain depends on."""
        relationships = self.get_domain_relationships(
            domain_id,
            CompatibilityType.DEPENDS_ON,
        )
        return [r.target_domain for r in relationships]

    def get_conflicts(self, domain_id: str) -> List[str]:
        """Get all domains that conflict with the given domain."""
        relationships = self.get_domain_relationships(
            domain_id,
            CompatibilityType.CONFLICTS_WITH,
        )
        return [r.target_domain for r in relationships]

    def get_recommendations(self, domain_id: str) -> List[str]:
        """Get all domains recommended to use with the given domain."""
        relationships = self.get_domain_relationships(
            domain_id,
            CompatibilityType.RECOMMENDED_TOGETHER,
        )
        return [r.target_domain for r in relationships]

    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship."""
        if relationship_id in self._relationships:
            del self._relationships[relationship_id]
            return True
        return False

    def remove_matrix(self, matrix_id: str) -> bool:
        """Remove a matrix."""
        if matrix_id in self._matrices:
            del self._matrices[matrix_id]
            return True
        return False
