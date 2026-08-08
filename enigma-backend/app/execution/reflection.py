from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    ExecutionReflection,
    ReflectionGenerator,
)


@dataclass
class ReflectionContext:
    """Context for generating reflections."""
    session_id: str
    plan: ExecutionPlan
    execution_results: Dict[str, Any]
    step_states: Dict[str, StepState]
    outputs: Dict[str, List[Any]] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseReflectionGenerator:
    """
    Base implementation of Reflection Generator.
    
    This generator creates reflections from execution results without
    containing domain-specific logic. It analyzes:
    - What went well
    - What could be improved
    - Lessons learned
    - Action items
    """

    def generate_reflection(
        self,
        session_id: str,
        plan: ExecutionPlan,
        execution_results: Dict[str, Any],
    ) -> ExecutionReflection:
        """
        Generate reflection from execution results.
        
        Args:
            session_id: ID of the execution session
            plan: The execution plan that was executed
            execution_results: Results from execution
            
        Returns:
            ExecutionReflection with analysis and recommendations
        """
        reflection_id = f"reflection_{uuid.uuid4().hex[:8]}"
        
        # Extract step states from execution results
        step_states = execution_results.get("step_states", {})
        outputs = execution_results.get("outputs", {})
        errors = execution_results.get("errors", {})
        
        # Create reflection context
        context = ReflectionContext(
            session_id=session_id,
            plan=plan,
            execution_results=execution_results,
            step_states=step_states,
            outputs=outputs,
            errors=errors,
        )
        
        # Analyze what went well
        what_went_well = self._analyze_what_went_well(context)
        
        # Analyze what could be improved
        what_could_be_improved = self._analyze_what_could_be_improved(context)
        
        # Extract lessons learned
        lessons_learned = self._extract_lessons_learned(context)
        
        # Generate action items
        action_items = self._generate_action_items(context)
        
        return ExecutionReflection(
            reflection_id=reflection_id,
            session_id=session_id,
            reflection_type="overall",
            subject=f"Execution reflection for session {session_id}",
            what_went_well=what_went_well,
            what_could_be_improved=what_could_be_improved,
            lessons_learned=lessons_learned,
            action_items=action_items,
            reflected_at=datetime.utcnow(),
            metadata={
                "plan_id": plan.plan_id,
                "domain_id": plan.domain_id,
                "total_steps": len(plan.steps),
                "completed_steps": len([s for s in plan.steps if step_states.get(s.step_id) == StepState.DONE]),
            },
        )

    def _analyze_what_went_well(self, context: ReflectionContext) -> List[str]:
        """Analyze what went well during execution."""
        what_went_well = []
        
        # Check for successful steps
        successful_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.DONE
        ]
        
        if successful_steps:
            what_went_well.append(f"Successfully completed {len(successful_steps)} steps")
        
        # Check for milestone completion
        completed_milestones = [
            step for step in context.plan.steps
            if step.step_id in context.plan.milestones
            and context.step_states.get(step.step_id) == StepState.DONE
        ]
        
        if completed_milestones:
            what_went_well.append(f"Completed {len(completed_milestones)} milestones")
        
        # Check for quality gate passage
        passed_quality_gates = [
            step for step in context.plan.steps
            if step.step_id in context.plan.quality_gates
            and context.step_states.get(step.step_id) == StepState.DONE
        ]
        
        if passed_quality_gates:
            what_went_well.append(f"Passed {len(passed_quality_gates)} quality gates")
        
        # Check for no critical errors
        if not context.errors:
            what_went_well.append("No critical errors encountered")
        
        return what_went_well

    def _analyze_what_could_be_improved(self, context: ReflectionContext) -> List[str]:
        """Analyze what could be improved during execution."""
        what_could_be_improved = []
        
        # Check for failed steps
        failed_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        if failed_steps:
            what_could_be_improved.append(f"{len(failed_steps)} steps failed")
            for step in failed_steps:
                error_msg = context.errors.get(step.step_id, "Unknown error")
                what_could_be_improved.append(f"Step '{step.name}' failed: {error_msg}")
        
        # Check for retries
        retried_steps = [
            step for step in context.plan.steps
            if step.retry_count > 0
        ]
        
        if retried_steps:
            what_could_be_improved.append(f"{len(retried_steps)} steps required retries")
        
        # Check for skipped steps
        skipped_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.SKIPPED
        ]
        
        if skipped_steps:
            what_could_be_improved.append(f"{len(skipped_steps)} steps were skipped")
        
        return what_could_be_improved

    def _extract_lessons_learned(self, context: ReflectionContext) -> List[str]:
        """Extract lessons learned from execution."""
        lessons = []
        
        # Lesson from failures
        failed_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        if failed_steps:
            lessons.append("Identify and address common failure patterns")
        
        # Lesson from retries
        retried_steps = [
            step for step in context.plan.steps
            if step.retry_count > 0
        ]
        
        if retried_steps:
            lessons.append("Improve step reliability to reduce retries")
        
        # Lesson from dependencies
        blocked_steps = 0
        for step in context.plan.steps:
            for dep_id in step.dependencies:
                dep_state = context.step_states.get(dep_id)
                if dep_state == StepState.FAILED:
                    blocked_steps += 1
        
        if blocked_steps > 0:
            lessons.append("Review and optimize step dependencies")
        
        return lessons

    def _generate_action_items(self, context: ReflectionContext) -> List[str]:
        """Generate action items from reflection."""
        action_items = []
        
        # Action items for failed steps
        failed_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        for step in failed_steps:
            action_items.append(f"Investigate and fix failure in step: {step.name}")
        
        # Action items for improvements
        if context.errors:
            action_items.append("Review error handling and add better error recovery")
        
        # Action items for optimization
        retried_steps = [
            step for step in context.plan.steps
            if step.retry_count > 0
        ]
        
        if retried_steps:
            action_items.append("Optimize steps that required retries")
        
        return action_items


