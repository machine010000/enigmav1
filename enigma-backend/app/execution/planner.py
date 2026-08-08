from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
    QualityGate,
    ExecutionPlanner,
)


class BaseExecutionPlanner:
    """
    Base implementation of Execution Planner.
    
    This planner creates execution plans from work specifications
    without any domain-specific logic. It relies on the work specification
    to provide the required capabilities and tasks.
    """

    def create_plan(
        self,
        work_specification_id: str,
        domain_id: str,
        session_id: str,
        context: Dict[str, Any],
    ) -> ExecutionPlan:
        """
        Create an execution plan from work specification.
        
        Args:
            work_specification_id: ID of the work specification
            domain_id: ID of the domain
            session_id: ID of the execution session
            context: Additional context including work specification details
            
        Returns:
            ExecutionPlan with steps, order, quality gates, and milestones
        """
        # Extract work specification from context
        work_spec = context.get("work_specification")
        
        # Create steps from work specification
        steps = self._create_steps_from_work_spec(
            work_specification_id,
            domain_id,
            session_id,
            work_spec,
        )
        
        # Determine step order based on dependencies
        step_order = self._determine_step_order(steps)
        
        # Identify quality gates (deliverable steps)
        quality_gates = self._identify_quality_gates(steps)
        
        # Identify milestones (capability steps)
        milestones = self._identify_milestones(steps)
        
        return ExecutionPlan(
            plan_id=f"plan_{session_id}",
            session_id=session_id,
            work_specification_id=work_specification_id,
            domain_id=domain_id,
            steps=steps,
            step_order=step_order,
            quality_gates=quality_gates,
            milestones=milestones,
            created_at=datetime.utcnow(),
            metadata={
                "planner_type": "base",
                "work_specification_id": work_specification_id,
            },
        )

    def _create_steps_from_work_spec(
        self,
        work_specification_id: str,
        domain_id: str,
        session_id: str,
        work_spec: Optional[Any],
    ) -> List[ExecutionStep]:
        """Create execution steps from work specification."""
        steps = []
        
        if not work_spec:
            # Return minimal plan if no work spec
            return steps
        
        # Extract required capabilities and tasks
        required_capabilities = getattr(work_spec, "required_capabilities", [])
        required_tasks = getattr(work_spec, "required_tasks", [])
        optional_tasks = getattr(work_spec, "optional_tasks", [])
        suggested_tasks = getattr(work_spec, "suggested_tasks", [])
        
        # Create capability steps
        for i, capability in enumerate(required_capabilities):
            step = ExecutionStep(
                step_id=f"capability_{i}_{uuid.uuid4().hex[:8]}",
                step_type=StepType.CAPABILITY,
                name=f"Execute {capability}",
                description=f"Execute capability: {capability}",
                state=StepState.PENDING,
                required_capabilities=[capability],
                expected_outputs=[f"{capability}_result"],
                estimated_duration="5m",
                metadata={"capability": capability},
            )
            steps.append(step)
        
        # Create task steps
        all_tasks = required_tasks + optional_tasks + suggested_tasks
        for i, task in enumerate(all_tasks):
            step = ExecutionStep(
                step_id=f"task_{i}_{uuid.uuid4().hex[:8]}",
                step_type=StepType.TASK,
                name=f"Execute {task}",
                description=f"Execute task: {task}",
                state=StepState.PENDING,
                dependencies=self._get_task_dependencies(task, required_capabilities, steps),
                expected_outputs=[f"{task}_result"],
                estimated_duration="10m",
                metadata={"task": task},
            )
            steps.append(step)
        
        # Create deliverable step (final step)
        if steps:
            deliverable_step = ExecutionStep(
                step_id=f"deliverable_{uuid.uuid4().hex[:8]}",
                step_type=StepType.DELIVERABLE,
                name="Generate Deliverable",
                description="Generate final deliverable from all execution results",
                state=StepState.PENDING,
                dependencies=[s.step_id for s in steps if s.step_type in [StepType.CAPABILITY, StepType.TASK]],
                expected_outputs=["deliverable"],
                estimated_duration="5m",
                metadata={"is_final_deliverable": True},
            )
            steps.append(deliverable_step)
        
        return steps

    def _determine_step_order(self, steps: List[ExecutionStep]) -> List[str]:
        """Determine execution order based on dependencies."""
        # Topological sort based on dependencies
        step_map = {step.step_id: step for step in steps}
        visited = set()
        order = []
        
        def visit(step_id: str):
            if step_id in visited:
                return
            visited.add(step_id)
            
            step = step_map.get(step_id)
            if step:
                for dep_id in step.dependencies:
                    visit(dep_id)
            
            order.append(step_id)
        
        for step in steps:
            visit(step.step_id)
        
        return order

    def _identify_quality_gates(self, steps: List[ExecutionStep]) -> List[str]:
        """Identify quality gates from steps."""
        # Deliverable steps are quality gates
        return [step.step_id for step in steps if step.step_type == StepType.DELIVERABLE]

    def _identify_milestones(self, steps: List[ExecutionStep]) -> List[str]:
        """Identify milestones from steps."""
        # Capability steps are milestones
        return [step.step_id for step in steps if step.step_type == StepType.CAPABILITY]

    def _get_task_dependencies(
        self,
        task: str,
        capabilities: List[str],
        existing_steps: List[ExecutionStep],
    ) -> List[str]:
        """Get dependencies for a task based on capabilities."""
        # Tasks depend on related capabilities
        dependencies = []
        
        for step in existing_steps:
            if step.step_type == StepType.CAPABILITY:
                # Simple heuristic: if task name contains capability name
                capability = step.metadata.get("capability", "")
                if capability.lower() in task.lower():
                    dependencies.append(step.step_id)
        
        return dependencies


