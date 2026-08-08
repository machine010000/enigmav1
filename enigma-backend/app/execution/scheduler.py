from __future__ import annotations

from typing import Dict, List, Optional

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    ExecutionScheduler,
)


class BaseExecutionScheduler:
    """
    Base implementation of Execution Scheduler.
    
    This scheduler determines the next step to execute based on:
    - Current step states
    - Dependencies between steps
    - Retry logic
    - Step readiness
    """

    def get_next_step(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> Optional[ExecutionStep]:
        """
        Get the next step to execute.
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps (step_id -> StepState)
            
        Returns:
            The next step to execute, or None if no step is ready
        """
        # Iterate through steps in order
        for step_id in plan.step_order:
            step = self._get_step_by_id(plan, step_id)
            if not step:
                continue
            
            current_step_state = current_state.get(step_id, StepState.PENDING)
            
            # Skip completed, failed (beyond retries), or skipped steps
            if current_step_state in [StepState.DONE, StepState.SKIPPED]:
                continue
            
            # Check if step is ready to execute
            if self._is_step_ready(step, current_state):
                # Mark as ready if pending
                if current_step_state == StepState.PENDING:
                    return step
                # Return if already running or waiting
                elif current_step_state in [StepState.READY, StepState.RUNNING, StepState.WAITING]:
                    return step
                # Check if should retry
                elif current_step_state == StepState.FAILED:
                    if step.retry_count < step.max_retries:
                        return step
        
        return None

    def _get_step_by_id(
        self,
        plan: ExecutionPlan,
        step_id: str,
    ) -> Optional[ExecutionStep]:
        """Get a step by ID from the plan."""
        for step in plan.steps:
            if step.step_id == step_id:
                return step
        return None

    def _is_step_ready(
        self,
        step: ExecutionStep,
        current_state: Dict[str, StepState],
    ) -> bool:
        """
        Check if a step is ready to execute.
        
        A step is ready if:
        - All dependencies are DONE
        - Step is not already DONE
        - Step is not SKIPPED
        - If FAILED, retry count is not exceeded
        """
        # Check dependencies
        for dep_id in step.dependencies:
            dep_state = current_state.get(dep_id, StepState.PENDING)
            if dep_state != StepState.DONE:
                return False
        
        # Check if step can be executed
        step_state = current_state.get(step.step_id, StepState.PENDING)
        
        # Can execute if pending, ready, running, or waiting
        if step_state in [StepState.PENDING, StepState.READY, StepState.RUNNING, StepState.WAITING]:
            return True
        
        # Can retry if failed and retries available
        if step_state == StepState.FAILED and step.retry_count < step.max_retries:
            return True
        
        return False

    def get_ready_steps(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> List[ExecutionStep]:
        """
        Get all steps that are ready to execute.
        
        This is useful for parallel execution scenarios.
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            List of steps that are ready to execute
        """
        ready_steps = []
        
        for step in plan.steps:
            if self._is_step_ready(step, current_state):
                step_state = current_state.get(step.step_id, StepState.PENDING)
                if step_state in [StepState.PENDING, StepState.READY]:
                    ready_steps.append(step)
        
        return ready_steps

    def get_blocked_steps(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> Dict[str, List[str]]:
        """
        Get steps that are blocked and their blocking dependencies.
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            Dictionary mapping step_id to list of blocking step_ids
        """
        blocked = {}
        
        for step in plan.steps:
            step_state = current_state.get(step.step_id, StepState.PENDING)
            
            # Only check pending steps
            if step_state != StepState.PENDING:
                continue
            
            blocking_deps = []
            for dep_id in step.dependencies:
                dep_state = current_state.get(dep_id, StepState.PENDING)
                if dep_state != StepState.DONE:
                    blocking_deps.append(dep_id)
            
            if blocking_deps:
                blocked[step.step_id] = blocking_deps
        
        return blocked

    def get_failed_steps(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> List[ExecutionStep]:
        """
        Get steps that have failed and cannot be retried.
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            List of failed steps
        """
        failed_steps = []
        
        for step in plan.steps:
            step_state = current_state.get(step.step_id, StepState.PENDING)
            if step_state == StepState.FAILED and step.retry_count >= step.max_retries:
                failed_steps.append(step)
        
        return failed_steps

    def can_proceed(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> bool:
        """
        Check if execution can proceed.
        
        Execution can proceed if:
        - There are steps ready to execute
        - No critical failures
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            True if execution can proceed
        """
        # Check for critical failures
        failed_steps = self.get_failed_steps(plan, current_state)
        if failed_steps:
            # Check if any failed step is a quality gate
            for step in failed_steps:
                if step.step_id in plan.quality_gates:
                    return False
        
        # Check if there are steps ready
        ready_steps = self.get_ready_steps(plan, current_state)
        return len(ready_steps) > 0

    def is_execution_complete(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> bool:
        """
        Check if execution is complete.
        
        Execution is complete if:
        - All steps are DONE or SKIPPED
        - No steps are in progress
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            True if execution is complete
        """
        for step in plan.steps:
            step_state = current_state.get(step.step_id, StepState.PENDING)
            if step_state not in [StepState.DONE, StepState.SKIPPED]:
                return False
        
        return True

    def get_completion_percentage(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> float:
        """
        Calculate completion percentage.
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            Completion percentage (0.0 to 1.0)
        """
        if not plan.steps:
            return 1.0
        
        completed = 0
        for step in plan.steps:
            step_state = current_state.get(step.step_id, StepState.PENDING)
            if step_state in [StepState.DONE, StepState.SKIPPED]:
                completed += 1
        
        return completed / len(plan.steps)


class PriorityExecutionScheduler:
    """
    Priority-based execution scheduler.
    
    This scheduler prioritizes steps based on:
    - Step type (milestones first)
    - Dependencies
    - Estimated duration (shorter first)
    """

    def __init__(self) -> None:
        self._base_scheduler = BaseExecutionScheduler()

    def get_next_step(
        self,
        plan: ExecutionPlan,
        current_state: Dict[str, StepState],
    ) -> Optional[ExecutionStep]:
        """
        Get the next step to execute based on priority.
        
        Args:
            plan: The execution plan
            current_state: Current state of all steps
            
        Returns:
            The next step to execute
        """
        # Get all ready steps
        ready_steps = self._base_scheduler.get_ready_steps(plan, current_state)
        
        if not ready_steps:
            return None
        
        # Sort by priority
        prioritized_steps = self._prioritize_steps(ready_steps, plan)
        
        return prioritized_steps[0] if prioritized_steps else None

    def _prioritize_steps(
        self,
        steps: List[ExecutionStep],
        plan: ExecutionPlan,
    ) -> List[ExecutionStep]:
        """Prioritize steps based on multiple criteria."""
        def priority_score(step: ExecutionStep) -> int:
            score = 0
            
            # Milestones get highest priority
            if step.step_id in plan.milestones:
                score += 100
            
            # Quality gates get high priority
            if step.step_id in plan.quality_gates:
                score += 50
            
            # Shorter duration gets higher priority
            if step.estimated_duration:
                duration_minutes = self._parse_duration(step.estimated_duration)
                score -= duration_minutes  # Lower duration = higher score
            
            # Fewer dependencies gets higher priority
            score -= len(step.dependencies) * 5
            
            return score
        
        return sorted(steps, key=priority_score, reverse=True)

    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to minutes."""
        if not duration:
            return 10  # Default
        
        duration = duration.lower()
        if "h" in duration:
            return int(duration.replace("h", "")) * 60
        elif "m" in duration:
            return int(duration.replace("m", ""))
        else:
            return 10  # Default


# Default scheduler instance
default_scheduler = BaseExecutionScheduler()
