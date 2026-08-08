"""
Tests for Execution Scheduler module.

Tests step scheduling, dependency resolution, and execution order.
"""

import pytest

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
)
from app.execution.scheduler import BaseExecutionScheduler, PriorityExecutionScheduler


class TestBaseExecutionScheduler:
    """Test BaseExecutionScheduler."""

    def test_get_next_step_with_pending_steps(self):
        """Test getting next step with pending steps."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.PENDING}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        assert next_step is not None
        assert next_step.step_id == "step_001"

    def test_get_next_step_with_dependencies(self):
        """Test getting next step with dependencies."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
            dependencies=["step_001"],
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
        )
        
        # Step 2 should not be ready if step 1 is not done
        current_state = {"step_001": StepState.PENDING, "step_002": StepState.PENDING}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        assert next_step is not None
        assert next_step.step_id == "step_001"

    def test_get_next_step_with_completed_dependency(self):
        """Test getting next step when dependency is completed."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
            dependencies=["step_001"],
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
        )
        
        # Step 2 should be ready if step 1 is done
        current_state = {"step_001": StepState.DONE, "step_002": StepState.PENDING}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        assert next_step is not None
        assert next_step.step_id == "step_002"

    def test_get_next_step_all_done(self):
        """Test getting next step when all steps are done."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.DONE}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        assert next_step is None

    def test_get_next_step_with_failed_step(self):
        """Test getting next step with failed step."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
            max_retries=3,
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.FAILED}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        # Should return step for retry
        assert next_step is not None
        assert next_step.step_id == "step_001"

    def test_get_next_step_no_retries_left(self):
        """Test getting next step when no retries left."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
            retry_count=3,
            max_retries=3,
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.FAILED}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        # Should not return step if no retries left
        assert next_step is None

    def test_get_ready_steps(self):
        """Test getting all ready steps."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.CAPABILITY,
            name="Capability 2",
            description="Second capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
        )
        
        current_state = {"step_001": StepState.PENDING, "step_002": StepState.PENDING}
        
        ready_steps = scheduler.get_ready_steps(plan, current_state)
        
        assert len(ready_steps) == 2

    def test_get_blocked_steps(self):
        """Test getting blocked steps."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
            dependencies=["step_001"],
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
        )
        
        current_state = {"step_001": StepState.PENDING, "step_002": StepState.PENDING}
        
        blocked = scheduler.get_blocked_steps(plan, current_state)
        
        assert "step_002" in blocked
        assert "step_001" in blocked["step_002"]

    def test_get_failed_steps(self):
        """Test getting failed steps."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
            retry_count=3,
            max_retries=3,
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.FAILED}
        
        failed_steps = scheduler.get_failed_steps(plan, current_state)
        
        assert len(failed_steps) == 1
        assert failed_steps[0].step_id == "step_001"

    def test_can_proceed(self):
        """Test checking if execution can proceed."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.PENDING}
        
        can_proceed = scheduler.can_proceed(plan, current_state)
        
        assert can_proceed is True

    def test_can_proceed_with_critical_failure(self):
        """Test checking if execution can proceed with critical failure."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Deliverable 1",
            description="First deliverable",
            retry_count=3,
            max_retries=3,
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
            quality_gates=["step_001"],
        )
        
        current_state = {"step_001": StepState.FAILED}
        
        can_proceed = scheduler.can_proceed(plan, current_state)
        
        # Should not proceed if quality gate failed
        assert can_proceed is False

    def test_is_execution_complete(self):
        """Test checking if execution is complete."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        current_state = {"step_001": StepState.DONE}
        
        is_complete = scheduler.is_execution_complete(plan, current_state)
        
        assert is_complete is True

    def test_get_completion_percentage(self):
        """Test getting completion percentage."""
        scheduler = BaseExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.CAPABILITY,
            name="Capability 2",
            description="Second capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
        )
        
        current_state = {"step_001": StepState.DONE, "step_002": StepState.PENDING}
        
        percentage = scheduler.get_completion_percentage(plan, current_state)
        
        assert percentage == 0.5

    def test_get_completion_percentage_empty_plan(self):
        """Test getting completion percentage for empty plan."""
        scheduler = BaseExecutionScheduler()
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[],
            step_order=[],
        )
        
        percentage = scheduler.get_completion_percentage(plan, {})
        
        assert percentage == 1.0


class TestPriorityExecutionScheduler:
    """Test PriorityExecutionScheduler."""

    def test_prioritize_milestones(self):
        """Test that milestones are prioritized."""
        scheduler = PriorityExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
            milestones=["step_002"],
        )
        
        current_state = {"step_001": StepState.PENDING, "step_002": StepState.PENDING}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        # Milestone should be prioritized
        assert next_step is not None
        assert next_step.step_id == "step_002"

    def test_prioritize_quality_gates(self):
        """Test that quality gates are prioritized."""
        scheduler = PriorityExecutionScheduler()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.DELIVERABLE,
            name="Deliverable 1",
            description="First deliverable",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
            quality_gates=["step_002"],
        )
        
        current_state = {"step_001": StepState.PENDING, "step_002": StepState.PENDING}
        
        next_step = scheduler.get_next_step(plan, current_state)
        
        # Quality gate should be prioritized
        assert next_step is not None
        assert next_step.step_id == "step_002"