class TemplateBasedPlanner:
    """
    Template-based execution planner.
    
    Uses predefined templates for common execution patterns.
    Templates are registered by domain but the planner itself
    remains domain-agnostic.
    """

    def __init__(self) -> None:
        self._templates: Dict[str, Dict[str, Any]] = {}

    def register_template(
        self,
        template_id: str,
        template: Dict[str, Any],
    ) -> None:
        """Register a template."""
        self._templates[template_id] = template

    def create_plan(
        self,
        work_specification_id: str,
        domain_id: str,
        session_id: str,
        context: Dict[str, Any],
    ) -> ExecutionPlan:
        """
        Create an execution plan using templates.
        
        Args:
            work_specification_id: ID of the work specification
            domain_id: ID of the domain
            session_id: ID of the execution session
            context: Additional context including template_id
            
        Returns:
            ExecutionPlan from template
        """
        template_id = context.get("template_id", "default")
        template = self._templates.get(template_id, {})
        
        # Get steps from template or create default
        template_steps = template.get("steps", [])
        steps = self._create_steps_from_template(
            template_steps,
            session_id,
            context,
        )
        
        # Get order from template or determine
        step_order = template.get("step_order") or self._determine_step_order(steps)
        
        # Get quality gates from template or identify
        quality_gates = template.get("quality_gates") or self._identify_quality_gates(steps)
        
        # Get milestones from template or identify
        milestones = template.get("milestones") or self._identify_milestones(steps)
        
        return ExecutionPlan(
            plan_id=f"plan_{session_id}",
            session_id=session_id,
            work_specification_id=work_specification_id,
            domain_id=domain_id,
            steps=steps,
            step_order=step_order,
            quality_gates=quality_gates,
            milestones=milestones,
            created_at=datetime.utcnow(),
            metadata={
                "planner_type": "template",
                "template_id": template_id,
                "work_specification_id": work_specification_id,
            },
        )

    def _create_steps_from_template(
        self,
        template_steps: List[Dict[str, Any]],
        session_id: str,
        context: Dict[str, Any],
    ) -> List[ExecutionStep]:
        """Create steps from template definition."""
        steps = []
        
        for i, step_def in enumerate(template_steps):
            step = ExecutionStep(
                step_id=step_def.get("step_id", f"step_{i}_{uuid.uuid4().hex[:8]}"),
                step_type=StepType(step_def.get("step_type", "task")),
                name=step_def.get("name", f"Step {i}"),
                description=step_def.get("description", ""),
                state=StepState.PENDING,
                dependencies=step_def.get("dependencies", []),
                required_capabilities=step_def.get("required_capabilities", []),
                inputs=step_def.get("inputs", {}),
                expected_outputs=step_def.get("expected_outputs", []),
                estimated_duration=step_def.get("estimated_duration"),
                max_retries=step_def.get("max_retries", 3),
                metadata=step_def.get("metadata", {}),
            )
            steps.append(step)
        
        return steps

    def _determine_step_order(self, steps: List[ExecutionStep]) -> List[str]:
        """Determine execution order based on dependencies."""
        step_map = {step.step_id: step for step in steps}
        visited = set()
        order = []
        
        def visit(step_id: str):
            if step_id in visited:
                return
            visited.add(step_id)
            
            step = step_map.get(step_id)
            if step:
                for dep_id in step.dependencies:
                    visit(dep_id)
            
            order.append(step_id)
        
        for step in steps:
            visit(step.step_id)
        
        return order

    def _identify_quality_gates(self, steps: List[ExecutionStep]) -> List[str]:
        """Identify quality gates from steps."""
        return [step.step_id for step in steps if step.step_type == StepType.DELIVERABLE]

    def _identify_milestones(self, steps: List[ExecutionStep]) -> List[str]:
        """Identify milestones from steps."""
        return [step.step_id for step in steps if step.step_type == StepType.CAPABILITY]


# Default planner instance
default_planner = BaseExecutionPlanner()
