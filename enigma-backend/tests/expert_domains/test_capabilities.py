import pytest

from app.expert_domains.capabilities import (
    CapabilityContract,
    CapabilityPurpose,
    CapabilityRequirement,
    CapabilityRegistry,
)


class TestCapabilityContract:
    """Tests for CapabilityContract."""

    def test_capability_contract_creation(self):
        """Test creating a capability contract."""
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
        )
        assert capability.capability_id == "keyword_research"
        assert capability.name == "Keyword Research"
        assert capability.purpose == CapabilityPurpose.ANALYSIS

    def test_capability_contract_with_requirements(self):
        """Test capability with requirements."""
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
            required_knowledge_areas=["seo_basics"],
            required_concepts=["keyword"],
            required_evidence=["search_volume"],
        )
        assert len(capability.required_knowledge_areas) == 1
        assert len(capability.required_concepts) == 1
        assert len(capability.required_evidence) == 1


class TestCapabilityRequirement:
    """Tests for CapabilityRequirement."""

    def test_capability_requirement_creation(self):
        """Test creating a capability requirement."""
        requirement = CapabilityRequirement(
            requirement_id="req1",
            capability_id="keyword_research",
            requirement_type="knowledge",
            requirement_value="seo_basics",
        )
        assert requirement.requirement_id == "req1"
        assert requirement.capability_id == "keyword_research"
        assert requirement.requirement_type == "knowledge"
        assert requirement.optional is False


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CapabilityRegistry()
        assert registry.list_all() == []

    def test_register_capability(self):
        """Test registering a capability."""
        registry = CapabilityRegistry()
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
        )
        result = registry.register(capability)
        assert result is True
        assert "keyword_research" in [c.capability_id for c in registry.list_all()]

    def test_register_duplicate_capability(self):
        """Test that registering a duplicate capability fails."""
        registry = CapabilityRegistry()
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
        )
        registry.register(capability)
        result = registry.register(capability)
        assert result is False

    def test_get_capability(self):
        """Test retrieving a capability."""
        registry = CapabilityRegistry()
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
        )
        registry.register(capability)
        retrieved = registry.get("keyword_research")
        assert retrieved is not None
        assert retrieved.capability_id == "keyword_research"

    def test_get_nonexistent_capability(self):
        """Test retrieving a nonexistent capability."""
        registry = CapabilityRegistry()
        retrieved = registry.get("nonexistent")
        assert retrieved is None

    def test_list_by_purpose(self):
        """Test listing capabilities by purpose."""
        registry = CapabilityRegistry()
        capability1 = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
        )
        capability2 = CapabilityContract(
            capability_id="content_planning",
            name="Content Planning",
            description="Plan content strategy",
            purpose=CapabilityPurpose.PLANNING,
        )
        registry.register(capability1)
        registry.register(capability2)
        analysis_capabilities = registry.list_by_purpose(CapabilityPurpose.ANALYSIS)
        assert len(analysis_capabilities) == 1
        assert analysis_capabilities[0].capability_id == "keyword_research"

    def test_remove_capability(self):
        """Test removing a capability."""
        registry = CapabilityRegistry()
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
        )
        registry.register(capability)
        result = registry.remove("keyword_research")
        assert result is True
        assert registry.get("keyword_research") is None

    def test_validate_requirements_success(self):
        """Test requirement validation with all requirements met."""
        registry = CapabilityRegistry()
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
            required_knowledge_areas=["seo_basics"],
            required_concepts=["keyword"],
            required_evidence=["search_volume"],
        )
        registry.register(capability)
        validation = registry.validate_requirements(
            "keyword_research",
            ["seo_basics"],
            ["keyword"],
            ["search_volume"],
        )
        assert validation["valid"] is True
        assert validation["knowledge_areas_met"] is True
        assert validation["concepts_met"] is True
        assert validation["evidence_met"] is True

    def test_validate_requirements_failure(self):
        """Test requirement validation with missing requirements."""
        registry = CapabilityRegistry()
        capability = CapabilityContract(
            capability_id="keyword_research",
            name="Keyword Research",
            description="Research keywords for SEO",
            purpose=CapabilityPurpose.ANALYSIS,
            required_knowledge_areas=["seo_basics"],
            required_concepts=["keyword"],
            required_evidence=["search_volume"],
        )
        registry.register(capability)
        validation = registry.validate_requirements(
            "keyword_research",
            [],
            [],
            [],
        )
        assert validation["valid"] is False
        assert validation["knowledge_areas_met"] is False
        assert validation["concepts_met"] is False
        assert validation["evidence_met"] is False
