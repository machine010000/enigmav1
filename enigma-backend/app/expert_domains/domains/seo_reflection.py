from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.knowledge_governance.models import (
    CandidateKnowledge,
    Evidence,
    SourceType,
    KnowledgeMaturity,
    KnowledgeFreshness,
)


class ReflectionOutcome(str, Enum):
    """Possible outcomes of task execution reflection."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    UNEXPECTED_RESULT = "unexpected_result"


@dataclass
class TaskExecutionResult:
    """Result of a task execution for reflection."""
    task_id: str
    execution_id: str
    expected_outcome: str
    actual_outcome: str
    metrics: Dict[str, float] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    """Reflection on a task execution."""
    reflection_id: str
    task_execution: TaskExecutionResult
    outcome: ReflectionOutcome
    difference: str
    reason: str
    lesson: str
    generated_candidates: List[CandidateKnowledge] = field(default_factory=list)
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReflectionGenerator(ABC):
    """Contract for generating reflections from task executions."""

    @abstractmethod
    def generate_reflection(
        self,
        execution_result: TaskExecutionResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> Reflection:
        """
        Generate a reflection from task execution.

        Process:
        1. Compare expected vs actual outcome
        2. Identify differences
        3. Determine reason for difference
        4. Extract lesson learned
        5. Generate candidate knowledge if applicable

        Never directly updates knowledge - only generates candidates.
        """
        pass


class SEOReflectionGenerator(ReflectionGenerator):
    """
    Generates SEO-specific reflections from task executions.

    Analyzes SEO task outcomes to extract learning opportunities.
    """

    def __init__(self) -> None:
        self._reflection_history: List[Reflection] = []

    def generate_reflection(
        self,
        execution_result: TaskExecutionResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> Reflection:
        """
        Generate a reflection from SEO task execution.

        Analyzes the execution to identify:
        - What was expected vs what happened
        - Why the difference occurred
        - What can be learned
        - What knowledge should be updated
        """
        context = context or {}

        # Determine outcome
        outcome = self._determine_outcome(execution_result)

        # Identify difference
        difference = self._identify_difference(execution_result)

        # Determine reason
        reason = self._determine_reason(execution_result, difference, context)

        # Extract lesson
        lesson = self._extract_lesson(execution_result, difference, reason)

        # Generate candidate knowledge if applicable
        candidates = self._generate_candidates(execution_result, lesson, reason)

        # Calculate confidence
        confidence = self._calculate_confidence(execution_result, candidates)

        reflection = Reflection(
            reflection_id=f"reflection_{datetime.utcnow().timestamp()}",
            task_execution=execution_result,
            outcome=outcome,
            difference=difference,
            reason=reason,
            lesson=lesson,
            generated_candidates=candidates,
            confidence=confidence,
            metadata=context,
        )

        # Record history
        self._reflection_history.append(reflection)

        return reflection

    def _determine_outcome(self, execution_result: TaskExecutionResult) -> ReflectionOutcome:
        """Determine the outcome of the task execution."""
        expected = execution_result.expected_outcome.lower()
        actual = execution_result.actual_outcome.lower()

        if expected == actual:
            return ReflectionOutcome.SUCCESS
        elif "partial" in actual or "some" in actual:
            return ReflectionOutcome.PARTIAL_SUCCESS
        elif "fail" in actual or "error" in actual:
            return ReflectionOutcome.FAILURE
        else:
            return ReflectionOutcome.UNEXPECTED_RESULT

    def _identify_difference(self, execution_result: TaskExecutionResult) -> str:
        """Identify the difference between expected and actual outcome."""
        expected = execution_result.expected_outcome
        actual = execution_result.actual_outcome

        if expected == actual:
            return "No difference - outcome matched expectations"
        else:
            return f"Expected '{expected}' but got '{actual}'"

    def _determine_reason(
        self,
        execution_result: TaskExecutionResult,
        difference: str,
        context: Dict[str, Any],
    ) -> str:
        """Determine the reason for the difference."""
        # Check metrics for clues
        metrics = execution_result.metadata.get("execution_metrics", {})

        if "ranking_change" in metrics:
            if metrics["ranking_change"] > 0:
                return "Ranking improved as expected"
            else:
                return "Ranking did not improve as expected"

        if "traffic_change" in metrics:
            if metrics["traffic_change"] > 0:
                return "Traffic increased as expected"
            else:
                return "Traffic did not increase as expected"

        if "errors" in execution_result.metadata:
            errors = execution_result.metadata["errors"]
            if errors:
                return f"Execution encountered errors: {', '.join(errors[:3])}"

        # Default reason based on outcome
        if execution_result.actual_outcome.lower() == "success":
            return "Task completed successfully"
        elif execution_result.actual_outcome.lower() == "failure":
            return "Task failed to complete"
        else:
            return "Outcome differed from expectations"

    def _extract_lesson(
        self,
        execution_result: TaskExecutionResult,
        difference: str,
        reason: str,
    ) -> str:
        """Extract the lesson learned from the execution."""
        task_id = execution_result.task_id

        # Task-specific lessons
        if "technical_seo_audit" in task_id:
            if "ranking" in reason.lower():
                return "Technical SEO factors directly impact rankings"
            elif "errors" in reason.lower():
                return "Technical errors prevent successful SEO execution"
            else:
                return "Technical SEO audit provides actionable insights"

        elif "keyword_research" in task_id:
            if "traffic" in reason.lower():
                return "Keyword selection affects traffic outcomes"
            else:
                return "Keyword research quality influences campaign success"

        elif "link_building" in task_id:
            if "authority" in reason.lower():
                return "Link quality impacts domain authority"
            else:
                return "Link building requires strategic approach"

        elif "on_page_optimization" in task_id:
            if "ranking" in reason.lower():
                return "On-page optimization affects search rankings"
            else:
                return "On-page elements require ongoing optimization"

        # Generic lesson
        if "success" in execution_result.actual_outcome.lower():
            return "Successful execution validates current approach"
        elif "failure" in execution_result.actual_outcome.lower():
            return "Failed execution indicates need for approach adjustment"
        else:
            return "Mixed results suggest need for optimization"

    def _generate_candidates(
        self,
        execution_result: TaskExecutionResult,
        lesson: str,
        reason: str,
    ) -> List[CandidateKnowledge]:
        """
        Generate candidate knowledge from the reflection.

        Only generates candidates if the reflection indicates a learning opportunity.
        """
        candidates = []

        # Only generate candidates for significant learnings
        outcome = self._determine_outcome(execution_result)
        if outcome in [
            ReflectionOutcome.FAILURE,
            ReflectionOutcome.UNEXPECTED_RESULT,
        ]:
            # Create evidence from the execution
            evidence = Evidence(
                id=f"evidence_reflection_{execution_result.execution_id}",
                source="task_execution_reflection",
                source_type=SourceType.EXPERIMENT,
                claim=f"{lesson}: {reason}",
                retrieved_at=execution_result.completed_at,
                quality_score=0.6,  # Medium trust for reflections
                confidence=0.5,
                freshness=KnowledgeFreshness.FRESH,
                metadata={
                    "task_id": execution_result.task_id,
                    "execution_id": execution_result.execution_id,
                    "outcome": execution_result.actual_outcome,
                },
            )

            # Create candidate knowledge
            concept_name = self._extract_concept_name(execution_result, lesson)
            candidate = CandidateKnowledge(
                id=f"candidate_reflection_{execution_result.execution_id}",
                name=concept_name,
                definition=f"{lesson}. Based on execution: {reason}",
                evidence=[evidence],
                proposed_maturity=KnowledgeMaturity.DEFINITION,
                proposed_confidence=0.5,
                source="task_reflection",
                submitted_at=datetime.utcnow(),
                metadata={
                    "task_id": execution_result.task_id,
                    "execution_id": execution_result.execution_id,
                    "reflection_type": "post_execution",
                },
            )

            candidates.append(candidate)

        return candidates

    def _extract_concept_name(
        self,
        execution_result: TaskExecutionResult,
        lesson: str,
    ) -> str:
        """Extract a concept name from the lesson."""
        task_id = execution_result.task_id

        # Map tasks to concept names
        if "technical_seo_audit" in task_id:
            return "technical_seo_execution"
        elif "keyword_research" in task_id:
            return "keyword_research_execution"
        elif "link_building" in task_id:
            return "link_building_execution"
        elif "on_page_optimization" in task_id:
            return "on_page_optimization_execution"
        else:
            return f"{task_id}_execution"

    def _calculate_confidence(
        self,
        execution_result: TaskExecutionResult,
        candidates: List[CandidateKnowledge],
    ) -> float:
        """Calculate confidence in the reflection."""
        base_confidence = 0.5

        # Increase confidence if we have metrics
        if execution_result.metrics:
            base_confidence += 0.2

        # Increase confidence if we generated candidates
        if candidates:
            base_confidence += 0.1

        # Adjust based on outcome
        outcome = self._determine_outcome(execution_result)
        if outcome == ReflectionOutcome.SUCCESS:
            base_confidence += 0.1
        elif outcome == ReflectionOutcome.FAILURE:
            base_confidence -= 0.1

        return min(1.0, max(0.0, base_confidence))

    def get_reflection_history(self) -> List[Reflection]:
        """Get history of reflections."""
        return self._reflection_history.copy()

    def get_reflection_statistics(self) -> Dict[str, Any]:
        """Get statistics about reflections."""
        if not self._reflection_history:
            return {
                "total_reflections": 0,
                "by_outcome": {},
                "candidates_generated": 0,
            }

        by_outcome: Dict[str, int] = {}
        candidates_generated = 0

        for reflection in self._reflection_history:
            outcome = reflection.outcome.value
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
            candidates_generated += len(reflection.generated_candidates)

        return {
            "total_reflections": len(self._reflection_history),
            "by_outcome": by_outcome,
            "candidates_generated": candidates_generated,
        }


class SEOReflectionOrchestrator:
    """
    Orchestrates the reflection process for SEO tasks.

    Provides high-level interface for reflection operations.
    """

    def __init__(self) -> None:
        self._generator = SEOReflectionGenerator()

    def reflect_on_task(
        self,
        task_id: str,
        execution_id: str,
        expected_outcome: str,
        actual_outcome: str,
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Reflection:
        """
        Reflect on a completed SEO task.

        Creates a reflection and generates candidate knowledge if applicable.
        """
        execution_result = TaskExecutionResult(
            task_id=task_id,
            execution_id=execution_id,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            metrics=metrics or {},
            metadata=metadata or {},
        )

        return self._generator.generate_reflection(execution_result)

    def reflect_on_success(
        self,
        task_id: str,
        execution_id: str,
        metrics: Optional[Dict[str, float]] = None,
    ) -> Reflection:
        """Reflect on a successful task execution."""
        return self.reflect_on_task(
            task_id=task_id,
            execution_id=execution_id,
            expected_outcome="success",
            actual_outcome="success",
            metrics=metrics,
        )

    def reflect_on_failure(
        self,
        task_id: str,
        execution_id: str,
        error_reason: str,
        metrics: Optional[Dict[str, float]] = None,
    ) -> Reflection:
        """Reflect on a failed task execution."""
        return self.reflect_on_task(
            task_id=task_id,
            execution_id=execution_id,
            expected_outcome="success",
            actual_outcome=f"failure: {error_reason}",
            metrics=metrics,
            metadata={"errors": [error_reason]},
        )

    def reflect_on_partial_success(
        self,
        task_id: str,
        execution_id: str,
        success_description: str,
        failure_description: str,
        metrics: Optional[Dict[str, float]] = None,
    ) -> Reflection:
        """Reflect on a partially successful task execution."""
        return self.reflect_on_task(
            task_id=task_id,
            execution_id=execution_id,
            expected_outcome="success",
            actual_outcome=f"partial success: {success_description}, but {failure_description}",
            metrics=metrics,
        )

    def get_reflection_statistics(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        return self._generator.get_reflection_statistics()

    def get_reflection_history(self) -> List[Reflection]:
        """Get reflection history."""
        return self._generator.get_reflection_history()
