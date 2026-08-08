"""
Tests for Execution Planner module.

Tests plan creation from work specifications and templates.
"""

import pytest
from dataclasses import dataclass, field
from datetime import datetime

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
)
from app.execution.planner import BaseExecutionPlanner, TemplateBasedPlanner


@dataclass(frozen=True)
class MockWorkSpecification:
    """Mock work specification for testing."""
    work_id: str
    title: str
    description: str
    business_goal: str
    business_context: str
    industry: str
    target_audience: str
    expected_outcome: str
    constraints: list = field(default_factory=list)
    priority: str = "medium"
    complexity: str = "moderate"
    required_capabilities: list = field(default_factory=list)
    optional_capabilities: list = field(default_factory=list)
    recommended_capabilities: list = field(default_factory=list)
    required_tasks: list = field(default_factory=list)
    optional_tasks: list = field(default_factory=list)
    suggested_tasks: list = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


class TestBaseExecutionPlanner:
    """Test BaseExecutionPlanner."""

    def test_create_plan_without_work_spec(self):
        """Test creating plan without work specification."""
        planner = BaseExecutionPlanner()
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={},
        )
        
        assert plan.plan_id == "plan_session_001"
        assert plan.session_id == "session_001"
        assert plan.domain_id == "seo"
        assert len(plan.steps) == 0

    def test_create_plan_with_work_spec(self):
        """Test creating plan with work specification."""
        planner = BaseExecutionPlanner()
        
        work_spec = MockWorkSpecification(
            work_id="work_spec_001",
            title="SEO Audit",
            description="SEO audit work",
            business_goal="Improve SEO",
            business_context="SEO project",
            industry="technology",
            target_audience="general",
            expected_outcome="Better SEO",
            required_capabilities=["technical_seo_audit", "keyword_research"],
            required_tasks=["crawl_site", "analyze_content"],
        )
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"work_specification": work_spec},
        )
        
        assert len(plan.steps) > 0
        assert len(plan.step_order) > 0
        # Should have capability steps
        capability_steps = [s for s in plan.steps if s.step_type == StepType.CAPABILITY]
        assert len(capability_steps) >= 2

    def test_plan_step_order(self):
        """Test step order is determined correctly."""
        planner = BaseExecutionPlanner()
        
        work_spec = MockWorkSpecification(
            work_id="work_spec_001",
            title="SEO Audit",
            description="SEO audit work",
            business_goal="Improve SEO",
            business_context="SEO project",
            industry="technology",
            target_audience="general",
            expected_outcome="Better SEO",
            required_capabilities=["capability_1"],
            required_tasks=["task_1"],
        )
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"work_specification": work_spec},
        )
        
        # Step order should be a list
        assert isinstance(plan.step_order, list)
        # All step IDs in order should exist in steps
        for step_id in plan.step_order:
            assert any(s.step_id == step_id for s in plan.steps)

    def test_plan_quality_gates(self):
        """Test quality gates are identified."""
        planner = BaseExecutionPlanner()
        
        work_spec = MockWorkSpecification(
            work_id="work_spec_001",
            title="SEO Audit",
            description="SEO audit work",
            business_goal="Improve SEO",
            business_context="SEO project",
            industry="technology",
            target_audience="general",
            expected_outcome="Better SEO",
            required_capabilities=["capability_1"],
        )
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"work_specification": work_spec},
        )
        
        # Deliverable steps should be quality gates
        deliverable_steps = [s for s in plan.steps if s.step_type == StepType.DELIVERABLE]
        if deliverable_steps:
            assert len(plan.quality_gates) > 0

    def test_plan_milestones(self):
        """Test milestones are identified."""
        planner = BaseExecutionPlanner()
        
        work_spec = MockWorkSpecification(
            work_id="work_spec_001",
            title="SEO Audit",
            description="SEO audit work",
            business_goal="Improve SEO",
            business_context="SEO project",
            industry="technology",
            target_audience="general",
            expected_outcome="Better SEO",
            required_capabilities=["capability_1", "capability_2"],
        )
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"work_specification": work_spec},
        )
        
        # Capability steps should be milestones
        capability_steps = [s for s in plan.steps if s.step_type == StepType.CAPABILITY]
        if capability_steps:
            assert len(plan.milestones) > 0


class TestTemplateBasedPlanner:
    """Test TemplateBasedPlanner."""

    def test_register_template(self):
        """Test registering a template."""
        planner = TemplateBasedPlanner()
        
        template = {
            "steps": [
                {
                    "step_id": "step_001",
                    "step_type": "capability",
                    "name": "Capability 1",
                    "description": "First capability",
                    "dependencies": [],
                }
            ],
            "step_order": ["step_001"],
        }
        
        planner.register_template("template_001", template)
        
        assert "template_001" in planner._templates

    def test_create_plan_from_template(self):
        """Test creating plan from template."""
        planner = TemplateBasedPlanner()
        
        template = {
            "steps": [
                {
                    "step_id": "step_001",
                    "step_type": "capability",
                    "name": "Capability 1",
                    "description": "First capability",
                    "dependencies": [],
                    "expected_outputs": ["output_1"],
                },
                {
                    "step_id": "step_002",
                    "step_type": "task",
                    "name": "Task 1",
                    "description": "First task",
                    "dependencies": ["step_001"],
                    "expected_outputs": ["output_2"],
                }
            ],
            "step_order": ["step_001", "step_002"],
            "quality_gates": ["step_002"],
            "milestones": ["step_001"],
        }
        
        planner.register_template("template_001", template)
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"template_id": "template_001"},
        )
        
        assert len(plan.steps) == 2
        assert plan.step_order == ["step_001", "step_002"]
        assert plan.quality_gates == ["step_002"]
        assert plan.milestones == ["step_001"]

    def test_create_plan_from_nonexistent_template(self):
        """Test creating plan from nonexistent template."""
        planner = TemplateBasedPlanner()
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"template_id": "nonexistent"},
        )
        
        # Should create empty plan
        assert len(plan.steps) == 0

    def test_template_with_custom_step_order(self):
        """Test template with custom step order."""
        planner = TemplateBasedPlanner()
        
        template = {
            "steps": [
                {
                    "step_id": "step_001",
                    "step_type": "capability",
                    "name": "Capability 1",
                    "description": "First capability",
                },
                {
                    "step_id": "step_002",
                    "step_type": "task",
                    "name": "Task 1",
                    "description": "First task",
                }
            ],
            "step_order": ["step_002", "step_001"],  # Reverse order
        }
        
        planner.register_template("template_001", template)
        
        plan = planner.create_plan(
            work_specification_id="work_spec_001",
            domain_id="seo",
            session_id="session_001",
            context={"template_id": "template_001"},
        )
        
        assert plan.step_order == ["step_002", "step_001"]