class StepReflectionGenerator:
    """
    Generator for step-level reflections.
    
    This generator creates reflections for individual steps.
    """

    def generate_step_reflection(
        self,
        session_id: str,
        step: ExecutionStep,
        execution_result: Dict[str, Any],
    ) -> ExecutionReflection:
        """
        Generate reflection for a single step.
        
        Args:
            session_id: ID of the execution session
            step: The step to reflect on
            execution_result: Result from step execution
            
        Returns:
            ExecutionReflection for the step
        """
        reflection_id = f"step_reflection_{uuid.uuid4().hex[:8]}"
        
        success = execution_result.get("success", False)
        error_message = execution_result.get("error_message")
        
        what_went_well = []
        what_could_be_improved = []
        lessons_learned = []
        action_items = []
        
        if success:
            what_went_well.append(f"Step '{step.name}' completed successfully")
            if execution_result.get("outputs"):
                what_went_well.append(f"Generated {len(execution_result['outputs'])} outputs")
        else:
            what_could_be_improved.append(f"Step '{step.name}' failed")
            if error_message:
                what_could_be_improved.append(f"Error: {error_message}")
            action_items.append(f"Investigate failure in step: {step.name}")
            lessons_learned.append(f"Step '{step.name}' needs reliability improvements")
        
        return ExecutionReflection(
            reflection_id=reflection_id,
            session_id=session_id,
            reflection_type="step",
            subject=f"Reflection for step: {step.name}",
            what_went_well=what_went_well,
            what_could_be_improved=what_could_be_improved,
            lessons_learned=lessons_learned,
            action_items=action_items,
            reflected_at=datetime.utcnow(),
            metadata={
                "step_id": step.step_id,
                "step_type": step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type),
                "success": success,
            },
        )


class CallbackReflectionGenerator:
    """
    Reflection generator that uses a callback function.
    
    This allows custom reflection logic to be injected without
    creating a full generator class.
    """

    def __init__(
        self,
        generate_callback: Callable[
            [str, ExecutionPlan, Dict[str, Any]],
            ExecutionReflection,
        ],
    ) -> None:
        self._generate_callback = generate_callback

    def generate_reflection(
        self,
        session_id: str,
        plan: ExecutionPlan,
        execution_results: Dict[str, Any],
    ) -> ExecutionReflection:
        """Generate reflection using callback."""
        return self._generate_callback(session_id, plan, execution_results)


class AggregateReflectionGenerator:
    """
    Aggregate reflection generator that combines multiple generators.
    
    This generator allows multiple reflection sources to be combined
    into a single comprehensive reflection.
    """

    def __init__(self) -> None:
        self._generators: List[ReflectionGenerator] = []

    def add_generator(self, generator: ReflectionGenerator) -> None:
        """Add a reflection generator."""
        self._generators.append(generator)

    def generate_reflection(
        self,
        session_id: str,
        plan: ExecutionPlan,
        execution_results: Dict[str, Any],
    ) -> ExecutionReflection:
        """Generate reflection by combining all generators."""
        all_what_went_well = []
        all_what_could_be_improved = []
        all_lessons_learned = []
        all_action_items = []
        
        for generator in self._generators:
            try:
                reflection = generator.generate_reflection(session_id, plan, execution_results)
                all_what_went_well.extend(reflection.what_went_well)
                all_what_could_be_improved.extend(reflection.what_could_be_improved)
                all_lessons_learned.extend(reflection.lessons_learned)
                all_action_items.extend(reflection.action_items)
            except Exception:
                # Continue with other generators if one fails
                pass
        
        # Remove duplicates
        all_what_went_well = list(set(all_what_went_well))
        all_what_could_be_improved = list(set(all_what_could_be_improved))
        all_lessons_learned = list(set(all_lessons_learned))
        all_action_items = list(set(all_action_items))
        
        return ExecutionReflection(
            reflection_id=f"aggregate_reflection_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            reflection_type="aggregate",
            subject=f"Aggregate reflection for session {session_id}",
            what_went_well=all_what_went_well,
            what_could_be_improved=all_what_could_be_improved,
            lessons_learned=all_lessons_learned,
            action_items=all_action_items,
            reflected_at=datetime.utcnow(),
            metadata={
                "generator_count": len(self._generators),
            },
        )


# Default reflection generator instance
default_reflection_generator = BaseReflectionGenerator()
