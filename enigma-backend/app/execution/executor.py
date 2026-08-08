from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.execution.contracts import (
    ExecutionStep,
    StepState,
    ExecutionOutput,
    ValidationResult,
)


@dataclass
class ExecutionContext:
    """Context for executing a step."""
    session_id: str
    step_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    worker_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of executing a step."""
    step_id: str
    success: bool
    outputs: List[ExecutionOutput] = field(default_factory=list)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Worker(ABC):
    """
    Abstract base class for workers.
    
    Workers are responsible for actual execution of steps.
    The executor orchestrates workers but does not contain execution logic.
    """

    @abstractmethod
    def execute(
        self,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute the step.
        
        Args:
            context: Execution context with inputs and metadata
            
        Returns:
            ExecutionResult with outputs and status
        """
        ...

    @abstractmethod
    def can_execute(self, step: ExecutionStep) -> bool:
        """
        Check if this worker can execute the given step.
        
        Args:
            step: The step to execute
            
        Returns:
            True if this worker can execute the step
        """
        ...


class BaseExecutor:
    """
    Base implementation of Execution Executor.
    
    This executor orchestrates worker execution without containing
    any domain-specific execution logic. It delegates to registered workers.
    """

    def __init__(self) -> None:
        self._workers: List[Worker] = []
        self._worker_registry: Dict[str, List[Worker]] = {}  # step_type -> workers

    def register_worker(self, worker: Worker) -> None:
        """Register a worker for execution."""
        self._workers.append(worker)

    def register_worker_for_type(
        self,
        step_type: str,
        worker: Worker,
    ) -> None:
        """Register a worker for a specific step type."""
        if step_type not in self._worker_registry:
            self._worker_registry[step_type] = []
        self._worker_registry[step_type].append(worker)

    def execute_step(
        self,
        step: ExecutionStep,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute a single step.
        
        Args:
            step: The step to execute
            context: Execution context
            
        Returns:
            ExecutionResult with outputs and status
        """
        start_time = datetime.utcnow()
        
        # Find appropriate worker
        worker = self._find_worker(step)
        
        if not worker:
            return ExecutionResult(
                step_id=step.step_id,
                success=False,
                error_message=f"No worker available for step type: {step.step_type}",
                execution_time_seconds=0.0,
            )
        
        # Execute step
        try:
            result = worker.execute(context)
            result.execution_time_seconds = (datetime.utcnow() - start_time).total_seconds()
            return result
        except Exception as e:
            return ExecutionResult(
                step_id=step.step_id,
                success=False,
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                execution_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

    def execute_step_with_validation(
        self,
        step: ExecutionStep,
        context: ExecutionContext,
        validator: Optional[Callable[[ExecutionResult], ValidationResult]] = None,
    ) -> tuple[ExecutionResult, Optional[ValidationResult]]:
        """
        Execute a step with optional validation.
        
        Args:
            step: The step to execute
            context: Execution context
            validator: Optional validation function
            
        Returns:
            Tuple of (execution_result, validation_result)
        """
        result = self.execute_step(step, context)
        
        validation_result = None
        if validator and result.success:
            try:
                validation_result = validator(result)
            except Exception as e:
                # Validation failure should not fail execution
                validation_result = ValidationResult(
                    validation_id=f"validation_{step.step_id}",
                    step_id=step.step_id,
                    session_id=context.session_id,
                    status="warning",  # Use string to avoid enum issues
                    validation_errors=[f"Validation error: {str(e)}"],
                )
        
        return result, validation_result

    def execute_batch(
        self,
        steps: List[ExecutionStep],
        contexts: List[ExecutionContext],
    ) -> List[ExecutionResult]:
        """
        Execute multiple steps in batch.
        
        Args:
            steps: List of steps to execute
            contexts: List of execution contexts (must match steps length)
            
        Returns:
            List of execution results
        """
        if len(steps) != len(contexts):
            raise ValueError("Steps and contexts must have the same length")
        
        results = []
        for step, context in zip(steps, contexts):
            result = self.execute_step(step, context)
            results.append(result)
        
        return results

    def _find_worker(self, step: ExecutionStep) -> Optional[Worker]:
        """Find a worker that can execute the given step."""
        # First try type-specific workers
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        type_workers = self._worker_registry.get(step_type_str, [])
        
        for worker in type_workers:
            if worker.can_execute(step):
                return worker
        
        # Then try general workers
        for worker in self._workers:
            if worker.can_execute(step):
                return worker
        
        return None


class MockWorker(Worker):
    """
    Mock worker for testing purposes.
    
    This worker simulates execution without actual work.
    """

    def __init__(self, step_types: Optional[List[str]] = None) -> None:
        self._step_types = step_types or []

    def execute(
        self,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Simulate execution."""
        return ExecutionResult(
            step_id=context.step_id,
            success=True,
            outputs=[
                ExecutionOutput(
                    output_id=f"output_{context.step_id}",
                    step_id=context.step_id,
                    session_id=context.session_id,
                    output_type="artifact",
                    name="Mock Output",
                    description="Mock output from mock worker",
                    content={"mock": True},
                    content_type="json",
                )
            ],
            execution_time_seconds=0.1,
        )

    def can_execute(self, step: ExecutionStep) -> bool:
        """Check if can execute."""
        if not self._step_types:
            return True  # Can execute any step type
        
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        return step_type_str in self._step_types


class CallbackWorker(Worker):
    """
    Worker that uses a callback function for execution.
    
    This allows custom execution logic to be injected without
    creating a full worker class.
    """

    def __init__(
        self,
        execute_callback: Callable[[ExecutionContext], ExecutionResult],
        can_execute_callback: Optional[Callable[[ExecutionStep], bool]] = None,
    ) -> None:
        self._execute_callback = execute_callback
        self._can_execute_callback = can_execute_callback

    def execute(
        self,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute using callback."""
        return self._execute_callback(context)

    def can_execute(self, step: ExecutionStep) -> bool:
        """Check if can execute using callback."""
        if self._can_execute_callback:
            return self._can_execute_callback(step)
        return True


# Default executor instance
default_executor = BaseExecutor()
