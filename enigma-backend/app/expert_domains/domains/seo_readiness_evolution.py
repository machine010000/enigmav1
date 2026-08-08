from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import ReadinessScore
from app.knowledge_governance.models import KnowledgeMaturity, KnowledgeFreshness


class ExecutionResult(str, Enum):
    """Result of a task execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    ERROR = "error"


@dataclass
class ExecutionRecord:
    """Record of a task execution for readiness tracking."""
    execution_id: str
    task_id: str
    result: ExecutionResult
    duration_seconds: float
    quality_score: float  # 0.0 to 1.0
    completed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceImpact:
    """Impact of evidence on readiness."""
    evidence_id: str
    concept_id: str
    quality_score: float
    maturity_impact: float
    readiness_delta: float  # -1.0 to 1.0
    applied_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeImpact:
    """Impact of knowledge changes on readiness."""
    knowledge_id: str
    change_type: str  # new, updated, deprecated
    previous_maturity: Optional[KnowledgeMaturity]
    new_maturity: Optional[KnowledgeMaturity]
    readiness_delta: float  # -1.0 to 1.0
    applied_at: datetime = field(default_factory=datetime.utcnow)


class SEOKnowledgeReadinessEvolution:
    """
    Manages SEO readiness evolution based on executions and evidence.

    Readiness changes according to:
    - Successful executions
    - Failed executions
    - Validated evidence
    - New knowledge
    - Outdated knowledge
    """

    def __init__(self, domain_id: str, initial_readiness: Optional[ReadinessScore] = None) -> None:
        self.domain_id = domain_id
        self._current_readiness = initial_readiness or ReadinessScore(
            domain_id=domain_id,
            knowledge_readiness=0.5,
            execution_readiness=0.5,
            evidence_readiness=0.5,
            learning_readiness=0.5,
            overall_readiness=0.5,
        )
        
        self._execution_history: List[ExecutionRecord] = []
        self._evidence_impacts: List[EvidenceImpact] = []
        self._knowledge_impacts: List[KnowledgeImpact] = []
        
        # Readiness evolution parameters
        self._execution_success_weight = 0.05  # Impact of successful execution
        self._execution_failure_weight = -0.03  # Impact of failed execution
        self._evidence_quality_weight = 0.02  # Impact of high-quality evidence
        self._knowledge_maturity_weight = 0.03  # Impact of knowledge maturity increase
        self._decay_rate = 0.01  # Readiness decay per day without activity

    def record_execution(
        self,
        execution_id: str,
        task_id: str,
        result: ExecutionResult,
        duration_seconds: float,
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReadinessScore:
        """
        Record a task execution and update readiness.

        Readiness impact:
        - Success: Increases execution readiness
        - Failure: Decreases execution readiness
        - Quality score: Modifies impact magnitude
        """
        record = ExecutionRecord(
            execution_id=execution_id,
            task_id=task_id,
            result=result,
            duration_seconds=duration_seconds,
            quality_score=quality_score,
            metadata=metadata or {},
        )
        
        self._execution_history.append(record)
        
        # Update readiness based on execution
        self._update_readiness_from_execution(record)
        
        return self._current_readiness

    def apply_evidence_impact(
        self,
        evidence_id: str,
        concept_id: str,
        quality_score: float,
        maturity_impact: float,
    ) -> ReadinessScore:
        """
        Apply evidence impact to readiness.

        High-quality evidence increases evidence readiness.
        Maturity impact affects knowledge readiness.
        """
        impact = EvidenceImpact(
            evidence_id=evidence_id,
            concept_id=concept_id,
            quality_score=quality_score,
            maturity_impact=maturity_impact,
            readiness_delta=self._calculate_evidence_readiness_delta(quality_score),
        )
        
        self._evidence_impacts.append(impact)
        
        # Update readiness based on evidence
        self._update_readiness_from_evidence(impact)
        
        return self._current_readiness

    def apply_knowledge_impact(
        self,
        knowledge_id: str,
        change_type: str,
        previous_maturity: Optional[KnowledgeMaturity],
        new_maturity: Optional[KnowledgeMaturity],
    ) -> ReadinessScore:
        """
        Apply knowledge impact to readiness.

        Knowledge maturity changes affect knowledge readiness.
        """
        impact = KnowledgeImpact(
            knowledge_id=knowledge_id,
            change_type=change_type,
            previous_maturity=previous_maturity,
            new_maturity=new_maturity,
            readiness_delta=self._calculate_knowledge_readiness_delta(
                previous_maturity, new_maturity
            ),
        )
        
        self._knowledge_impacts.append(impact)
        
        # Update readiness based on knowledge
        self._update_readiness_from_knowledge(impact)
        
        return self._current_readiness

    def decay_readiness(self, days: int = 1) -> ReadinessScore:
        """
        Apply readiness decay for inactivity.

        Readiness naturally decays over time without activity.
        """
        decay_amount = self._decay_rate * days
        
        self._current_readiness = ReadinessScore(
            domain_id=self.domain_id,
            knowledge_readiness=max(0.0, self._current_readiness.knowledge_readiness - decay_amount),
            execution_readiness=max(0.0, self._current_readiness.execution_readiness - decay_amount),
            evidence_readiness=max(0.0, self._current_readiness.evidence_readiness - decay_amount),
            learning_readiness=max(0.0, self._current_readiness.learning_readiness - decay_amount),
            overall_readiness=0.0,  # Will be recalculated
        )
        
        # Recalculate overall readiness
        self._recalculate_overall_readiness()
        
        return self._current_readiness

    def get_current_readiness(self) -> ReadinessScore:
        """Get the current readiness score."""
        return self._current_readiness

    def get_execution_history(self, limit: int = 100) -> List[ExecutionRecord]:
        """Get recent execution history."""
        return self._execution_history[-limit:]

    def get_evidence_impacts(self, limit: int = 100) -> List[EvidenceImpact]:
        """Get recent evidence impacts."""
        return self._evidence_impacts[-limit:]

    def get_knowledge_impacts(self, limit: int = 100) -> List[KnowledgeImpact]:
        """Get recent knowledge impacts."""
        return self._knowledge_impacts[-limit:]

    def get_readiness_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        Get readiness trend over time.

        Returns statistics about readiness changes.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent_executions = [
            e for e in self._execution_history
            if e.completed_at >= cutoff
        ]
        
        recent_evidence = [
            e for e in self._evidence_impacts
            if e.applied_at >= cutoff
        ]
        
        recent_knowledge = [
            k for k in self._knowledge_impacts
            if k.applied_at >= cutoff
        ]
        
        # Calculate trends
        success_rate = 0.0
        if recent_executions:
            successes = sum(1 for e in recent_executions if e.result == ExecutionResult.SUCCESS)
            success_rate = successes / len(recent_executions)
        
        avg_quality = 0.0
        if recent_executions:
            avg_quality = sum(e.quality_score for e in recent_executions) / len(recent_executions)
        
        total_evidence_impact = sum(e.readiness_delta for e in recent_evidence)
        total_knowledge_impact = sum(k.readiness_delta for k in recent_knowledge)
        
        return {
            "period_days": days,
            "execution_count": len(recent_executions),
            "success_rate": success_rate,
            "average_quality": avg_quality,
            "evidence_impacts": len(recent_evidence),
            "total_evidence_impact": total_evidence_impact,
            "knowledge_impacts": len(recent_knowledge),
            "total_knowledge_impact": total_knowledge_impact,
            "current_readiness": self._current_readiness.overall_readiness,
        }

    def _update_readiness_from_execution(self, record: ExecutionRecord) -> None:
        """Update readiness based on execution result."""
        if record.result == ExecutionResult.SUCCESS:
            # Success increases execution readiness
            delta = self._execution_success_weight * record.quality_score
            self._current_readiness = ReadinessScore(
                domain_id=self.domain_id,
                knowledge_readiness=self._current_readiness.knowledge_readiness,
                execution_readiness=min(1.0, self._current_readiness.execution_readiness + delta),
                evidence_readiness=self._current_readiness.evidence_readiness,
                learning_readiness=min(1.0, self._current_readiness.learning_readiness + delta * 0.5),
                overall_readiness=0.0,  # Will be recalculated
            )
        elif record.result == ExecutionResult.FAILURE or record.result == ExecutionResult.ERROR:
            # Failure decreases execution readiness
            delta = self._execution_failure_weight * (1.0 - record.quality_score)
            self._current_readiness = ReadinessScore(
                domain_id=self.domain_id,
                knowledge_readiness=self._current_readiness.knowledge_readiness,
                execution_readiness=max(0.0, self._current_readiness.execution_readiness + delta),
                evidence_readiness=self._current_readiness.evidence_readiness,
                learning_readiness=max(0.0, self._current_readiness.learning_readiness + delta * 0.5),
                overall_readiness=0.0,  # Will be recalculated
            )
        elif record.result == ExecutionResult.PARTIAL_SUCCESS:
            # Partial success has small positive impact
            delta = self._execution_success_weight * record.quality_score * 0.5
            self._current_readiness = ReadinessScore(
                domain_id=self.domain_id,
                knowledge_readiness=self._current_readiness.knowledge_readiness,
                execution_readiness=min(1.0, self._current_readiness.execution_readiness + delta),
                evidence_readiness=self._current_readiness.evidence_readiness,
                learning_readiness=min(1.0, self._current_readiness.learning_readiness + delta * 0.5),
                overall_readiness=0.0,  # Will be recalculated
            )
        
        self._recalculate_overall_readiness()

    def _update_readiness_from_evidence(self, impact: EvidenceImpact) -> None:
        """Update readiness based on evidence impact."""
        # Evidence quality affects evidence readiness
        delta = self._evidence_quality_weight * impact.quality_score
        
        self._current_readiness = ReadinessScore(
            domain_id=self.domain_id,
            knowledge_readiness=self._current_readiness.knowledge_readiness,
            execution_readiness=self._current_readiness.execution_readiness,
            evidence_readiness=min(1.0, self._current_readiness.evidence_readiness + delta),
            learning_readiness=self._current_readiness.learning_readiness,
            overall_readiness=0.0,  # Will be recalculated
        )
        
        # Maturity impact affects knowledge readiness
        if impact.maturity_impact > 0:
            self._current_readiness = ReadinessScore(
                domain_id=self.domain_id,
                knowledge_readiness=min(1.0, self._current_readiness.knowledge_readiness + impact.maturity_impact * 0.1),
                execution_readiness=self._current_readiness.execution_readiness,
                evidence_readiness=self._current_readiness.evidence_readiness,
                learning_readiness=self._current_readiness.learning_readiness,
                overall_readiness=0.0,  # Will be recalculated
            )
        
        self._recalculate_overall_readiness()

    def _update_readiness_from_knowledge(self, impact: KnowledgeImpact) -> None:
        """Update readiness based on knowledge impact."""
        # Knowledge maturity changes affect knowledge readiness
        delta = self._knowledge_maturity_weight * impact.readiness_delta
        
        self._current_readiness = ReadinessScore(
            domain_id=self.domain_id,
            knowledge_readiness=min(1.0, max(0.0, self._current_readiness.knowledge_readiness + delta)),
            execution_readiness=self._current_readiness.execution_readiness,
            evidence_readiness=self._current_readiness.evidence_readiness,
            learning_readiness=min(1.0, self._current_readiness.learning_readiness + delta * 0.5),
            overall_readiness=0.0,  # Will be recalculated
        )
        
        self._recalculate_overall_readiness()

    def _calculate_evidence_readiness_delta(self, quality_score: float) -> float:
        """Calculate readiness delta from evidence quality."""
        return quality_score * self._evidence_quality_weight

    def _calculate_knowledge_readiness_delta(
        self,
        previous_maturity: Optional[KnowledgeMaturity],
        new_maturity: Optional[KnowledgeMaturity],
    ) -> float:
        """Calculate readiness delta from knowledge maturity change."""
        if not previous_maturity or not new_maturity:
            return 0.0
        
        maturity_change = new_maturity.value - previous_maturity.value
        return maturity_change * self._knowledge_maturity_weight

    def _recalculate_overall_readiness(self) -> None:
        """Recalculate overall readiness from components."""
        weights = {
            "knowledge": 0.3,
            "execution": 0.3,
            "evidence": 0.2,
            "learning": 0.2,
        }
        
        overall = (
            self._current_readiness.knowledge_readiness * weights["knowledge"]
            + self._current_readiness.execution_readiness * weights["execution"]
            + self._current_readiness.evidence_readiness * weights["evidence"]
            + self._current_readiness.learning_readiness * weights["learning"]
        )
        
        self._current_readiness = ReadinessScore(
            domain_id=self.domain_id,
            knowledge_readiness=self._current_readiness.knowledge_readiness,
            execution_readiness=self._current_readiness.execution_readiness,
            evidence_readiness=self._current_readiness.evidence_readiness,
            learning_readiness=self._current_readiness.learning_readiness,
            overall_readiness=overall,
        )


class SEOKnowledgeReadinessOrchestrator:
    """
    Orchestrates readiness evolution for SEO Expert Domain.

    Provides high-level interface for readiness management.
    """

    def __init__(self, domain_id: str, initial_readiness: Optional[ReadinessScore] = None) -> None:
        self._evolution = SEOKnowledgeReadinessEvolution(domain_id, initial_readiness)

    def record_successful_execution(
        self,
        execution_id: str,
        task_id: str,
        duration_seconds: float,
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReadinessScore:
        """Record a successful execution."""
        return self._evolution.record_execution(
            execution_id=execution_id,
            task_id=task_id,
            result=ExecutionResult.SUCCESS,
            duration_seconds=duration_seconds,
            quality_score=quality_score,
            metadata=metadata,
        )

    def record_failed_execution(
        self,
        execution_id: str,
        task_id: str,
        duration_seconds: float,
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReadinessScore:
        """Record a failed execution."""
        return self._evolution.record_execution(
            execution_id=execution_id,
            task_id=task_id,
            result=ExecutionResult.FAILURE,
            duration_seconds=duration_seconds,
            quality_score=quality_score,
            metadata=metadata,
        )

    def record_partial_success(
        self,
        execution_id: str,
        task_id: str,
        duration_seconds: float,
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReadinessScore:
        """Record a partially successful execution."""
        return self._evolution.record_execution(
            execution_id=execution_id,
            task_id=task_id,
            result=ExecutionResult.PARTIAL_SUCCESS,
            duration_seconds=duration_seconds,
            quality_score=quality_score,
            metadata=metadata,
        )

    def apply_high_quality_evidence(
        self,
        evidence_id: str,
        concept_id: str,
        quality_score: float,
        maturity_impact: float,
    ) -> ReadinessScore:
        """Apply high-quality evidence impact."""
        return self._evolution.apply_evidence_impact(
            evidence_id=evidence_id,
            concept_id=concept_id,
            quality_score=quality_score,
            maturity_impact=maturity_impact,
        )

    def apply_knowledge_increase(
        self,
        knowledge_id: str,
        previous_maturity: KnowledgeMaturity,
        new_maturity: KnowledgeMaturity,
    ) -> ReadinessScore:
        """Apply knowledge maturity increase."""
        return self._evolution.apply_knowledge_impact(
            knowledge_id=knowledge_id,
            change_type="maturity_increase",
            previous_maturity=previous_maturity,
            new_maturity=new_maturity,
        )

    def apply_knowledge_decrease(
        self,
        knowledge_id: str,
        previous_maturity: KnowledgeMaturity,
        new_maturity: KnowledgeMaturity,
    ) -> ReadinessScore:
        """Apply knowledge maturity decrease."""
        return self._evolution.apply_knowledge_impact(
            knowledge_id=knowledge_id,
            change_type="maturity_decrease",
            previous_maturity=previous_maturity,
            new_maturity=new_maturity,
        )

    def get_current_readiness(self) -> ReadinessScore:
        """Get current readiness."""
        return self._evolution.get_current_readiness()

    def get_readiness_trend(self, days: int = 30) -> Dict[str, Any]:
        """Get readiness trend."""
        return self._evolution.get_readiness_trend(days)

    def apply_daily_decay(self) -> ReadinessScore:
        """Apply daily readiness decay."""
        return self._evolution.decay_readiness(days=1)
