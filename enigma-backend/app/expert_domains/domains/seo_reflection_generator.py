from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    ExecutionReflection,
    ReflectionGenerator,
)
from app.execution.reflection import BaseReflectionGenerator


@dataclass
class SEOReflectionContext:
    """Context for SEO reflection generation."""
    session_id: str
    plan: ExecutionPlan
    execution_results: Dict[str, Any]
    step_states: Dict[str, StepState]
    outputs: Dict[str, List[Any]] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None
    audit_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SEOReflectionGenerator(BaseReflectionGenerator):
    """
    SEO-specific reflection generator.
    
    Generates reflections for SEO execution with domain-specific insights including:
    - Technical SEO performance
    - Knowledge gaps
    - Evidence gaps
    - Learning recommendations
    - Readiness updates
    """

    def generate_reflection(
        self,
        session_id: str,
        plan: ExecutionPlan,
        execution_results: Dict[str, Any],
    ) -> ExecutionReflection:
        """
        Generate SEO-specific reflection from execution results.
        
        Args:
            session_id: ID of the execution session
            plan: The execution plan that was executed
            execution_results: Results from execution
            
        Returns:
            ExecutionReflection with SEO-specific analysis
        """
        reflection_id = f"seo_reflection_{uuid.uuid4().hex[:8]}"
        
        # Extract step states and outputs
        step_states = execution_results.get("step_states", {})
        outputs = execution_results.get("outputs", {})
        errors = execution_results.get("errors", {})
        
        # Create SEO reflection context
        context = SEOReflectionContext(
            session_id=session_id,
            plan=plan,
            execution_results=execution_results,
            step_states=step_states,
            outputs=outputs,
            errors=errors,
            url=execution_results.get("url"),
            audit_type=execution_results.get("audit_type", "technical_seo_audit"),
            metadata=execution_results.get("metadata", {}),
        )
        
        # Analyze what went well
        what_went_well = self._analyze_what_went_well(context)
        
        # Analyze what could be improved
        what_could_be_improved = self._analyze_what_could_be_improved(context)
        
        # Extract lessons learned
        lessons_learned = self._extract_lessons_learned(context)
        
        # Generate action items
        action_items = self._generate_action_items(context)
        
        # Identify missing knowledge
        missing_knowledge = self._identify_missing_knowledge(context)
        
        # Identify missing evidence
        missing_evidence = self._identify_missing_evidence(context)
        
        # Suggest learning
        suggested_learning = self._suggest_learning(context)
        
        return ExecutionReflection(
            reflection_id=reflection_id,
            session_id=session_id,
            reflection_type="seo_execution",
            subject=f"SEO Execution Reflection for {context.audit_type}",
            what_went_well=what_went_well,
            what_could_be_improved=what_could_be_improved,
            lessons_learned=lessons_learned,
            action_items=action_items,
            reflected_at=datetime.utcnow(),
            metadata={
                "plan_id": plan.plan_id,
                "domain_id": plan.domain_id,
                "audit_type": context.audit_type,
                "url": context.url,
                "total_steps": len(plan.steps),
                "completed_steps": len([s for s in plan.steps if step_states.get(s.step_id) == StepState.DONE]),
                "missing_knowledge": missing_knowledge,
                "missing_evidence": missing_evidence,
                "suggested_learning": suggested_learning,
            },
        )

    def _analyze_what_went_well(self, context: SEOReflectionContext) -> List[str]:
        """Analyze what went well during SEO execution."""
        what_went_well = []
        
        # Check for successful steps
        successful_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.DONE
        ]
        
        if successful_steps:
            what_went_well.append(f"Successfully completed {len(successful_steps)} execution steps")
        
        # Check for audit completion
        if context.audit_type == "technical_seo_audit":
            what_went_well.append("Technical SEO audit completed successfully")
        
        # Check for outputs generated
        total_outputs = sum(len(outputs) for outputs in context.outputs.values())
        if total_outputs > 0:
            what_went_well.append(f"Generated {total_outputs} SEO outputs including reports, findings, and recommendations")
        
        # Check for evidence collection
        evidence_outputs = [
            output for outputs in context.outputs.values()
            for output in outputs
            if hasattr(output, 'output_type') and str(output.output_type) == "evidence"
        ]
        if evidence_outputs:
            what_went_well.append(f"Collected {len(evidence_outputs)} evidence items for knowledge governance")
        
        # Check for no critical errors
        if not context.errors:
            what_went_well.append("No critical errors encountered during execution")
        
        # Check for metrics generation
        metrics_outputs = [
            output for outputs in context.outputs.values()
            for output in outputs
            if hasattr(output, 'output_type') and str(output.output_type) == "metric"
        ]
        if metrics_outputs:
            what_went_well.append("Generated SEO performance metrics for analysis")
        
        return what_went_well

    def _analyze_what_could_be_improved(self, context: SEOReflectionContext) -> List[str]:
        """Analyze what could be improved during SEO execution."""
        what_could_be_improved = []
        
        # Check for failed steps
        failed_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        if failed_steps:
            what_could_be_improved.append(f"{len(failed_steps)} steps failed during execution")
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
        
        # Check for incomplete outputs
        expected_outputs = set()
        for step in context.plan.steps:
            expected_outputs.update(step.expected_outputs)
        
        actual_outputs = set()
        for outputs in context.outputs.values():
            for output in outputs:
                if hasattr(output, 'name'):
                    actual_outputs.add(output.name)
        
        missing_outputs = expected_outputs - actual_outputs
        if missing_outputs:
            what_could_be_improved.append(f"Missing {len(missing_outputs)} expected outputs: {list(missing_outputs)}")
        
        return what_could_be_improved

    def _extract_lessons_learned(self, context: SEOReflectionContext) -> List[str]:
        """Extract lessons learned from SEO execution."""
        lessons = []
        
        # Lesson from failures
        failed_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        if failed_steps:
            lessons.append("Identify and address common failure patterns in SEO execution")
        
        # Lesson from retries
        retried_steps = [
            step for step in context.plan.steps
            if step.retry_count > 0
        ]
        
        if retried_steps:
            lessons.append("Improve step reliability to reduce retries in SEO tasks")
        
        # Lesson from dependencies
        blocked_steps = 0
        for step in context.plan.steps:
            for dep_id in step.dependencies:
                dep_state = context.step_states.get(dep_id)
                if dep_state == StepState.FAILED:
                    blocked_steps += 1
        
        if blocked_steps > 0:
            lessons.append("Review and optimize step dependencies for SEO workflows")
        
        # SEO-specific lessons
        if context.audit_type == "technical_seo_audit":
            lessons.append("Technical SEO audits require comprehensive crawling and analysis")
            lessons.append("Page speed optimization is critical for SEO performance")
        
        return lessons

    def _generate_action_items(self, context: SEOReflectionContext) -> List[str]:
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
            action_items.append("Review error handling and add better error recovery for SEO tasks")
        
        # Action items for optimization
        retried_steps = [
            step for step in context.plan.steps
            if step.retry_count > 0
        ]
        
        if retried_steps:
            action_items.append("Optimize SEO steps that required retries")
        
        # SEO-specific action items
        if context.audit_type == "technical_seo_audit":
            action_items.append("Implement automated technical SEO crawling for faster audits")
            action_items.append("Enhance issue severity scoring for better prioritization")
        
        return action_items

    def _identify_missing_knowledge(self, context: SEOReflectionContext) -> List[str]:
        """Identify missing knowledge from execution."""
        missing_knowledge = []
        
        # Check for failed technical analysis
        failed_technical_steps = [
            step for step in context.plan.steps
            if "technical" in step.name.lower()
            and context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        if failed_technical_steps:
            missing_knowledge.append("Technical SEO analysis patterns need improvement")
        
        # Check for missing outputs
        if not context.outputs:
            missing_knowledge.append("Output generation patterns need development")
        
        # SEO-specific knowledge gaps
        if context.audit_type == "technical_seo_audit":
            # Check if certain key outputs are missing
            has_findings = any("finding" in str(o).lower() for outputs in context.outputs.values() for o in outputs)
            has_recommendations = any("recommendation" in str(o).lower() for outputs in context.outputs.values() for o in outputs)
            
            if not has_findings:
                missing_knowledge.append("Technical SEO finding extraction patterns")
            if not has_recommendations:
                missing_knowledge.append("SEO recommendation generation patterns")
        
        return missing_knowledge

    def _identify_missing_evidence(self, context: SEOReflectionContext) -> List[str]:
        """Identify missing evidence from execution."""
        missing_evidence = []
        
        # Check for evidence outputs
        evidence_outputs = [
            output for outputs in context.outputs.values()
            for output in outputs
            if hasattr(output, 'output_type') and str(output.output_type) == "evidence"
        ]
        
        if not evidence_outputs:
            missing_evidence.append("Evidence collection during SEO execution")
        
        # Check for crawl data
        has_crawl_data = any(
            "crawl" in str(o.content).lower() if hasattr(o, 'content') else False
            for outputs in context.outputs.values()
            for o in outputs
        )
        
        if not has_crawl_data and context.audit_type == "technical_seo_audit":
            missing_evidence.append("Technical crawl data evidence")
        
        # Check for performance data
        has_performance_data = any(
            "performance" in str(o.content).lower() if hasattr(o, 'content') else False
            for outputs in context.outputs.values()
            for o in outputs
        )
        
        if not has_performance_data:
            missing_evidence.append("Performance metrics evidence")
        
        return missing_evidence

    def _suggest_learning(self, context: SEOReflectionContext) -> List[str]:
        """Suggest learning based on execution results."""
        suggested_learning = []
        
        # Learning from failures
        failed_steps = [
            step for step in context.plan.steps
            if context.step_states.get(step.step_id) == StepState.FAILED
        ]
        
        if failed_steps:
            suggested_learning.append("Investigate failure patterns in SEO execution to improve reliability")
        
        # Learning from missing knowledge
        missing_knowledge = self._identify_missing_knowledge(context)
        if missing_knowledge:
            suggested_learning.append(f"Develop knowledge patterns for: {', '.join(missing_knowledge)}")
        
        # Learning from missing evidence
        missing_evidence = self._identify_missing_evidence(context)
        if missing_evidence:
            suggested_learning.append(f"Develop evidence collection patterns for: {', '.join(missing_evidence)}")
        
        # SEO-specific learning
        if context.audit_type == "technical_seo_audit":
            suggested_learning.append("Study advanced technical SEO patterns and best practices")
            suggested_learning.append("Research automated crawling and analysis techniques")
        
        return suggested_learning


# Default SEO reflection generator instance
seo_reflection_generator = SEOReflectionGenerator()
