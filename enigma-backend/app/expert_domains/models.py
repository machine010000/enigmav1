from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import (
    DomainLifecycleStage,
    DomainIdentity,
    KnowledgeArea,
    DomainConcept,
    DomainEvidence,
    ReasoningPattern,
    DecisionRule,
    DomainKPI,
    ExecutionStandard,
    EvaluationResult,
    ReadinessScore,
)


class KnowledgeStructure:
    """Defines the structure of knowledge organization for a domain."""

    def __init__(
        self,
        knowledge_areas: List[KnowledgeArea],
        concepts: List[DomainConcept],
        relationships: Dict[str, List[str]] = None,
    ):
        self.knowledge_areas = knowledge_areas
        self.concepts = concepts
        self.relationships = relationships or {}

    def get_concepts_by_area(self, area_id: str) -> List[DomainConcept]:
        """Get all concepts belonging to a knowledge area."""
        area = next((a for a in self.knowledge_areas if a.area_id == area_id), None)
        if area:
            return [c for c in self.concepts if c.concept_id in area.required_concepts]
        return []

    def get_related_concepts(self, concept_id: str) -> List[DomainConcept]:
        """Get concepts related to a given concept."""
        related_ids = self.relationships.get(concept_id, [])
        return [c for c in self.concepts if c.concept_id in related_ids]


class DomainLifecycle:
    """Manages the lifecycle stages of an expert domain."""

    LIFECYCLE_TRANSITIONS = {
        DomainLifecycleStage.UNKNOWN: [DomainLifecycleStage.LEARNING],
        DomainLifecycleStage.LEARNING: [DomainLifecycleStage.GROWING],
        DomainLifecycleStage.GROWING: [DomainLifecycleStage.OPERATIONAL],
        DomainLifecycleStage.OPERATIONAL: [DomainLifecycleStage.EXPERT],
        DomainLifecycleStage.EXPERT: [DomainLifecycleStage.SELF_IMPROVING],
        DomainLifecycleStage.SELF_IMPROVING: [DomainLifecycleStage.SELF_IMPROVING],
    }

    def __init__(self, current_stage: DomainLifecycleStage = DomainLifecycleStage.UNKNOWN):
        self.current_stage = current_stage
        self.stage_history: List[tuple[DomainLifecycleStage, datetime]] = [
            (current_stage, datetime.utcnow())
        ]

    def can_advance_to(self, stage: DomainLifecycleStage) -> bool:
        """Check if the domain can advance to the given stage."""
        possible_transitions = self.LIFECYCLE_TRANSITIONS.get(self.current_stage, [])
        return stage in possible_transitions

    def advance_to(self, stage: DomainLifecycleStage) -> bool:
        """Advance the domain to the given lifecycle stage."""
        if self.can_advance_to(stage):
            self.current_stage = stage
            self.stage_history.append((stage, datetime.utcnow()))
            return True
        return False

    def get_current_stage(self) -> DomainLifecycleStage:
        """Return the current lifecycle stage."""
        return self.current_stage

    def get_stage_history(self) -> List[tuple[DomainLifecycleStage, datetime]]:
        """Return the history of lifecycle stage transitions."""
        return self.stage_history.copy()


class DomainMaturity:
    """Manages knowledge maturity for a domain."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self._concept_maturity: Dict[str, int] = {}  # concept_id -> maturity level (0-5)

    def set_concept_maturity(self, concept_id: str, maturity: int) -> None:
        """Set the maturity level for a concept."""
        self._concept_maturity[concept_id] = max(0, min(5, maturity))

    def get_concept_maturity(self, concept_id: str) -> int:
        """Get the maturity level for a concept."""
        return self._concept_maturity.get(concept_id, 0)

    def get_average_maturity(self) -> float:
        """Get the average maturity level across all concepts."""
        if not self._concept_maturity:
            return 0.0
        return sum(self._concept_maturity.values()) / len(self._concept_maturity)

    def get_maturity_distribution(self) -> Dict[int, int]:
        """Get the distribution of maturity levels."""
        distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for maturity in self._concept_maturity.values():
            distribution[maturity] += 1
        return distribution


class DomainEvaluation:
    """Evaluates domain state based on defined criteria."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id

    def evaluate_execution_quality(
        self,
        execution_results: List[Dict[str, Any]],
        standards: List[ExecutionStandard],
    ) -> float:
        """Evaluate execution quality based on results and standards."""
        if not execution_results:
            return 0.0

        score = 0.0
        for result in execution_results:
            # Placeholder: calculate quality based on standards
            quality_score = 0.5  # Default score
            score += quality_score

        return min(score / len(execution_results), 1.0)

    def evaluate_knowledge_quality(
        self,
        concepts: List[DomainConcept],
        evidence: List[DomainEvidence],
    ) -> float:
        """Evaluate knowledge quality based on concepts and evidence."""
        if not concepts:
            return 0.0

        total_maturity = sum(c.knowledge_maturity.value for c in concepts)
        avg_maturity = total_maturity / len(concepts)
        return avg_maturity / 5.0  # Normalize to 0-1

    def evaluate_evidence_coverage(
        self,
        concepts: List[DomainConcept],
        evidence: List[DomainEvidence],
    ) -> float:
        """Evaluate evidence coverage for concepts."""
        if not concepts:
            return 0.0

        concepts_with_evidence = sum(1 for c in concepts if c.evidence_ids)
        return concepts_with_evidence / len(concepts)

    def evaluate_risk(
        self,
        evaluation_result: EvaluationResult,
    ) -> float:
        """Evaluate overall risk."""
        # Placeholder: calculate risk based on evaluation result
        return evaluation_result.risk


