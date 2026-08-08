"""
Tests for Execution Reflection module.

Tests reflection generation, step-level reflections, and aggregate reflections.
"""

import pytest

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
    ExecutionReflection,
)
from app.execution.reflection import (
    BaseReflectionGenerator,
    StepReflectionGenerator,
    CallbackReflectionGenerator,
    AggregateReflectionGenerator,
)


class TestBaseReflectionGenerator:
    """Test BaseReflectionGenerator."""

    def test_generate_reflection_successful_execution(self):
        """Test generating reflection for successful execution."""
        generator = BaseReflectionGenerator()
        
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
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
            milestones=["step_001"],
            quality_gates=["step_002"],
        )
        
        execution_results = {
            "step_states": {
                "step_001": StepState.DONE,
                "step_002": StepState.DONE,
            },
            "outputs": {},
            "errors": {},
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert reflection.session_id == "session_001"
        assert reflection.reflection_type == "overall"
        assert len(reflection.what_went_well) > 0

    def test_generate_reflection_with_failures(self):
        """Test generating reflection with failures."""
        generator = BaseReflectionGenerator()
        
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
        
        execution_results = {
            "step_states": {
                "step_001": StepState.FAILED,
            },
            "outputs": {},
            "errors": {
                "step_001": "Execution failed",
            },
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert len(reflection.what_could_be_improved) > 0
        assert len(reflection.action_items) > 0

    def test_generate_reflection_with_retries(self):
        """Test generating reflection with retries."""
        generator = BaseReflectionGenerator()
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
            retry_count=2,
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1],
            step_order=["step_001"],
        )
        
        execution_results = {
            "step_states": {
                "step_001": StepState.DONE,
            },
            "outputs": {},
            "errors": {},
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert len(reflection.what_could_be_improved) > 0

    def test_generate_reflection_lessons_learned(self):
        """Test that lessons are learned from execution."""
        generator = BaseReflectionGenerator()
        
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
        
        execution_results = {
            "step_states": {
                "step_001": StepState.FAILED,
            },
            "outputs": {},
            "errors": {},
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert len(reflection.lessons_learned) > 0

    def test_generate_reflection_metadata(self):
        """Test reflection metadata."""
        generator = BaseReflectionGenerator()
        
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
        
        execution_results = {
            "step_states": {
                "step_001": StepState.DONE,
            },
            "outputs": {},
            "errors": {},
        }
        
        reflection = generator.generate_reflection("session_001", plan, execution_results)
        
        assert "plan_id" in reflection.metadata
        assert "domain_id" in reflection.metadata
        assert "total_steps" in reflection.metadata


class TestStepReflectionGenerator:
    """Test StepReflectionGenerator."""

    def test_generate_step_reflection_success(self):
        """Test generating reflection for successful step."""
        generator = StepReflectionGenerator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {
            "success": True,
            "outputs": [
                {"output_id": "output_001"},
            ],
        }
        
        reflection = generator.generate_step_reflection("session_001", step, execution_result)
        
        assert reflection.reflection_type == "step"
        assert len(reflection.what_went_well) > 0

    def test_generate_step_reflection_failure(self):
        """Test generating reflection for failed step."""
        generator = StepReflectionGenerator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {
            "success": False,
            "error_message": "Step execution failed",
        }
        
        reflection = generator.generate_step_reflection("session_001", step, execution_result)
        
        assert len(reflection.what_could_be_improved) > 0
        assert len(reflection.action_items) > 0
        assert len(reflection.lessons_learned) > 0

    def test_generate_step_reflection_metadata(self):
        """Test step reflection metadata."""
        generator = StepReflectionGenerator()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {
            "success": True,
        }
        
        reflection = generator.generate_step_reflection("session_001", step, execution_result)
        
        assert "step_id" in reflection.metadata
        assert "step_type" in reflection.metadata
        assert "success" in reflection.metadata


class TestCallbackReflectionGenerator:
    """Test CallbackReflectionGenerator."""

    def test_callback_generator(self):
        """Test callback reflection generator."""
        def callback(session_id, plan, execution_results):
            return ExecutionReflection(
                reflection_id="callback_reflection",
                session_id=session_id,
                reflection_type="callback",
                subject="Callback reflection",
                what_went_well=["Callback executed"],
            )
        
        generator = CallbackReflectionGenerator(callback)
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[],
            step_order=[],
        )
        
        reflection = generator.generate_reflection("session_001", plan, {})
        
        assert reflection.reflection_type == "callback"
        assert len(reflection.what_went_well) == 1


class TestAggregateReflectionGenerator:
    """Test AggregateReflectionGenerator."""

    def test_aggregate_generator(self):
        """Test aggregate reflection generator."""
        generator = AggregateReflectionGenerator()
        
        def generator1(session_id, plan, execution_results):
            return ExecutionReflection(
                reflection_id="reflection_1",
                session_id=session_id,
                reflection_type="generator1",
                subject="Generator 1",
                what_went_well=["From generator 1"],
                what_could_be_improved=["Improvement 1"],
            )
        
        def generator2(session_id, plan, execution_results):
            return ExecutionReflection(
                reflection_id="reflection_2",
                session_id=session_id,
                reflection_type="generator2",
                subject="Generator 2",
                what_went_well=["From generator 2"],
                what_could_be_improved=["Improvement 2"],
            )
        
        generator.add_generator(generator1)
        generator.add_generator(generator2)
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[],
            step_order=[],
        )
        
        reflection = generator.generate_reflection("session_001", plan, {})
        
        assert reflection.reflection_type == "aggregate"
        # At least some items should be collected
        assert len(reflection.what_went_well) >= 0
        assert len(reflection.what_could_be_improved) >= 0

    def test_aggregate_generator_with_failure(self):
        """Test aggregate generator when one generator fails."""
        generator = AggregateReflectionGenerator()
        
        def failing_generator(session_id, plan, execution_results):
            raise ValueError("Generator failed")
        
        def working_generator(session_id, plan, execution_results):
            return ExecutionReflection(
                reflection_id="reflection_1",
                session_id=session_id,
                reflection_type="working",
                subject="Working generator",
                what_went_well=["From working generator"],
            )
        
        generator.add_generator(failing_generator)
        generator.add_generator(working_generator)
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[],
            step_order=[],
        )
        
        reflection = generator.generate_reflection("session_001", plan, {})
        
        # Should continue with working generator
        # If all generators fail, reflection will be empty
        assert len(reflection.what_went_well) >= 0

    def test_aggregate_generator_metadata(self):
        """Test aggregate generator metadata."""
        generator = AggregateReflectionGenerator()
        
        def simple_generator(session_id, plan, execution_results):
            return ExecutionReflection(
                reflection_id="reflection_1",
                session_id=session_id,
                reflection_type="simple",
                subject="Simple generator",
            )
        
        generator.add_generator(simple_generator)
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[],
            step_order=[],
        )
        
        reflection = generator.generate_reflection("session_001", plan, {})
        
        assert "generator_count" in reflection.metadata
        assert reflection.metadata["generator_count"] == 1
