"""
Tests for Execution Runtime module.

Tests session management, plan management, and step state tracking.
"""

import pytest

from app.execution.contracts import (
    ExecutionSession,
    SessionState,
    SessionPriority,
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
)
from app.execution.runtime import ExecutionRuntime, execution_runtime


class TestExecutionRuntime:
    """Test ExecutionRuntime."""

    def test_create_session(self):
        """Test creating an execution session."""
        runtime = ExecutionRuntime()
        
        session = runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
            priority=SessionPriority.HIGH,
        )
        
        assert session.session_id == "session_001"
        assert session.session_state == SessionState.INITIALIZED
        assert session.priority == SessionPriority.HIGH

    def test_get_session(self):
        """Test getting a session."""
        runtime = ExecutionRuntime()
        
        runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        
        session = runtime.get_session("session_001")
        
        assert session is not None
        assert session.session_id == "session_001"

    def test_update_session_state(self):
        """Test updating session state."""
        runtime = ExecutionRuntime()
        
        runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        
        success = runtime.update_session_state("session_001", SessionState.EXECUTING)
        
        assert success is True
        
        session = runtime.get_session("session_001")
        assert session.session_state == SessionState.EXECUTING

    def test_list_sessions(self):
        """Test listing all sessions."""
        runtime = ExecutionRuntime()
        
        runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        runtime.create_session(
            session_id="session_002",
            work_specification_id="work_spec_002",
            decision_id="decision_002",
            domain_id="seo",
        )
        
        sessions = runtime.list_sessions()
        
        assert len(sessions) == 2

    def test_get_sessions_by_state(self):
        """Test getting sessions by state."""
        runtime = ExecutionRuntime()
        
        runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        runtime.update_session_state("session_001", SessionState.EXECUTING)
        
        runtime.create_session(
            session_id="session_002",
            work_specification_id="work_spec_002",
            decision_id="decision_002",
            domain_id="seo",
        )
        
        executing_sessions = runtime.get_sessions_by_state(SessionState.EXECUTING)
        
        assert len(executing_sessions) == 1
        assert executing_sessions[0].session_id == "session_001"

    def test_register_plan(self):
        """Test registering an execution plan."""
        runtime = ExecutionRuntime()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step],
            step_order=["step_001"],
        )
        
        success = runtime.register_plan(plan)
        
        assert success is True
        assert runtime.get_plan("session_001") is not None

    def test_get_plan(self):
        """Test getting a plan."""
        runtime = ExecutionRuntime()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step],
            step_order=["step_001"],
        )
        
        runtime.register_plan(plan)
        
        retrieved_plan = runtime.get_plan("session_001")
        
        assert retrieved_plan is not None
        assert retrieved_plan.plan_id == "plan_001"

    def test_update_step_state(self):
        """Test updating step state."""
        runtime = ExecutionRuntime()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step],
            step_order=["step_001"],
        )
        
        runtime.register_plan(plan)
        
        success = runtime.update_step_state("session_001", "step_001", StepState.RUNNING)
        
        assert success is True
        
        step_state = runtime.get_step_state("session_001", "step_001")
        assert step_state == StepState.RUNNING

    def test_get_step_state(self):
        """Test getting step state."""
        runtime = ExecutionRuntime()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step],
            step_order=["step_001"],
        )
        
        runtime.register_plan(plan)
        
        step_state = runtime.get_step_state("session_001", "step_001")
        
        assert step_state == StepState.PENDING

    def test_get_all_step_states(self):
        """Test getting all step states."""
        runtime = ExecutionRuntime()
        
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
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step1, step2],
            step_order=["step_001", "step_002"],
        )
        
        runtime.register_plan(plan)
        
        step_states = runtime.get_all_step_states("session_001")
        
        assert len(step_states) == 2
        assert "step_001" in step_states
        assert "step_002" in step_states

    def test_get_step_by_id(self):
        """Test getting a step by ID."""
        runtime = ExecutionRuntime()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        plan = ExecutionPlan(
            plan_id="plan_001",
            session_id="session_001",
            work_specification_id="work_spec_001",
            domain_id="seo",
            steps=[step],
            step_order=["step_001"],
        )
        
        runtime.register_plan(plan)
        
        retrieved_step = runtime.get_step_by_id("session_001", "step_001")
        
        assert retrieved_step is not None
        assert retrieved_step.step_id == "step_001"

    def test_complete_session(self):
        """Test completing a session."""
        runtime = ExecutionRuntime()
        
        runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        
        success = runtime.complete_session("session_001", SessionState.COMPLETED)
        
        assert success is True
        
        session = runtime.get_session("session_001")
        assert session.session_state == SessionState.COMPLETED
        assert session.ended_at is not None

    def test_cancel_session(self):
        """Test cancelling a session."""
        runtime = ExecutionRuntime()
        
        runtime.create_session(
            session_id="session_001",
            work_specification_id="work_spec_001",
            decision_id="decision_001",
            domain_id="seo",
        )
        
        success = runtime.cancel_session("session_001")
        
        assert success is True
        
        session = runtime.get_session("session_001")
        assert session.session_state == SessionState.CANCELLED

    def test_update_progress(self):
        """Test updating progress."""
        runtime = ExecutionRuntime()
        
        from app.execution.contracts import SessionProgress
        
        progress = SessionProgress(
            session_id="session_001",
            current_state=SessionState.EXECUTING,
            progress_percentage=0.5,
            capabilities_completed=2,
            capabilities_total=4,
        )
        
        success = runtime.update_progress("session_001", progress)
        
        assert success is True
        
        retrieved_progress = runtime.get_progress("session_001")
        assert retrieved_progress is not None
        assert retrieved_progress.progress_percentage == 0.5

    def test_record_event(self):
        """Test recording an event."""
        runtime = ExecutionRuntime()
        
        from app.execution.contracts import ExecutionEvent
        
        event = ExecutionEvent(
            event_id="event_001",
            session_id="session_001",
            event_type="state_change",
            event_name="State Changed",
            description="Session state changed",
        )
        
        success = runtime.record_event(event)
        
        assert success is True

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        runtime = ExecutionRuntime()
        
        from app.execution.contracts import ExecutionCheckpoint
        
        checkpoint = ExecutionCheckpoint(
            checkpoint_id="checkpoint_001",
            session_id="session_001",
            checkpoint_name="Milestone 1",
            description="First milestone",
            checkpoint_type="milestone",
        )
        
        success = runtime.create_checkpoint(checkpoint)
        
        assert success is True

    def test_achieve_checkpoint(self):
        """Test achieving a checkpoint."""
        runtime = ExecutionRuntime()
        
        from app.execution.contracts import ExecutionCheckpoint
        
        checkpoint = ExecutionCheckpoint(
            checkpoint_id="checkpoint_001",
            session_id="session_001",
            checkpoint_name="Milestone 1",
            description="First milestone",
            checkpoint_type="milestone",
            requires_approval=False,
        )
        
        runtime.create_checkpoint(checkpoint)
        
        success = runtime.achieve_checkpoint("checkpoint_001")
        
        assert success is True
        
        achieved_checkpoint = runtime.get_checkpoint("checkpoint_001")
        assert achieved_checkpoint.achieved is True
        assert achieved_checkpoint.achieved_at is not None


class TestGlobalRuntime:
    """Test global runtime instance."""

    def test_global_runtime_exists(self):
        """Test global runtime instance exists."""
        from app.execution import execution_runtime
        
        assert execution_runtime is not None
        assert isinstance(execution_runtime, ExecutionRuntime)
