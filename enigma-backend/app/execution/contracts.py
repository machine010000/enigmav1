from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class SessionState(str, Enum):
    """States for execution sessions."""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    CAPABILITY_SELECTION = "capability_selection"
    TASK_GRAPH = "task_graph"
    EXECUTING = "executing"
    DELIVERING = "delivering"
    REVIEWING = "reviewing"
    REFLECTING = "reflecting"
    LEARNING = "learning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class SessionPriority(str, Enum):
    """Priority levels for execution sessions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepState(str, Enum):
    """States for execution steps."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    FAILED = "failed"
    RETRY = "retry"
    DONE = "done"
    SKIPPED = "skipped"


class StepType(str, Enum):
    """Types of execution steps."""
    CAPABILITY = "capability"
    TASK = "task"
    DELIVERABLE = "deliverable"
    VALIDATION = "validation"
    MILESTONE = "milestone"


class ValidationStatus(str, Enum):
    """Status of validation results."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class OutputType(str, Enum):
    """Types of execution outputs."""
    EVIDENCE = "evidence"
    ARTIFACT = "artifact"
    REPORT = "report"
    METRIC = "metric"
    FILE = "file"
    RECOMMENDATION = "recommendation"
    CONFIGURATION = "configuration"


@dataclass(frozen=True)
class ExecutionSession:
    """A task-specific execution session."""
    session_id: str
    work_specification_id: str
    decision_id: str
    domain_id: str
    session_state: SessionState = SessionState.INITIALIZED
    priority: SessionPriority = SessionPriority.MEDIUM
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    owner: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SessionProgress:
    """Progress tracking for an execution session."""
    session_id: str
    current_state: SessionState
    progress_percentage: float = 0.0  # 0.0 to 1.0
    capabilities_completed: int = 0
    capabilities_total: int = 0
    tasks_completed: int = 0
    tasks_total: int = 0
    deliverables_completed: int = 0
    deliverables_total: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionEvent:
    """An event during execution."""
    event_id: str
    session_id: str
    event_type: str  # state_change, capability_started, capability_completed, task_started, task_completed, deliverable_created, review_started, review_completed, error, warning
    event_name: str
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None  # system, user, automation
    severity: str = "info"  # info, warning, error, critical
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionCheckpoint:
    """A checkpoint during execution."""
    checkpoint_id: str
    session_id: str
    checkpoint_name: str
    description: str
    checkpoint_type: str  # milestone, capability, task, deliverable, review
    achieved: bool = False
    achieved_at: Optional[datetime] = None
    expected_at: Optional[datetime] = None
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionHistory:
    """History of execution for a session."""
    history_id: str
    session_id: str
    events: List[ExecutionEvent] = field(default_factory=list)
    checkpoints: List[ExecutionCheckpoint] = field(default_factory=list)
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionArtifact:
    """An artifact produced during execution."""
    artifact_id: str
    session_id: str
    artifact_type: str  # evidence, deliverable, report, data, configuration, code, document
    name: str
    description: str
    content_type: str  # text, json, csv, pdf, html, etc.
    location: Optional[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionReflection:
    """Reflection on execution."""
    reflection_id: str
    session_id: str
    reflection_type: str  # capability, task, deliverable, overall
    subject: str
    what_went_well: List[str] = field(default_factory=list)
    what_could_be_improved: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    reflected_at: datetime = field(default_factory=datetime.utcnow)
    reflected_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionSummary:
    """Summary of execution."""
    summary_id: str
    session_id: str
    work_specification_id: str
    decision_id: str
    final_state: SessionState
    total_duration: Optional[str] = None
    total_events: int = 0
    total_checkpoints: int = 0
    total_artifacts: int = 0
    total_reflections: int = 0
    success_rate: float = 0.0  # 0.0 to 1.0
    quality_score: float = 0.0  # 0.0 to 1.0
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    highlights: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# New contracts for Execution Framework


@dataclass(frozen=True)
class ExecutionStep:
    """A single step in an execution plan."""
    step_id: str
    step_type: StepType
    name: str
    description: str
    state: StepState = StepState.PENDING
    dependencies: List[str] = field(default_factory=list)  # step_ids this step depends on
    required_capabilities: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected_outputs: List[str] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionPlan:
    """A complete execution plan."""
    plan_id: str
    session_id: str
    work_specification_id: str
    domain_id: str
    steps: List[ExecutionStep] = field(default_factory=list)
    step_order: List[str] = field(default_factory=list)  # ordered step_ids
    quality_gates: List[str] = field(default_factory=list)  # step_ids that are quality gates
    milestones: List[str] = field(default_factory=list)  # step_ids that are milestones
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating an execution step."""
    validation_id: str
    step_id: str
    session_id: str
    status: ValidationStatus
    checks_passed: int = 0
    checks_total: int = 0
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)
    validated_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionOutput:
    """An output produced during execution."""
    output_id: str
    step_id: str
    session_id: str
    output_type: OutputType
    name: str
    description: str
    content: Any = None
    content_type: str = "text"
    size: Optional[int] = None
    location: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityGate:
    """A quality gate for validation."""
    gate_id: str
    step_id: str
    gate_name: str
    description: str
    criteria: List[str] = field(default_factory=list)
    threshold: Optional[float] = None
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# Protocol contracts for extensibility


class ExecutionPlanner(Protocol):
    """Protocol for execution planners."""
    
    def create_plan(
        self,
        work_specification_id: str,
        domain_id: str,
        session_id: str,
        context: Dict[str, Any],
    ) -> ExecutionPlan:
        """Create an execution plan from work specification."""
        ...


class ExecutionScheduler(Protocol):
    """Protocol for execution schedulers."""
    
    def get_next_step(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> Optional[ExecutionStep]:
        """Get the next step to execute."""
        ...


class ExecutionValidator(Protocol):
    """Protocol for execution validators."""
    
    def validate_step(
        self,
        step: ExecutionStep,
        outputs: List[ExecutionOutput],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate an execution step."""
        ...


class OutputBuilder(Protocol):
    """Protocol for output builders."""
    
    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build outputs from execution result."""
        ...


class ReflectionGenerator(Protocol):
    """Protocol for reflection generators."""
    
    def generate_reflection(
        self,
        session_id: str,
        plan: ExecutionPlan,
        execution_results: Dict[str, Any],
    ) -> ExecutionReflection:
        """Generate reflection from execution results."""
        ...
