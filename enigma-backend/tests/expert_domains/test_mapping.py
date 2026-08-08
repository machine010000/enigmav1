import pytest

from app.expert_domains.mapping import (
    ProfessionMapping,
    MappingType,
    Profession,
    CapabilityTaskMapping,
    ProfessionMappingRegistry,
)


class TestProfessionMapping:
    """Tests for ProfessionMapping."""

    def test_profession_mapping_creation(self):
        """Test creating a profession mapping."""
        mapping = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
        )
        assert mapping.mapping_id == "map1"
        assert mapping.mapping_type == MappingType.PROFESSION_TO_CAPABILITY
        assert mapping.profession_id == "seo_specialist"
        assert mapping.target_id == "keyword_research"

    def test_profession_mapping_with_conditions(self):
        """Test profession mapping with conditions."""
        mapping = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
            required=True,
            priority="high",
            conditions=["certified"],
        )
        assert mapping.required is True
        assert mapping.priority == "high"
        assert len(mapping.conditions) == 1


class TestProfession:
    """Tests for Profession."""

    def test_profession_creation(self):
        """Test creating a profession."""
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
        )
        assert profession.profession_id == "seo_specialist"
        assert profession.name == "SEO Specialist"
        assert profession.category == "digital_marketing"

    def test_profession_with_requirements(self):
        """Test profession with requirements."""
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
            required_domains=["seo"],
            supported_capabilities=["keyword_research", "technical_seo"],
            supported_tasks=["seo_audit", "keyword_research"],
        )
        assert len(profession.required_domains) == 1
        assert len(profession.supported_capabilities) == 2
        assert len(profession.supported_tasks) == 2


class TestCapabilityTaskMapping:
    """Tests for CapabilityTaskMapping."""

    def test_capability_task_mapping_creation(self):
        """Test creating a capability-task mapping."""
        mapping = CapabilityTaskMapping(
            mapping_id="ctmap1",
            capability_id="keyword_research",
            task_id="seo_audit",
        )
        assert mapping.mapping_id == "ctmap1"
        assert mapping.capability_id == "keyword_research"
        assert mapping.task_id == "seo_audit"

    def test_capability_task_mapping_with_attributes(self):
        """Test capability-task mapping with attributes."""
        mapping = CapabilityTaskMapping(
            mapping_id="ctmap1",
            capability_id="keyword_research",
            task_id="seo_audit",
            required=True,
            usage_frequency="high",
            complexity="medium",
        )
        assert mapping.required is True
        assert mapping.usage_frequency == "high"
        assert mapping.complexity == "medium"


