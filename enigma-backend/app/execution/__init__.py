from __future__ import annotations

from app.execution.contracts import (
    SessionState,
    SessionPriority,
    ExecutionSession,
    SessionProgress,
    ExecutionEvent,
    ExecutionCheckpoint,
    ExecutionHistory,
    ExecutionArtifact,
    ExecutionReflection,
    ExecutionSummary,
    StepState,
    StepType,
    ValidationStatus,
    OutputType,
    ExecutionStep,
    ExecutionPlan,
    ValidationResult,
    ExecutionOutput,
    QualityGate,
    ExecutionPlanner,
    ExecutionScheduler,
    ExecutionValidator,
    OutputBuilder,
    ReflectionGenerator,
)

from app.execution.runtime import ExecutionRuntime, execution_runtime
from app.execution.planner import BaseExecutionPlanner, TemplateBasedPlanner, default_planner
from app.execution.scheduler import BaseExecutionScheduler, PriorityExecutionScheduler, default_scheduler
from app.execution.executor import BaseExecutor, MockWorker, CallbackWorker, default_executor
from app.execution.validation import BaseValidator, RuleBasedValidator, CallbackValidator, default_validator
from app.execution.outputs import BaseOutputBuilder, EvidenceOutputBuilder, ReportOutputBuilder, MetricOutputBuilder, default_output_builder
from app.execution.reflection import BaseReflectionGenerator, StepReflectionGenerator, CallbackReflectionGenerator, default_reflection_generator
from app.execution.registry import ExecutionRegistry, execution_registry

__all__ = [
    # Session
    "SessionState",
    "SessionPriority",
    "ExecutionSession",
    "SessionProgress",
    # Execution
    "ExecutionEvent",
    "ExecutionCheckpoint",
    "ExecutionHistory",
    "ExecutionArtifact",
    "ExecutionReflection",
    "ExecutionSummary",
    # Step
    "StepState",
    "StepType",
    "ExecutionStep",
    "ExecutionPlan",
    # Validation
    "ValidationStatus",
    "ValidationResult",
    "QualityGate",
    # Output
    "OutputType",
    "ExecutionOutput",
    # Protocols
    "ExecutionPlanner",
    "ExecutionScheduler",
    "ExecutionValidator",
    "OutputBuilder",
    "ReflectionGenerator",
    # Runtime
    "ExecutionRuntime",
    "execution_runtime",
    # Planner
    "BaseExecutionPlanner",
    "TemplateBasedPlanner",
    "default_planner",
    # Scheduler
    "BaseExecutionScheduler",
    "PriorityExecutionScheduler",
    "default_scheduler",
    # Executor
    "BaseExecutor",
    "MockWorker",
    "CallbackWorker",
    "default_executor",
    # Validation
    "BaseValidator",
    "RuleBasedValidator",
    "CallbackValidator",
    "default_validator",
    # Outputs
    "BaseOutputBuilder",
    "EvidenceOutputBuilder",
    "ReportOutputBuilder",
    "MetricOutputBuilder",
    "default_output_builder",
    # Reflection
    "BaseReflectionGenerator",
    "StepReflectionGenerator",
    "CallbackReflectionGenerator",
    "default_reflection_generator",
    # Registry
    "ExecutionRegistry",
    "execution_registry",
]
