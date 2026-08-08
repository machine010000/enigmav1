import pytest

from app.expert_domains.work.registry import WorkRegistry, work_registry
from app.expert_domains.work.work_specification import WorkSpecification, WorkCapabilityMapping, WorkTaskMapping
from app.expert_domains.work.requirements import ClientRequirements
from app.expert_domains.work.deliverables import Deliverable, DeliverableInstance
from app.expert_domains.work.acceptance import AcceptanceCriteriaSet, AcceptanceResult
from app.expert_domains.work.review import Review, ReviewChecklist, ReviewPolicy


class TestWorkRegistry:
    """Tests for WorkRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = WorkRegistry()
        assert registry.list_work_specifications() == []

    def test_register_work_specification(self):
        """Test registering a work specification."""
        registry = WorkRegistry()
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
        result = registry.register_work_specification(spec)
        assert result is True
        assert "work1" in [s.work_id for s in registry.list_work_specifications()]

    def test_register_duplicate_work_specification(self):
        """Test that registering a duplicate work specification fails."""
        registry = WorkRegistry()
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
        registry.register_work_specification(spec)
        result = registry.register_work_specification(spec)
        assert result is False

    def test_get_work_specification(self):
        """Test retrieving a work specification."""
        registry = WorkRegistry()
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
        registry.register_work_specification(spec)
        retrieved = registry.get_work_specification("work1")
        assert retrieved is not None
        assert retrieved.work_id == "work1"

    def test_register_capability_mapping(self):
        """Test registering a capability mapping."""
        registry = WorkRegistry()
        mapping = WorkCapabilityMapping(
            mapping_id="map1",
            work_id="work1",
            capability_id="keyword_research",
            mapping_type="required",
        )
        result = registry.register_capability_mapping(mapping)
        assert result is True

    def test_get_capability_mappings_for_work(self):
        """Test getting capability mappings for a work specification."""
        registry = WorkRegistry()
        mapping1 = WorkCapabilityMapping(
            mapping_id="map1",
            work_id="work1",
            capability_id="keyword_research",
            mapping_type="required",
        )
        mapping2 = WorkCapabilityMapping(
            mapping_id="map2",
            work_id="work1",
            capability_id="technical_seo",
            mapping_type="required",
        )
        registry.register_capability_mapping(mapping1)
        registry.register_capability_mapping(mapping2)
        mappings = registry.get_capability_mappings_for_work("work1")
        assert len(mappings) == 2

    def test_register_task_mapping(self):
        """Test registering a task mapping."""
        registry = WorkRegistry()
        mapping = WorkTaskMapping(
            mapping_id="map1",
            work_id="work1",
            task_id="seo_audit",
            mapping_type="required",
        )
        result = registry.register_task_mapping(mapping)
        assert result is True

    def test_get_task_mappings_for_work(self):
        """Test getting task mappings for a work specification."""
        registry = WorkRegistry()
        mapping = WorkTaskMapping(
            mapping_id="map1",
            work_id="work1",
            task_id="seo_audit",
            mapping_type="required",
        )
        registry.register_task_mapping(mapping)
        mappings = registry.get_task_mappings_for_work("work1")
        assert len(mappings) == 1

    def test_register_client_requirements(self):
        """Test registering client requirements."""
        registry = WorkRegistry()
        reqs = ClientRequirements(
            requirements_id="reqs1",
            work_id="work1",
        )
        result = registry.register_client_requirements(reqs)
        assert result is True

    def test_get_requirements_for_work(self):
        """Test getting requirements for a work specification."""
        registry = WorkRegistry()
        reqs = ClientRequirements(
            requirements_id="reqs1",
            work_id="work1",
        )
        registry.register_client_requirements(reqs)
        retrieved = registry.get_requirements_for_work("work1")
        assert retrieved is not None
        assert retrieved.work_id == "work1"

    def test_register_deliverable(self):
        """Test registering a deliverable."""
        registry = WorkRegistry()
        from app.expert_domains.work.deliverables import DeliverableType, DeliverableFormat
        deliverable = Deliverable(
            deliverable_id="del1",
            name="SEO Audit Report",
            description="Comprehensive SEO audit report",
            deliverable_type=DeliverableType.REPORT,
            format=DeliverableFormat.PDF,
            expected_audience="Client",
            quality_standard="High",
            validation_method="Manual review",
        )
        result = registry.register_deliverable(deliverable)
        assert result is True

    def test_register_deliverable_instance(self):
        """Test registering a deliverable instance."""
        registry = WorkRegistry()
        instance = DeliverableInstance(
            instance_id="inst1",
            deliverable_id="del1",
            work_id="work1",
        )
        result = registry.register_deliverable_instance(instance)
        assert result is True

    def test_get_instances_for_work(self):
        """Test getting deliverable instances for a work specification."""
        registry = WorkRegistry()
        instance = DeliverableInstance(
            instance_id="inst1",
            deliverable_id="del1",
            work_id="work1",
        )
        registry.register_deliverable_instance(instance)
        instances = registry.get_instances_for_work("work1")
        assert len(instances) == 1

    def test_register_acceptance_criteria_set(self):
        """Test registering an acceptance criteria set."""
        registry = WorkRegistry()
        criteria_set = AcceptanceCriteriaSet(
            criteria_set_id="set1",
            name="Quality Criteria",
            description="Quality criteria for deliverables",
            target_type="deliverable",
            target_id="del1",
        )
        result = registry.register_acceptance_criteria_set(criteria_set)
        assert result is True

    def test_register_acceptance_result(self):
        """Test registering an acceptance result."""
        registry = WorkRegistry()
        result = AcceptanceResult(
            result_id="res1",
            criteria_set_id="set1",
            target_id="del1",
            passed=True,
            overall_score=1.0,
        )
        registry.register_acceptance_result(result)
        retrieved = registry.get_acceptance_result("res1")
        assert retrieved is not None

    def test_register_review(self):
        """Test registering a review."""
        registry = WorkRegistry()
        from app.expert_domains.work.review import ReviewType
        review = Review(
            review_id="rev1",
            target_type="deliverable",
            target_id="del1",
            review_type=ReviewType.QUALITY,
            reviewer="quality_specialist",
        )
        result = registry.register_review(review)
        assert result is True

    def test_get_reviews_for_target(self):
        """Test getting reviews for a target."""
        registry = WorkRegistry()
        from app.expert_domains.work.review import ReviewType
        review = Review(
            review_id="rev1",
            target_type="deliverable",
            target_id="del1",
            review_type=ReviewType.QUALITY,
            reviewer="quality_specialist",
        )
        registry.register_review(review)
        reviews = registry.get_reviews_for_target("deliverable", "del1")
        assert len(reviews) == 1

    def test_register_review_checklist(self):
        """Test registering a review checklist."""
        registry = WorkRegistry()
        from app.expert_domains.work.review import ReviewType
        checklist = ReviewChecklist(
            checklist_id="check1",
            name="Quality Checklist",
            description="Checklist for quality reviews",
            review_type=ReviewType.QUALITY,
        )
        result = registry.register_review_checklist(checklist)
        assert result is True

    def test_register_review_policy(self):
        """Test registering a review policy."""
        registry = WorkRegistry()
        from app.expert_domains.work.review import ReviewType
        policy = ReviewPolicy(
            policy_id="policy1",
            name="Standard Policy",
            description="Standard review policy",
            target_type="deliverable",
            required_review_types=[ReviewType.QUALITY],
        )
        result = registry.register_review_policy(policy)
        assert result is True

    def test_validate_work_requirements_success(self):
        """Test work requirement validation with all components."""
        registry = WorkRegistry()
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
        registry.register_work_specification(spec)
        reqs = ClientRequirements(
            requirements_id="reqs1",
            work_id="work1",
        )
        registry.register_client_requirements(reqs)
        mapping = WorkCapabilityMapping(
            mapping_id="map1",
            work_id="work1",
            capability_id="keyword_research",
            mapping_type="required",
        )
        registry.register_capability_mapping(mapping)
        task_mapping = WorkTaskMapping(
            mapping_id="taskmap1",
            work_id="work1",
            task_id="seo_audit",
            mapping_type="required",
        )
        registry.register_task_mapping(task_mapping)
        instance = DeliverableInstance(
            instance_id="inst1",
            deliverable_id="del1",
            work_id="work1",
        )
        registry.register_deliverable_instance(instance)

        validation = registry.validate_work_requirements("work1")
        assert validation["valid"] is True
        assert validation["has_specification"] is True
        assert validation["has_requirements"] is True
        assert validation["has_capability_mappings"] is True
        assert validation["has_task_mappings"] is True
        assert validation["has_deliverables"] is True

    def test_validate_work_requirements_failure(self):
        """Test work requirement validation with missing components."""
        registry = WorkRegistry()
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
        registry.register_work_specification(spec)

        validation = registry.validate_work_requirements("work1")
        assert validation["valid"] is False
        assert validation["has_specification"] is True
        assert validation["has_requirements"] is False

    def test_global_registry_exists(self):
        """Test that the global registry exists."""
        assert work_registry is not None
        assert isinstance(work_registry, WorkRegistry)