class DomainReadiness:
    """Calculates readiness scores for expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id

    def calculate_knowledge_readiness(
        self,
        concepts: List[DomainConcept],
        required_concepts: List[str],
    ) -> float:
        """Calculate knowledge readiness."""
        if not required_concepts:
            return 1.0

        available_concept_ids = set(c.concept_id for c in concepts)
        required_set = set(required_concepts)
        available_set = available_concept_ids & required_set

        return len(available_set) / len(required_set) if required_set else 1.0

    def calculate_execution_readiness(
        self,
        past_executions: List[Dict[str, Any]],
        standards: List[ExecutionStandard],
    ) -> float:
        """Calculate execution readiness."""
        if not past_executions:
            return 0.0

        # Placeholder: calculate based on past success rate
        success_count = sum(1 for e in past_executions if e.get("success", False))
        return success_count / len(past_executions)

    def calculate_evidence_readiness(
        self,
        concepts: List[DomainConcept],
        evidence: List[DomainEvidence],
    ) -> float:
        """Calculate evidence readiness."""
        if not concepts:
            return 0.0

        concepts_with_sufficient_evidence = 0
        for concept in concepts:
            if len(concept.evidence_ids) >= 2:  # Require at least 2 evidence
                concepts_with_sufficient_evidence += 1

        return concepts_with_sufficient_evidence / len(concepts)

    def calculate_learning_readiness(
        self,
        recent_learning: List[Dict[str, Any]],
    ) -> float:
        """Calculate learning readiness."""
        if not recent_learning:
            return 0.0

        # Placeholder: calculate based on recent learning activity
        return min(len(recent_learning) / 10.0, 1.0)

    def calculate_overall_readiness(
        self,
        knowledge_readiness: float,
        execution_readiness: float,
        evidence_readiness: float,
        learning_readiness: float,
    ) -> float:
        """Calculate overall readiness."""
        weights = {
            "knowledge": 0.3,
            "execution": 0.3,
            "evidence": 0.2,
            "learning": 0.2,
        }
        return (
            knowledge_readiness * weights["knowledge"]
            + execution_readiness * weights["execution"]
            + evidence_readiness * weights["evidence"]
            + learning_readiness * weights["learning"]
        )


class DomainLearning:
    """Manages learning behavior for expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self._learning_events: List[Dict[str, Any]] = []

    def record_new_knowledge(
        self,
        concept_id: str,
        knowledge: str,
        source: str,
    ) -> None:
        """Record acquisition of new knowledge."""
        self._learning_events.append({
            "type": "new_knowledge",
            "concept_id": concept_id,
            "knowledge": knowledge,
            "source": source,
            "timestamp": datetime.utcnow(),
        })

    def record_evidence_update(
        self,
        evidence_id: str,
        update_type: str,
    ) -> None:
        """Record an evidence update."""
        self._learning_events.append({
            "type": "evidence_update",
            "evidence_id": evidence_id,
            "update_type": update_type,
            "timestamp": datetime.utcnow(),
        })

    def record_concept_update(
        self,
        concept_id: str,
        update_type: str,
    ) -> None:
        """Record a concept update."""
        self._learning_events.append({
            "type": "concept_update",
            "concept_id": concept_id,
            "update_type": update_type,
            "timestamp": datetime.utcnow(),
        })

    def record_rule_update(
        self,
        rule_id: str,
        update_type: str,
    ) -> None:
        """Record a rule update."""
        self._learning_events.append({
            "type": "rule_update",
            "rule_id": rule_id,
            "update_type": update_type,
            "timestamp": datetime.utcnow(),
        })

    def record_reflection(
        self,
        reflection: str,
        outcome: str,
    ) -> None:
        """Record a reflection on execution."""
        self._learning_events.append({
            "type": "reflection",
            "reflection": reflection,
            "outcome": outcome,
            "timestamp": datetime.utcnow(),
        })

    def record_maturity_update(
        self,
        concept_id: str,
        old_maturity: int,
        new_maturity: int,
    ) -> None:
        """Record a maturity level update."""
        self._learning_events.append({
            "type": "maturity_update",
            "concept_id": concept_id,
            "old_maturity": old_maturity,
            "new_maturity": new_maturity,
            "timestamp": datetime.utcnow(),
        })

    def get_learning_history(self) -> List[Dict[str, Any]]:
        """Return the learning history."""
        return self._learning_events.copy()

    def get_recent_learning(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Return learning events from the last N hours."""
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return [
            event
            for event in self._learning_events
            if event["timestamp"] >= cutoff
        ]