class TestProfessionMappingRegistry:
    """Tests for ProfessionMappingRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ProfessionMappingRegistry()
        assert len(registry._mappings) == 0
        assert len(registry._professions) == 0
        assert len(registry._capability_task_mappings) == 0

    def test_add_mapping(self):
        """Test adding a mapping."""
        registry = ProfessionMappingRegistry()
        mapping = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
        )
        result = registry.add_mapping(mapping)
        assert result is True
        assert "map1" in registry._mappings

    def test_add_duplicate_mapping(self):
        """Test that adding a duplicate mapping fails."""
        registry = ProfessionMappingRegistry()
        mapping = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
        )
        registry.add_mapping(mapping)
        result = registry.add_mapping(mapping)
        assert result is False

    def test_get_mapping(self):
        """Test retrieving a mapping."""
        registry = ProfessionMappingRegistry()
        mapping = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
        )
        registry.add_mapping(mapping)
        retrieved = registry.get_mapping("map1")
        assert retrieved is not None
        assert retrieved.mapping_id == "map1"

    def test_get_mappings_by_profession(self):
        """Test getting mappings by profession."""
        registry = ProfessionMappingRegistry()
        mapping1 = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
        )
        mapping2 = ProfessionMapping(
            mapping_id="map2",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="technical_seo",
        )
        registry.add_mapping(mapping1)
        registry.add_mapping(mapping2)
        mappings = registry.get_mappings_by_profession("seo_specialist")
        assert len(mappings) == 2

    def test_get_mappings_by_type(self):
        """Test getting mappings by type."""
        registry = ProfessionMappingRegistry()
        mapping1 = ProfessionMapping(
            mapping_id="map1",
            mapping_type=MappingType.PROFESSION_TO_CAPABILITY,
            profession_id="seo_specialist",
            target_id="keyword_research",
        )
        mapping2 = ProfessionMapping(
            mapping_id="map2",
            mapping_type=MappingType.CAPABILITY_TO_TASK,
            profession_id="seo_specialist",
            target_id="seo_audit",
        )
        registry.add_mapping(mapping1)
        registry.add_mapping(mapping2)
        capability_mappings = registry.get_mappings_by_type(MappingType.PROFESSION_TO_CAPABILITY)
        assert len(capability_mappings) == 1

    def test_add_profession(self):
        """Test adding a profession."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
        )
        result = registry.add_profession(profession)
        assert result is True
        assert "seo_specialist" in registry._professions

    def test_get_profession(self):
        """Test retrieving a profession."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
        )
        registry.add_profession(profession)
        retrieved = registry.get_profession("seo_specialist")
        assert retrieved is not None
        assert retrieved.profession_id == "seo_specialist"

    def test_list_professions(self):
        """Test listing all professions."""
        registry = ProfessionMappingRegistry()
        profession1 = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
        )
        profession2 = Profession(
            profession_id="content_creator",
            name="Content Creator",
            description="Expert in content",
            category="content",
        )
        registry.add_profession(profession1)
        registry.add_profession(profession2)
        professions = registry.list_professions()
        assert len(professions) == 2

    def test_add_capability_task_mapping(self):
        """Test adding a capability-task mapping."""
        registry = ProfessionMappingRegistry()
        mapping = CapabilityTaskMapping(
            mapping_id="ctmap1",
            capability_id="keyword_research",
            task_id="seo_audit",
        )
        result = registry.add_capability_task_mapping(mapping)
        assert result is True
        assert "ctmap1" in registry._capability_task_mappings

    def test_get_tasks_for_capability(self):
        """Test getting tasks for a capability."""
        registry = ProfessionMappingRegistry()
        mapping1 = CapabilityTaskMapping(
            mapping_id="ctmap1",
            capability_id="keyword_research",
            task_id="seo_audit",
        )
        mapping2 = CapabilityTaskMapping(
            mapping_id="ctmap2",
            capability_id="keyword_research",
            task_id="keyword_analysis",
        )
        registry.add_capability_task_mapping(mapping1)
        registry.add_capability_task_mapping(mapping2)
        tasks = registry.get_tasks_for_capability("keyword_research")
        assert len(tasks) == 2
        assert "seo_audit" in tasks
        assert "keyword_analysis" in tasks

    def test_get_capabilities_for_task(self):
        """Test getting capabilities for a task."""
        registry = ProfessionMappingRegistry()
        mapping1 = CapabilityTaskMapping(
            mapping_id="ctmap1",
            capability_id="keyword_research",
            task_id="seo_audit",
        )
        mapping2 = CapabilityTaskMapping(
            mapping_id="ctmap2",
            capability_id="technical_seo",
            task_id="seo_audit",
        )
        registry.add_capability_task_mapping(mapping1)
        registry.add_capability_task_mapping(mapping2)
        capabilities = registry.get_capabilities_for_task("seo_audit")
        assert len(capabilities) == 2
        assert "keyword_research" in capabilities
        assert "technical_seo" in capabilities

    def test_get_profession_capabilities(self):
        """Test getting capabilities for a profession."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
            supported_capabilities=["keyword_research", "technical_seo"],
        )
        registry.add_profession(profession)
        capabilities = registry.get_profession_capabilities("seo_specialist")
        assert len(capabilities) == 2
        assert "keyword_research" in capabilities

    def test_get_profession_tasks(self):
        """Test getting tasks for a profession."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
            supported_tasks=["seo_audit", "keyword_research"],
        )
        registry.add_profession(profession)
        tasks = registry.get_profession_tasks("seo_specialist")
        assert len(tasks) == 2
        assert "seo_audit" in tasks

    def test_get_profession_domains(self):
        """Test getting domains for a profession."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
            required_domains=["seo", "analytics"],
        )
        registry.add_profession(profession)
        domains = registry.get_profession_domains("seo_specialist")
        assert len(domains) == 2
        assert "seo" in domains
        assert "analytics" in domains

    def test_validate_profession_requirements_success(self):
        """Test profession requirement validation with all requirements met."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
            required_domains=["seo"],
            supported_capabilities=["keyword_research"],
        )
        registry.add_profession(profession)
        validation = registry.validate_profession_requirements(
            "seo_specialist",
            ["seo"],
            ["keyword_research"],
        )
        assert validation["valid"] is True
        assert validation["domains_met"] is True
        assert validation["capabilities_met"] is True

    def test_validate_profession_requirements_failure(self):
        """Test profession requirement validation with missing requirements."""
        registry = ProfessionMappingRegistry()
        profession = Profession(
            profession_id="seo_specialist",
            name="SEO Specialist",
            description="Expert in SEO",
            category="digital_marketing",
            required_domains=["seo", "analytics"],
            supported_capabilities=["keyword_research", "technical_seo"],
        )
        registry.add_profession(profession)
        validation = registry.validate_profession_requirements(
            "seo_specialist",
            ["seo"],
            ["keyword_research"],
        )
        assert validation["valid"] is False
        assert validation["domains_met"] is False
        assert validation["capabilities_met"] is False
        assert "analytics" in validation["missing_domains"]
        assert "technical_seo" in validation["missing_capabilities"]
