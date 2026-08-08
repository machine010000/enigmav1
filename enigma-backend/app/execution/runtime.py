from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.execution.contracts import (
    ExecutionSession,
    SessionState,
    SessionPriority,
    SessionProgress,
    ExecutionEvent,
    ExecutionCheckpoint,
    ExecutionHistory,
    ExecutionArtifact,
    ExecutionReflection,
    ExecutionSummary,
    ExecutionPlan,
    ExecutionStep,
    StepState,
)


class ExecutionRuntime:
    """Runtime for managing execution sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, ExecutionSession] = {}
        self._progress: Dict[str, SessionProgress] = {}
        self._events: Dict[str, ExecutionEvent] = {}
        self._checkpoints: Dict[str, ExecutionCheckpoint] = {}
        self._histories: Dict[str, ExecutionHistory] = {}
        self._artifacts: Dict[str, ExecutionArtifact] = {}
        self._reflections: Dict[str, ExecutionReflection] = {}
        self._summaries: Dict[str, ExecutionSummary] = {}
        self._plans: Dict[str, ExecutionPlan] = {}
        self._step_states: Dict[str, Dict[str, StepState]] = {}  # session_id -> step_id -> state

    # Session Management
    def create_session(
        self,
        session_id: str,
        work_specification_id: str,
        decision_id: str,
        domain_id: str,
        priority: SessionPriority = SessionPriority.MEDIUM,
    ) -> ExecutionSession:
        """Create a new execution session."""
        session = ExecutionSession(
            session_id=session_id,
            work_specification_id=work_specification_id,
            decision_id=decision_id,
            domain_id=domain_id,
            priority=priority,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ExecutionSession]:
        """Get an execution session by ID."""
        return self._sessions.get(session_id)

    def update_session_state(
        self,
        session_id: str,
        new_state: SessionState,
    ) -> bool:
        """Update the state of a session."""
        if session_id not in self._sessions:
            return False
        old_session = self._sessions[session_id]
        updated_session = ExecutionSession(
            session_id=old_session.session_id,
            work_specification_id=old_session.work_specification_id,
            decision_id=old_session.decision_id,
            domain_id=old_session.domain_id,
            session_state=new_state,
            priority=old_session.priority,
            started_at=old_session.started_at,
            ended_at=old_session.ended_at if new_state in [SessionState.COMPLETED, SessionState.FAILED, SessionState.CANCELLED] else datetime.utcnow(),
            estimated_duration=old_session.estimated_duration,
            actual_duration=old_session.actual_duration,
            owner=old_session.owner,
            metadata=old_session.metadata,
        )
        self._sessions[session_id] = updated_session
        return True

    def list_sessions(self) -> List[ExecutionSession]:
        """List all execution sessions."""
        return list(self._sessions.values())

    def get_sessions_by_state(self, state: SessionState) -> List[ExecutionSession]:
        """Get sessions by state."""
        return [s for s in self._sessions.values() if s.session_state == state]

    # Progress Management
    def update_progress(
        self,
        session_id: str,
        progress: SessionProgress,
    ) -> bool:
        """Update progress for a session."""
        self._progress[session_id] = progress
        return True

    def get_progress(self, session_id: str) -> Optional[SessionProgress]:
        """Get progress for a session."""
        return self._progress.get(session_id)

    # Event Management
    def record_event(self, event: ExecutionEvent) -> bool:
        """Record an execution event."""
        self._events[event.event_id] = event
        return True

    def get_events_for_session(self, session_id: str) -> List[ExecutionEvent]:
        """Get events for a session."""
        return [e for e in self._events.values() if e.session_id == session_id]

    # Checkpoint Management
    def create_checkpoint(self, checkpoint: ExecutionCheckpoint) -> bool:
        """Create an execution checkpoint."""
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint
        return True

    def get_checkpoint(self, checkpoint_id: str) -> Optional[ExecutionCheckpoint]:
        """Get a checkpoint by ID."""
        return self._checkpoints.get(checkpoint_id)

    def get_checkpoints_for_session(self, session_id: str) -> List[ExecutionCheckpoint]:
        """Get checkpoints for a session."""
        return [c for c in self._checkpoints.values() if c.session_id == session_id]

    def achieve_checkpoint(
        self,
        checkpoint_id: str,
        approved_by: Optional[str] = None,
    ) -> bool:
        """Mark a checkpoint as achieved."""
        if checkpoint_id not in self._checkpoints:
            return False
        old_checkpoint = self._checkpoints[checkpoint_id]
        updated_checkpoint = ExecutionCheckpoint(
            checkpoint_id=old_checkpoint.checkpoint_id,
            session_id=old_checkpoint.session_id,
            checkpoint_name=old_checkpoint.checkpoint_name,
            description=old_checkpoint.description,
            checkpoint_type=old_checkpoint.checkpoint_type,
            achieved=True,
            achieved_at=datetime.utcnow(),
            expected_at=old_checkpoint.expected_at,
            requires_approval=old_checkpoint.requires_approval,
            approved_by=approved_by if old_checkpoint.requires_approval else old_checkpoint.approved_by,
            approved_at=datetime.utcnow() if approved_by else old_checkpoint.approved_at,
            notes=old_checkpoint.notes,
            metadata=old_checkpoint.metadata,
        )
        self._checkpoints[checkpoint_id] = updated_checkpoint
        return True

    # History Management
    def get_history(self, session_id: str) -> Optional[ExecutionHistory]:
        """Get history for a session."""
        return self._histories.get(session_id)

    def create_history(self, history: ExecutionHistory) -> bool:
        """Create history for a session."""
        self._histories[history.history_id] = history
        return True

    # Artifact Management
    def create_artifact(self, artifact: ExecutionArtifact) -> bool:
        """Create an execution artifact."""
        self._artifacts[artifact.artifact_id] = artifact
        return True

    def get_artifact(self, artifact_id: str) -> Optional[ExecutionArtifact]:
        """Get an artifact by ID."""
        return self._artifacts.get(artifact_id)

    def get_artifacts_for_session(self, session_id: str) -> List[ExecutionArtifact]:
        """Get artifacts for a session."""
        return [a for a in self._artifacts.values() if a.session_id == session_id]

    # Reflection Management
    def create_reflection(self, reflection: ExecutionReflection) -> bool:
        """Create an execution reflection."""
        self._reflections[reflection.reflection_id] = reflection
        return True

    def get_reflection(self, reflection_id: str) -> Optional[ExecutionReflection]:
        """Get a reflection by ID."""
        return self._reflections.get(reflection_id)

    def get_reflections_for_session(self, session_id: str) -> List[ExecutionReflection]:
        """Get reflections for a session."""
        return [r for r in self._reflections.values() if r.session_id == session_id]

    # Summary Management
    def create_summary(self, summary: ExecutionSummary) -> bool:
        """Create an execution summary."""
        self._summaries[summary.summary_id] = summary
        return True

    def get_summary(self, summary_id: str) -> Optional[ExecutionSummary]:
        """Get a summary by ID."""
        return self._summaries.get(summary_id)

    def get_summary_for_session(self, session_id: str) -> Optional[ExecutionSummary]:
        """Get summary for a session."""
        for summary in self._summaries.values():
            if summary.session_id == session_id:
                return summary
        return None

    # Lifecycle
    def complete_session(
        self,
        session_id: str,
        final_state: SessionState,
        completed_by: Optional[str] = None,
    ) -> bool:
        """Complete an execution session."""
        if session_id not in self._sessions:
            return False
        old_session = self._sessions[session_id]
        updated_session = ExecutionSession(
            session_id=old_session.session_id,
            work_specification_id=old_session.work_specification_id,
            decision_id=old_session.decision_id,
            domain_id=old_session.domain_id,
            session_state=final_state,
            priority=old_session.priority,
            started_at=old_session.started_at,
            ended_at=datetime.utcnow(),
            estimated_duration=old_session.estimated_duration,
            actual_duration=str(datetime.utcnow() - old_session.started_at),
            owner=completed_by or old_session.owner,
            metadata=old_session.metadata,
        )
        self._sessions[session_id] = updated_session
        return True

    def cancel_session(self, session_id: str) -> bool:
        """Cancel an execution session."""
        if session_id not in self._sessions:
            return False
        old_session = self._sessions[session_id]
        updated_session = ExecutionSession(
            session_id=old_session.session_id,
            work_specification_id=old_session.work_specification_id,
            decision_id=old_session.decision_id,
            domain_id=old_session.domain_id,
            session_state=SessionState.CANCELLED,
            priority=old_session.priority,
            started_at=old_session.started_at,
            ended_at=datetime.utcnow(),
            estimated_duration=old_session.estimated_duration,
            actual_duration=str(datetime.utcnow() - old_session.started_at),
            owner=old_session.owner,
            metadata=old_session.metadata,
        )
        self._sessions[session_id] = updated_session
        return True

    # Plan Management
    def register_plan(self, plan: ExecutionPlan) -> bool:
        """Register an execution plan for a session."""
        self._plans[plan.session_id] = plan
        # Initialize step states
        self._step_states[plan.session_id] = {
            step.step_id: step.state for step in plan.steps
        }
        return True

    def get_plan(self, session_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan for a session."""
        return self._plans.get(session_id)

    def update_step_state(
        self,
        session_id: str,
        step_id: str,
        new_state: StepState,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update state of a specific step."""
        if session_id not in self._step_states:
            return False
        if step_id not in self._step_states[session_id]:
            return False
        
        self._step_states[session_id][step_id] = new_state
        
        # Update the step in the plan
        plan = self._plans.get(session_id)
        if plan:
            updated_steps = []
            for step in plan.steps:
                if step.step_id == step_id:
                    updated_step = ExecutionStep(
                        step_id=step.step_id,
                        step_type=step.step_type,
                        name=step.name,
                        description=step.description,
                        state=new_state,
                        dependencies=step.dependencies,
                        required_capabilities=step.required_capabilities,
                        inputs=step.inputs,
                        expected_outputs=step.expected_outputs,
                        estimated_duration=step.estimated_duration,
                        retry_count=step.retry_count + 1 if new_state == StepState.RETRY else step.retry_count,
                        max_retries=step.max_retries,
                        started_at=step.started_at if new_state != StepState.RUNNING else datetime.utcnow(),
                        completed_at=step.completed_at if new_state not in [StepState.DONE, StepState.FAILED, StepState.SKIPPED] else datetime.utcnow(),
                        error_message=error_message or step.error_message,
                        metadata=step.metadata,
                    )
                    updated_steps.append(updated_step)
                else:
                    updated_steps.append(step)
            
            self._plans[session_id] = ExecutionPlan(
                plan_id=plan.plan_id,
                session_id=plan.session_id,
                work_specification_id=plan.work_specification_id,
                domain_id=plan.domain_id,
                steps=updated_steps,
                step_order=plan.step_order,
                quality_gates=plan.quality_gates,
                milestones=plan.milestones,
                created_at=plan.created_at,
                metadata=plan.metadata,
            )
        
        return True

    def get_step_state(
        self,
        session_id: str,
        step_id: str,
    ) -> Optional[StepState]:
        """Get state of a specific step."""
        if session_id not in self._step_states:
            return None
        return self._step_states[session_id].get(step_id)

    def get_all_step_states(self, session_id: str) -> Dict[str, StepState]:
        """Get all step states for a session."""
        return self._step_states.get(session_id, {})

    def get_step_by_id(
        self,
        session_id: str,
        step_id: str,
    ) -> Optional[ExecutionStep]:
        """Get a step by ID."""
        plan = self._plans.get(session_id)
        if not plan:
            return None
        for step in plan.steps:
            if step.step_id == step_id:
                return step
        return None


# Global execution runtime instance
execution_runtime = ExecutionRuntime()
