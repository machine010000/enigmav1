import pytest

from app.expert_domains.work.work_specification import (
    WorkSpecification,
    WorkPriority,
    WorkComplexity,
    WorkStatus,
    WorkCapabilityMapping,
    WorkTaskMapping,
)


class TestWorkSpecification:
    """Tests for WorkSpecification."""

    def test_work_specification_creation(self):
        """Test creating a work specification."""
        spec = WorkSpecification(
            work_id="work1",
            title="SEO Audit",
            description="Comprehensive SEO audit",
            business_goal="Improve search rankings",
            business_context="Website launch",
            industry="E-commerce",
            target_audience="Online shoppers",
            expected_outcome="Increased organic traffic",
        )
        assert spec.work_id == "work1"
        assert spec.title == "SEO Audit"
        assert spec.priority == WorkPriority.MEDIUM
        assert spec.complexity == WorkComplexity.MODERATE
        assert spec.status == WorkStatus.DRAFT

    def test_work_specification_with_capabilities(self):
        """Test work specification with capability mappings."""
        spec = WorkSpecification(
            work_id="work1",
            title="SEO Audit",
            description="Comprehensive SEO audit",
            business_goal="Improve search rankings",
            business_context="Website launch",
            industry="E-commerce",
            target_audience="Online shoppers",
            expected_outcome="Increased organic traffic",
            required_capabilities=["keyword_research", "technical_seo"],
            optional_capabilities=["content_audit"],
            recommended_capabilities=["analytics"],
        )
        assert len(spec.required_capabilities) == 2
        assert len(spec.optional_capabilities) == 1
        assert len(spec.recommended_capabilities) == 1

    def test_work_specification_with_tasks(self):
        """Test work specification with task mappings."""
        spec = WorkSpecification(
            work_id="work1",
            title="SEO Audit",
            description="Comprehensive SEO audit",
            business_goal="Improve search rankings",
            business_context="Website launch",
            industry="E-commerce",
            target_audience="Online shoppers",
            expected_outcome="Increased organic traffic",
            required_tasks=["seo_audit"],
            optional_tasks=["content_optimization"],
            suggested_tasks=["link_building"],
        )
        assert len(spec.required_tasks) == 1
        assert len(spec.optional_tasks) == 1
        assert len(spec.suggested_tasks) == 1


class TestWorkCapabilityMapping:
    """Tests for WorkCapabilityMapping."""

    def test_capability_mapping_creation(self):
        """Test creating a capability mapping."""
        mapping = WorkCapabilityMapping(
            mapping_id="map1",
            work_id="work1",
            capability_id="keyword_research",
            mapping_type="required",
        )
        assert mapping.mapping_id == "map1"
        assert mapping.work_id == "work1"
        assert mapping.capability_id == "keyword_research"
        assert mapping.mapping_type == "required"

    def test_capability_mapping_with_importance(self):
        """Test capability mapping with importance."""
        mapping = WorkCapabilityMapping(
            mapping_id="map1",
            work_id="work1",
            capability_id="keyword_research",
            mapping_type="required",
            importance="high",
            justification="Core capability for SEO",
        )
        assert mapping.importance == "high"
        assert mapping.justification == "Core capability for SEO"


class TestWorkTaskMapping:
    """Tests for WorkTaskMapping."""

    def test_task_mapping_creation(self):
        """Test creating a task mapping."""
        mapping = WorkTaskMapping(
            mapping_id="map1",
            work_id="work1",
            task_id="seo_audit",
            mapping_type="required",
        )
        assert mapping.mapping_id == "map1"
        assert mapping.work_id == "work1"
        assert mapping.task_id == "seo_audit"
        assert mapping.mapping_type == "required"

    def test_task_mapping_with_order(self):
        """Test task mapping with order and dependencies."""
        mapping = WorkTaskMapping(
            mapping_id="map1",
            work_id="work1",
            task_id="seo_audit",
            mapping_type="required",
            order=1,
            estimated_duration="2 hours",
            dependencies=["keyword_research"],
        )
        assert mapping.order == 1
        assert mapping.estimated_duration == "2 hours"
        assert len(mapping.dependencies) == 1
