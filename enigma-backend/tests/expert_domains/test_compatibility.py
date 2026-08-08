import pytest

from app.expert_domains.compatibility import (
    CompatibilityRelationship,
    CompatibilityType,
    CompatibilityMatrix,
    CompatibilityRegistry,
)


class TestCompatibilityRelationship:
    """Tests for CompatibilityRelationship."""

    def test_compatibility_relationship_creation(self):
        """Test creating a compatibility relationship."""
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        assert relationship.relationship_id == "rel1"
        assert relationship.source_domain == "seo"
        assert relationship.target_domain == "analytics"
        assert relationship.relationship_type == CompatibilityType.COMPATIBLE

    def test_compatibility_relationship_with_strength(self):
        """Test compatibility relationship with strength."""
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
            strength=0.9,
            description="SEO and Analytics work well together",
        )
        assert relationship.strength == 0.9
        assert relationship.description == "SEO and Analytics work well together"


class TestCompatibilityMatrix:
    """Tests for CompatibilityMatrix."""

    def test_compatibility_matrix_creation(self):
        """Test creating a compatibility matrix."""
        matrix = CompatibilityMatrix(
            matrix_id="matrix1",
            domain_id="seo",
        )
        assert matrix.matrix_id == "matrix1"
        assert matrix.domain_id == "seo"

    def test_compatibility_matrix_with_relationships(self):
        """Test compatibility matrix with relationships."""
        relationship1 = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        relationship2 = CompatibilityRelationship(
            relationship_id="rel2",
            source_domain="seo",
            target_domain="content",
            relationship_type=CompatibilityType.DEPENDS_ON,
        )
        matrix = CompatibilityMatrix(
            matrix_id="matrix1",
            domain_id="seo",
            relationships=[relationship1, relationship2],
        )
        assert len(matrix.relationships) == 2


class TestCompatibilityRegistry:
    """Tests for CompatibilityRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CompatibilityRegistry()
        assert len(registry._relationships) == 0
        assert len(registry._matrices) == 0

    def test_add_relationship(self):
        """Test adding a relationship."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        result = registry.add_relationship(relationship)
        assert result is True
        assert "rel1" in registry._relationships

    def test_add_duplicate_relationship(self):
        """Test that adding a duplicate relationship fails."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        registry.add_relationship(relationship)
        result = registry.add_relationship(relationship)
        assert result is False

    def test_get_relationship(self):
        """Test retrieving a relationship."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        registry.add_relationship(relationship)
        retrieved = registry.get_relationship("rel1")
        assert retrieved is not None
        assert retrieved.relationship_id == "rel1"

    def test_get_relationships_between(self):
        """Test getting relationships between two domains."""
        registry = CompatibilityRegistry()
        relationship1 = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        relationship2 = CompatibilityRelationship(
            relationship_id="rel2",
            source_domain="analytics",
            target_domain="seo",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        registry.add_relationship(relationship1)
        registry.add_relationship(relationship2)
        relationships = registry.get_relationships_between("seo", "analytics")
        assert len(relationships) == 1
        assert relationships[0].source_domain == "seo"

    def test_get_domain_relationships(self):
        """Test getting all relationships for a domain."""
        registry = CompatibilityRegistry()
        relationship1 = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        relationship2 = CompatibilityRelationship(
            relationship_id="rel2",
            source_domain="content",
            target_domain="seo",
            relationship_type=CompatibilityType.DEPENDS_ON,
        )
        registry.add_relationship(relationship1)
        registry.add_relationship(relationship2)
        relationships = registry.get_domain_relationships("seo")
        assert len(relationships) == 2

    def test_get_domain_relationships_by_type(self):
        """Test getting relationships for a domain by type."""
        registry = CompatibilityRegistry()
        relationship1 = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        relationship2 = CompatibilityRelationship(
            relationship_id="rel2",
            source_domain="seo",
            target_domain="content",
            relationship_type=CompatibilityType.DEPENDS_ON,
        )
        registry.add_relationship(relationship1)
        registry.add_relationship(relationship2)
        dependencies = registry.get_domain_relationships("seo", CompatibilityType.DEPENDS_ON)
        assert len(dependencies) == 1
        assert dependencies[0].target_domain == "content"

    def test_add_matrix(self):
        """Test adding a matrix."""
        registry = CompatibilityRegistry()
        matrix = CompatibilityMatrix(
            matrix_id="matrix1",
            domain_id="seo",
        )
        result = registry.add_matrix(matrix)
        assert result is True
        assert "matrix1" in registry._matrices

    def test_get_matrix(self):
        """Test retrieving a matrix."""
        registry = CompatibilityRegistry()
        matrix = CompatibilityMatrix(
            matrix_id="matrix1",
            domain_id="seo",
        )
        registry.add_matrix(matrix)
        retrieved = registry.get_matrix("matrix1")
        assert retrieved is not None
        assert retrieved.matrix_id == "matrix1"

    def test_get_domain_matrix(self):
        """Test getting the matrix for a domain."""
        registry = CompatibilityRegistry()
        matrix = CompatibilityMatrix(
            matrix_id="matrix1",
            domain_id="seo",
        )
        registry.add_matrix(matrix)
        retrieved = registry.get_domain_matrix("seo")
        assert retrieved is not None
        assert retrieved.domain_id == "seo"

    def test_check_compatibility_compatible(self):
        """Test compatibility check for compatible domains."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.COMPATIBLE,
        )
        registry.add_relationship(relationship)
        result = registry.check_compatibility("seo", "analytics")
        assert result["compatible"] is True
        assert len(result["relationships"]) == 1

    def test_check_compatibility_conflict(self):
        """Test compatibility check for conflicting domains."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="ads",
            relationship_type=CompatibilityType.CONFLICTS_WITH,
        )
        registry.add_relationship(relationship)
        result = registry.check_compatibility("seo", "ads")
        assert result["compatible"] is False
        assert len(result["conflicts"]) == 1

    def test_get_dependencies(self):
        """Test getting dependencies for a domain."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.DEPENDS_ON,
        )
        registry.add_relationship(relationship)
        dependencies = registry.get_dependencies("seo")
        assert "analytics" in dependencies

    def test_get_conflicts(self):
        """Test getting conflicts for a domain."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="ads",
            relationship_type=CompatibilityType.CONFLICTS_WITH,
        )
        registry.add_relationship(relationship)
        conflicts = registry.get_conflicts("seo")
        assert "ads" in conflicts

    def test_get_recommendations(self):
        """Test getting recommendations for a domain."""
        registry = CompatibilityRegistry()
        relationship = CompatibilityRelationship(
            relationship_id="rel1",
            source_domain="seo",
            target_domain="analytics",
            relationship_type=CompatibilityType.RECOMMENDED_TOGETHER,
        )
        registry.add_relationship(relationship)
        recommendations = registry.get_recommendations("seo")
        assert "analytics" in recommendations
