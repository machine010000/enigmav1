"""
Tests for Execution Executor module.

Tests worker execution, executor orchestration, and result handling.
"""

import pytest

from app.execution.contracts import (
    ExecutionStep,
    StepState,
    StepType,
    ExecutionOutput,
    OutputType,
)
from app.execution.executor import (
    BaseExecutor,
    MockWorker,
    CallbackWorker,
    ExecutionContext,
    ExecutionResult,
)


class TestExecutionContext:
    """Test ExecutionContext dataclass."""

    def test_create_execution_context(self):
        """Test creating execution context."""
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"input1": "value1"},
            metadata={"key": "value"},
        )
        
        assert context.session_id == "session_001"
        assert context.step_id == "step_001"
        assert context.inputs == {"input1": "value1"}


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_create_execution_result(self):
        """Test creating execution result."""
        result = ExecutionResult(
            step_id="step_001",
            success=True,
            execution_time_seconds=1.5,
        )
        
        assert result.step_id == "step_001"
        assert result.success is True
        assert result.execution_time_seconds == 1.5

    def test_execution_result_with_outputs(self):
        """Test execution result with outputs."""
        output = ExecutionOutput(
            output_id="output_001",
            step_id="step_001",
            session_id="session_001",
            output_type=OutputType.ARTIFACT,
            name="Output 1",
            description="First output",
        )
        
        result = ExecutionResult(
            step_id="step_001",
            success=True,
            outputs=[output],
        )
        
        assert len(result.outputs) == 1
        assert result.outputs[0].output_id == "output_001"

    def test_execution_result_with_error(self):
        """Test execution result with error."""
        result = ExecutionResult(
            step_id="step_001",
            success=False,
            error_message="Execution failed",
            error_details={"error_code": 500},
        )
        
        assert result.success is False
        assert result.error_message == "Execution failed"
        assert result.error_details == {"error_code": 500}


class TestMockWorker:
    """Test MockWorker."""

    def test_mock_worker_execute(self):
        """Test mock worker execution."""
        worker = MockWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result = worker.execute(context)
        
        assert result.success is True
        assert len(result.outputs) == 1

    def test_mock_worker_can_execute_any_step(self):
        """Test mock worker can execute any step."""
        worker = MockWorker()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        can_execute = worker.can_execute(step)
        
        assert can_execute is True

    def test_mock_worker_with_step_types(self):
        """Test mock worker with specific step types."""
        worker = MockWorker(step_types=["task", "capability"])
        
        task_step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        can_execute = worker.can_execute(task_step)
        
        assert can_execute is True


class TestCallbackWorker:
    """Test CallbackWorker."""

    def test_callback_worker_execute(self):
        """Test callback worker execution."""
        def callback(context: ExecutionContext) -> ExecutionResult:
            return ExecutionResult(
                step_id=context.step_id,
                success=True,
                outputs=[
                    ExecutionOutput(
                        output_id="output_001",
                        step_id=context.step_id,
                        session_id=context.session_id,
                        output_type=OutputType.ARTIFACT,
                        name="Callback Output",
                        description="Output from callback",
                    )
                ],
            )
        
        worker = CallbackWorker(callback)
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result = worker.execute(context)
        
        assert result.success is True
        assert len(result.outputs) == 1

    def test_callback_worker_can_execute_default(self):
        """Test callback worker can execute by default."""
        worker = CallbackWorker(lambda ctx: ExecutionResult(step_id=ctx.step_id, success=True))
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        can_execute = worker.can_execute(step)
        
        assert can_execute is True

    def test_callback_worker_with_can_execute_callback(self):
        """Test callback worker with can_execute callback."""
        def can_execute_callback(step: ExecutionStep) -> bool:
            return step.step_type == StepType.CAPABILITY
        
        worker = CallbackWorker(
            lambda ctx: ExecutionResult(step_id=ctx.step_id, success=True),
            can_execute_callback,
        )
        
        capability_step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Capability 1",
            description="First capability",
        )
        
        task_step = ExecutionStep(
            step_id="step_002",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        assert worker.can_execute(capability_step) is True
        assert worker.can_execute(task_step) is False


class TestBaseExecutor:
    """Test BaseExecutor."""

    def test_register_worker(self):
        """Test registering a worker."""
        executor = BaseExecutor()
        
        worker = MockWorker()
        executor.register_worker(worker)
        
        assert len(executor._workers) == 1

    def test_register_worker_for_type(self):
        """Test registering worker for specific type."""
        executor = BaseExecutor()
        
        worker = MockWorker()
        executor.register_worker_for_type("task", worker)
        
        assert "task" in executor._worker_registry
        assert len(executor._worker_registry["task"]) == 1

    def test_execute_step_with_mock_worker(self):
        """Test executing step with mock worker."""
        executor = BaseExecutor()
        
        worker = MockWorker()
        executor.register_worker(worker)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result = executor.execute_step(step, context)
        
        assert result.success is True

    def test_execute_step_without_worker(self):
        """Test executing step without registered worker."""
        executor = BaseExecutor()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result = executor.execute_step(step, context)
        
        assert result.success is False
        assert "No worker available" in result.error_message

    def test_execute_step_with_type_specific_worker(self):
        """Test executing step with type-specific worker."""
        executor = BaseExecutor()
        
        worker = MockWorker()
        executor.register_worker_for_type("task", worker)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result = executor.execute_step(step, context)
        
        assert result.success is True

    def test_execute_step_with_exception(self):
        """Test executing step that raises exception."""
        def failing_callback(context: ExecutionContext) -> ExecutionResult:
            raise ValueError("Test error")
        
        worker = CallbackWorker(failing_callback)
        executor = BaseExecutor()
        executor.register_worker(worker)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result = executor.execute_step(step, context)
        
        assert result.success is False
        assert result.error_message == "Test error"

    def test_execute_step_with_validation(self):
        """Test executing step with validation."""
        from app.execution.contracts import ValidationResult, ValidationStatus
        executor = BaseExecutor()
        
        worker = MockWorker()
        executor.register_worker(worker)
        
        def validator(result: ExecutionResult) -> ValidationResult:
            return ValidationResult(
                validation_id="validation_001",
                step_id=result.step_id,
                session_id="session_001",
                status=ValidationStatus.PASSED,
                checks_passed=1,
                checks_total=1,
            )
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        result, validation_result = executor.execute_step_with_validation(step, context, validator)
        
        assert result.success is True
        assert validation_result is not None

    def test_execute_batch(self):
        """Test executing batch of steps."""
        executor = BaseExecutor()
        
        worker = MockWorker()
        executor.register_worker(worker)
        
        step1 = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        step2 = ExecutionStep(
            step_id="step_002",
            step_type=StepType.TASK,
            name="Task 2",
            description="Second task",
        )
        
        context1 = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        context2 = ExecutionContext(
            session_id="session_001",
            step_id="step_002",
        )
        
        results = executor.execute_batch([step1, step2], [context1, context2])
        
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_execute_batch_mismatched_lengths(self):
        """Test executing batch with mismatched lengths."""
        executor = BaseExecutor()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
        )
        
        with pytest.raises(ValueError, match="Steps and contexts must have the same length"):
            executor.execute_batch([step], [context, context])
