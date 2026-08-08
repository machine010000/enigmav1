"""
Tests for Execution Framework contracts.

Tests dataclass definitions, enums, and protocol contracts.
"""

import pytest
from datetime import datetime

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
)


class TestSessionState:
    """Test SessionState enum."""

    def test_session_state_values(self):
        """Test session state enum values."""
        assert SessionState.INITIALIZED.value == "initialized"
        assert SessionState.PLANNING.value == "planning"
        assert SessionState.EXECUTING.value == "executing"
        assert SessionState.COMPLETED.value == "completed"
        assert SessionState.FAILED.value == "failed"


class TestSessionPriority:
    """Test SessionPriority enum."""

    def test_session_priority_values(self):
        """Test session priority enum values."""
        assert SessionPriority.LOW.value == "low"
        assert SessionPriority.MEDIUM.value == "medium"
        assert SessionPriority.HIGH.value == "high"
        assert SessionPriority.CRITICAL.value == "critical"


class TestExecutionSession:
    """Test ExecutionSession dataclass."""

    def test_create_execution_session(self):
        """Test creating an execution session."""
        session = ExecutionSession(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        
        assert session.session_id == "session_001"
        assert session.session_state == SessionState.INITIALIZED
        assert session.priority == SessionPriority.MEDIUM

    def test_execution_session_with_custom_state(self):
        """Test execution session with custom state."""
        session = ExecutionSession(
            session_id="session_002",
            work_specification_id="work_spec_002",
            decision_id="decision_002",
            domain_id="seo",
            session_state=SessionState.EXECUTING,
            priority=SessionPriority.HIGH,
        )
        
        assert session.session_state == SessionState.EXECUTING
        assert session.priority == SessionPriority.HIGH


class TestSessionProgress:
    """Test SessionProgress dataclass."""

    def test_create_session_progress(self):
        """Test creating session progress."""
        progress = SessionProgress(
            session_id="session_001",
            current_state=SessionState.EXECUTING,
            progress_percentage=0.5,
            capabilities_completed=2,
            capabilities_total=4,
        )
        
        assert progress.session_id == "session_001"
        assert progress.progress_percentage == 0.5
        assert progress.capabilities_completed == 2


class TestExecutionEvent:
    """Test ExecutionEvent dataclass."""

    def test_create_execution_event(self):
        """Test creating an execution event."""
        event = ExecutionEvent(
            event_id="event_001",
            session_id="session_001",
            event_type="state_change",
            event_name="Session Started",
            description="Execution session started",
        )
        
        assert event.event_id == "event_001"
        assert event.event_type == "state_change"
        assert event.severity == "info"


class TestExecutionCheckpoint:
    """Test ExecutionCheckpoint dataclass."""

    def test_create_execution_checkpoint(self):
        """Test creating an execution checkpoint."""
        checkpoint = ExecutionCheckpoint(
            checkpoint_id="checkpoint_001",
            session_id="session_001",
            checkpoint_name="Milestone 1",
            description="First milestone",
            checkpoint_type="milestone",
        )
        
        assert checkpoint.checkpoint_id == "checkpoint_001"
        assert checkpoint.achieved is False
        assert checkpoint.requires_approval is False


class TestExecutionHistory:
    """Test ExecutionHistory dataclass."""

    def test_create_execution_history(self):
        """Test creating execution history."""
        history = ExecutionHistory(
            history_id="history_001",
            session_id="session_001",
        )
        
        assert history.history_id == "history_001"
        assert len(history.events) == 0
        assert len(history.checkpoints) == 0


class TestExecutionArtifact:
    """Test ExecutionArtifact dataclass."""

    def test_create_execution_artifact(self):
        """Test creating an execution artifact."""
        artifact = ExecutionArtifact(
            artifact_id="artifact_001",
            session_id="session_001",
            artifact_type="report",
            name="Audit Report",
            description="SEO audit report",
            content_type="pdf",
        )
        
        assert artifact.artifact_id == "artifact_001"
        assert artifact.artifact_type == "report"
        assert artifact.content_type == "pdf"


class TestExecutionReflection:
    """Test ExecutionReflection dataclass."""

    def test_create_execution_reflection(self):
        """Test creating an execution reflection."""
        reflection = ExecutionReflection(
            reflection_id="reflection_001",
            session_id="session_001",
            reflection_type="overall",
            subject="Execution completed successfully",
        )
        
        assert reflection.reflection_id == "reflection_001"
        assert reflection.reflection_type == "overall"
        assert len(reflection.what_went_well) == 0


class TestExecutionSummary:
    """Test ExecutionSummary dataclass."""

    def test_create_execution_summary(self):
        """Test creating an execution summary."""
        summary = ExecutionSummary(
            summary_id="summary_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            final_state=SessionState.COMPLETED,
        )
        
        assert summary.summary_id == "summary_001"
        assert summary.final_state == SessionState.COMPLETED
        assert summary.success_rate == 0.0


class TestStepState:
    """Test StepState enum."""

    def test_step_state_values(self):
        """Test step state enum values."""
        assert StepState.PENDING.value == "pending"
        assert StepState.READY.value == "ready"
        assert StepState.RUNNING.value == "running"
        assert StepState.DONE.value == "done"
        assert StepState.FAILED.value == "failed"


class TestStepType:
    """Test StepType enum."""

    def test_step_type_values(self):
        """Test step type enum values."""
        assert StepType.CAPABILITY.value == "capability"
        assert StepType.TASK.value == "task"
        assert StepType.DELIVERABLE.value == "deliverable"
        assert StepType.VALIDATION.value == "validation"
        assert StepType.MILESTONE.value == "milestone"


class TestExecutionStep:
    """Test ExecutionStep dataclass."""

    def test_create_execution_step(self):
        """Test creating an execution step."""
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Execute Task",
            description="Execute the task",
        )
        
        assert step.step_id == "step_001"
        assert step.step_type == StepType.TASK
        assert step.state == StepState.PENDING

    def test_execution_step_with_dependencies(self):
        """Test execution step with dependencies."""
        step = ExecutionStep(
            step_id="step_002",
            step_type=StepType.TASK,
            name="Dependent Task",
            description="Task with dependencies",
            dependencies=["step_001"],
        )
        
        assert len(step.dependencies) == 1
        assert "step_001" in step.dependencies


