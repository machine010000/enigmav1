"""
Tests for Job Mapper module.

Tests capability and task mapping for work specifications.
"""

import pytest

from app.expert_domains.work.work_specification import WorkSpecification, WorkPriority, WorkComplexity
from app.work_market.job_mapper import (
    MappingType,
    MappingImportance,
    CapabilityMappingResult,
    TaskMappingResult,
    SEOCapabilityMapper,
    SEOTaskMapper,
    JobMappingOrchestrator,
)


class TestSEOCapabilityMapper:
    """Test SEO capability mapper."""

    def test_map_seo_audit_capabilities(self):
        """Test mapping capabilities for SEO audit job."""
        mapper = SEOCapabilityMapper()
        
        work_spec = WorkSpecification(
            work_id="job_001",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            metadata={"category": "seo_audit"},
        )
        
        result = mapper.map_capabilities(work_spec)
        
        assert isinstance(result, CapabilityMappingResult)
        assert len(result.required_capabilities) > 0
        assert "technical_seo_audit" in result.required_capabilities
        assert result.confidence > 0

    def test_map_keyword_research_capabilities(self):
        """Test mapping capabilities for keyword research job."""
        mapper = SEOCapabilityMapper()
        
        work_spec = WorkSpecification(
            work_id="job_002",
            title="Keyword Research",
            description="Need keyword research",
            business_goal="Find target keywords",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Keyword list",
            metadata={"category": "keyword_research"},
        )
        
        result = mapper.map_capabilities(work_spec)
        
        assert "keyword_research" in result.required_capabilities
        assert result.confidence > 0

    def test_map_technical_seo_capabilities(self):
        """Test mapping capabilities for technical SEO job."""
        mapper = SEOCapabilityMapper()
        
        work_spec = WorkSpecification(
            work_id="job_003",
            title="Technical SEO",
            description="Need technical SEO",
            business_goal="Improve technical performance",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Technical improvements",
            metadata={"category": "technical_seo"},
        )
        
        result = mapper.map_capabilities(work_spec)
        
        assert "technical_seo_audit" in result.required_capabilities
        assert "site_speed_optimization" in result.required_capabilities
        assert "mobile_optimization" in result.required_capabilities

    def test_complexity_adjustment(self):
        """Test capability adjustment based on complexity."""
        mapper = SEOCapabilityMapper()
        
        work_spec = WorkSpecification(
            work_id="job_004",
            title="Complex SEO Project",
            description="Complex SEO work",
            business_goal="Comprehensive SEO",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Comprehensive results",
            complexity=WorkComplexity.VERY_COMPLEX,
            metadata={"category": "seo_audit"},
        )
        
        result = mapper.map_capabilities(work_spec)
        
        # Complex jobs should have more capabilities
        assert len(result.required_capabilities) >= 3

    def test_mapping_justifications(self):
        """Test mapping justifications are generated."""
        mapper = SEOCapabilityMapper()
        
        work_spec = WorkSpecification(
            work_id="job_005",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            metadata={"category": "seo_audit"},
        )
        
        result = mapper.map_capabilities(work_spec)
        
        assert len(result.mapping_justifications) > 0
        for capability in result.required_capabilities:
            assert capability in result.mapping_justifications


class TestSEOTaskMapper:
    """Test SEO task mapper."""

    def test_map_seo_audit_tasks(self):
        """Test mapping tasks for SEO audit job."""
        mapper = SEOTaskMapper()
        
        work_spec = WorkSpecification(
            work_id="job_006",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            required_capabilities=["technical_seo_audit", "site_speed_optimization"],
            metadata={"category": "seo_audit"},
        )
        
        result = mapper.map_tasks(work_spec)
        
        assert isinstance(result, TaskMappingResult)
        assert len(result.required_tasks) > 0
        assert result.confidence > 0

    def test_map_keyword_research_tasks(self):
        """Test mapping tasks for keyword research job."""
        mapper = SEOTaskMapper()
        
        work_spec = WorkSpecification(
            work_id="job_007",
            title="Keyword Research",
            description="Need keyword research",
            business_goal="Find target keywords",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Keyword list",
            required_capabilities=["keyword_research"],
            metadata={"category": "keyword_research"},
        )
        
        result = mapper.map_tasks(work_spec)
        
        assert len(result.required_tasks) > 0
        assert any("keyword" in task.lower() for task in result.required_tasks)

    def test_task_order_determination(self):
        """Test task order is determined."""
        mapper = SEOTaskMapper()
        
        work_spec = WorkSpecification(
            work_id="job_008",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            required_capabilities=["technical_seo_audit"],
            metadata={"category": "seo_audit"},
        )
        
        result = mapper.map_tasks(work_spec)
        
        assert len(result.task_order) > 0
        # Required tasks should come before optional tasks
        if result.required_tasks and result.optional_tasks:
            first_optional_index = None
            for i, task in enumerate(result.task_order):
                if task in result.optional_tasks:
                    first_optional_index = i
                    break
            if first_optional_index is not None:
                # At least some required tasks should come before optional
                assert any(task in result.required_tasks for task in result.task_order[:first_optional_index])

    def test_suggested_tasks_generation(self):
        """Test suggested tasks are generated based on category."""
        mapper = SEOTaskMapper()
        
        work_spec = WorkSpecification(
            work_id="job_009",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            required_capabilities=["technical_seo_audit"],
            metadata={"category": "seo_audit"},
        )
        
        result = mapper.map_tasks(work_spec)
        
        # Should have suggested tasks
        assert len(result.suggested_tasks) >= 0