class TestExecutionPlan:
    """Test ExecutionPlan dataclass."""

    def test_create_execution_plan(self):
        """Test creating an execution plan."""
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
        )
        
        assert plan.plan_id == "plan_001"
        assert len(plan.steps) == 0
        assert len(plan.step_order) == 0

    def test_execution_plan_with_steps(self):
        """Test execution plan with steps."""
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
            plan_id="plan_002",
            session_id="session_002",
            work_specification_id="work_spec_002",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
            quality_gates=["step_002"],
            milestones=["step_001"],
        )
        
        assert len(plan.steps) == 2
        assert len(plan.quality_gates) == 1
        assert len(plan.milestones) == 1


class TestValidationStatus:
    """Test ValidationStatus enum."""

    def test_validation_status_values(self):
        """Test validation status enum values."""
        assert ValidationStatus.PENDING.value == "pending"
        assert ValidationStatus.PASSED.value == "passed"
        assert ValidationStatus.FAILED.value == "failed"
        assert ValidationStatus.WARNING.value == "warning"


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_create_validation_result(self):
        """Test creating a validation result."""
        result = ValidationResult(
            validation_id="validation_001",
            step_id="step_001",
            session_id="session_001",
            status=ValidationStatus.PASSED,
            checks_passed=5,
            checks_total=5,
        )
        
        assert result.validation_id == "validation_001"
        assert result.status == ValidationStatus.PASSED
        assert result.checks_passed == 5


class TestOutputType:
    """Test OutputType enum."""

    def test_output_type_values(self):
        """Test output type enum values."""
        assert OutputType.EVIDENCE.value == "evidence"
        assert OutputType.ARTIFACT.value == "artifact"
        assert OutputType.REPORT.value == "report"
        assert OutputType.METRIC.value == "metric"


class TestExecutionOutput:
    """Test ExecutionOutput dataclass."""

    def test_create_execution_output(self):
        """Test creating an execution output."""
        output = ExecutionOutput(
            output_id="output_001",
            step_id="step_001",
            session_id="session_001",
            output_type=OutputType.ARTIFACT,
            name="Output 1",
            description="First output",
            content={"data": "value"},
        )
        
        assert output.output_id == "output_001"
        assert output.output_type == OutputType.ARTIFACT
        assert output.content == {"data": "value"}


class TestQualityGate:
    """Test QualityGate dataclass."""

    def test_create_quality_gate(self):
        """Test creating a quality gate."""
        gate = QualityGate(
            gate_id="gate_001",
            step_id="step_001",
            gate_name="Quality Check",
            description="Quality gate for step",
            criteria=["criterion_1", "criterion_2"],
            threshold=0.8,
            required=True,
        )
        
        assert gate.gate_id == "gate_001"
        assert len(gate.criteria) == 2
        assert gate.threshold == 0.8
        assert gate.required is True