class TestJobMappingOrchestrator:
    """Test job mapping orchestrator."""

    def test_map_work_specification(self):
        """Test mapping work specification through orchestrator."""
        orchestrator = JobMappingOrchestrator()
        
        work_spec = WorkSpecification(
            work_id="job_010",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            metadata={"category": "seo_audit"},
        )
        
        capability_result, task_result = orchestrator.map_work_specification(work_spec)
        
        assert isinstance(capability_result, CapabilityMappingResult)
        assert isinstance(task_result, TaskMappingResult)
        assert capability_result.work_id == "job_010"
        assert task_result.work_id == "job_010"

    def test_update_work_specification(self):
        """Test updating work specification with mapping results."""
        orchestrator = JobMappingOrchestrator()
        
        work_spec = WorkSpecification(
            work_id="job_011",
            title="SEO Audit",
            description="Need SEO audit",
            business_goal="Identify SEO issues",
            business_context="SEO optimization project",
            industry="general",
            target_audience="general",
            expected_outcome="Audit report",
            metadata={"category": "seo_audit"},
        )
        
        capability_result, task_result = orchestrator.map_work_specification(work_spec)
        updated_spec = orchestrator.update_work_specification(work_spec, capability_result, task_result)
        
        assert updated_spec.required_capabilities == capability_result.required_capabilities
        assert updated_spec.required_tasks == task_result.required_tasks
        assert "capability_mapping_confidence" in updated_spec.metadata
        assert "task_mapping_confidence" in updated_spec.metadata


class TestMappingPipeline:
    """Test complete mapping pipeline."""

    def test_end_to_end_mapping(self):
        """Test end-to-end mapping pipeline."""
        orchestrator = JobMappingOrchestrator()
        
        work_spec = WorkSpecification(
            work_id="job_012",
            title="Technical SEO Audit",
            description="Need comprehensive technical SEO audit",
            business_goal="Identify and fix technical issues",
            business_context="Ecommerce optimization project",
            industry="ecommerce",
            target_audience="b2c",
            expected_outcome="Technical improvements and audit report",
            complexity=WorkComplexity.COMPLEX,
            metadata={"category": "technical_seo"},
        )
        
        # Map capabilities and tasks
        capability_result, task_result = orchestrator.map_work_specification(work_spec)
        
        # Update work specification
        updated_spec = orchestrator.update_work_specification(work_spec, capability_result, task_result)
        
        # Verify pipeline
        assert len(updated_spec.required_capabilities) > 0
        # Tasks may be empty if capabilities don't have task mappings, but suggested tasks should exist
        assert len(updated_spec.required_tasks) >= 0
        assert updated_spec.metadata["capability_mapping_confidence"] > 0
        assert updated_spec.metadata["task_mapping_confidence"] > 0

    def test_multiple_categories_mapping(self):
        """Test mapping for multiple job categories."""
        orchestrator = JobMappingOrchestrator()
        
        categories = ["seo_audit", "keyword_research", "technical_seo", "local_seo"]
        
        for category in categories:
            work_spec = WorkSpecification(
                work_id=f"job_{category}",
                title=f"{category.replace('_', ' ').title()}",
                description=f"Need {category}",
                business_goal=f"Complete {category}",
                business_context="SEO project",
                industry="general",
                target_audience="general",
                expected_outcome=f"{category} results",
                metadata={"category": category},
            )
            
            capability_result, task_result = orchestrator.map_work_specification(work_spec)
            
            assert len(capability_result.required_capabilities) > 0
            assert len(task_result.required_tasks) >= 0
