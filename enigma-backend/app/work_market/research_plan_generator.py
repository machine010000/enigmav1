from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.work_market.knowledge_gap_analysis import KnowledgeGap, KnowledgeGapAnalysisResult, GapSeverity
from app.work_market.evidence_gap_analysis import EvidenceGap, EvidenceGapAnalysisResult, EvidenceGapSeverity


class ResearchTaskType(str, Enum):
    """Types of research tasks."""
    KNOWLEDGE_RESEARCH = "knowledge_research"
    EVIDENCE_RESEARCH = "evidence_research"
    PRACTICE_TASK = "practice_task"
    VALIDATION_TASK = "validation_task"


class ResearchPriority(str, Enum):
    """Priority levels for research tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ResearchTask:
    """A single research task in the plan."""
    task_id: str
    task_type: ResearchTaskType
    priority: ResearchPriority
    description: str
    queries: List[str]
    target_concept: str
    expected_outcome: str
    estimated_duration_hours: float
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchPlan:
    """Comprehensive research plan for resolving knowledge and evidence gaps."""
    plan_id: str
    job_id: str
    domain_id: str
    knowledge_gaps: List[KnowledgeGap] = field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = field(default_factory=list)
    research_tasks: List[ResearchTask] = field(default_factory=list)
    total_tasks: int = 0
    critical_tasks: int = 0
    high_tasks: int = 0
    medium_tasks: int = 0
    low_tasks: int = 0
    estimated_total_hours: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResearchPlanGenerator:
    """
    Generates research plans to resolve knowledge and evidence gaps.
    
    Takes gap analysis results and creates structured research tasks
    with priorities, dependencies, and time estimates.
    """

    def __init__(self) -> None:
        self._severity_to_priority = {
            GapSeverity.CRITICAL: ResearchPriority.CRITICAL,
            GapSeverity.HIGH: ResearchPriority.HIGH,
            GapSeverity.MEDIUM: ResearchPriority.MEDIUM,
            GapSeverity.LOW: ResearchPriority.LOW,
            EvidenceGapSeverity.CRITICAL: ResearchPriority.CRITICAL,
            EvidenceGapSeverity.HIGH: ResearchPriority.HIGH,
            EvidenceGapSeverity.MEDIUM: ResearchPriority.MEDIUM,
            EvidenceGapSeverity.LOW: ResearchPriority.LOW,
        }

    def generate_plan(
        self,
        job_id: str,
        domain_id: str,
        knowledge_gap_analysis: KnowledgeGapAnalysisResult,
        evidence_gap_analysis: EvidenceGapAnalysisResult,
    ) -> ResearchPlan:
        """
        Generate a comprehensive research plan from gap analyses.
        
        Args:
            job_id: The job identifier
            domain_id: The domain identifier
            knowledge_gap_analysis: Result from knowledge gap analysis
            evidence_gap_analysis: Result from evidence gap analysis
            
        Returns:
            ResearchPlan with structured research tasks
        """
        plan_id = f"plan_{job_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        research_tasks: List[ResearchTask] = []
        
        # Generate tasks for knowledge gaps
        for gap in knowledge_gap_analysis.gaps:
            tasks = self._generate_knowledge_gap_tasks(gap)
            research_tasks.extend(tasks)
        
        # Generate tasks for evidence gaps
        for gap in evidence_gap_analysis.gaps:
            tasks = self._generate_evidence_gap_tasks(gap)
            research_tasks.extend(tasks)
        
        # Calculate statistics
        critical_count = sum(1 for t in research_tasks if t.priority == ResearchPriority.CRITICAL)
        high_count = sum(1 for t in research_tasks if t.priority == ResearchPriority.HIGH)
        medium_count = sum(1 for t in research_tasks if t.priority == ResearchPriority.MEDIUM)
        low_count = sum(1 for t in research_tasks if t.priority == ResearchPriority.LOW)
        
        total_hours = sum(t.estimated_duration_hours for t in research_tasks)
        
        return ResearchPlan(
            plan_id=plan_id,
            job_id=job_id,
            domain_id=domain_id,
            knowledge_gaps=knowledge_gap_analysis.gaps,
            evidence_gaps=evidence_gap_analysis.gaps,
            research_tasks=research_tasks,
            total_tasks=len(research_tasks),
            critical_tasks=critical_count,
            high_tasks=high_count,
            medium_tasks=medium_count,
            low_tasks=low_count,
            estimated_total_hours=total_hours,
        )

    def _generate_knowledge_gap_tasks(self, gap: KnowledgeGap) -> List[ResearchTask]:
        """Generate research tasks for a knowledge gap."""
        tasks: List[ResearchTask] = []
        priority = self._severity_to_priority[gap.severity]
        
        # Primary research task
        task = ResearchTask(
            task_id=f"task_knowledge_{gap.gap_id}",
            task_type=ResearchTaskType.KNOWLEDGE_RESEARCH,
            priority=priority,
            description=f"Research and acquire knowledge for: {gap.concept_name}",
            queries=gap.suggested_research_queries,
            target_concept=gap.concept_id,
            expected_outcome=f"Governed knowledge for {gap.concept_name} with maturity {gap.required_maturity.value}",
            estimated_duration_hours=self._estimate_duration_for_gap(gap.severity),
            metadata={"gap_type": "knowledge", "gap_id": gap.gap_id},
        )
        tasks.append(task)
        
        # Add practice task if maturity gap is significant
        if gap.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]:
            practice_task = ResearchTask(
                task_id=f"task_practice_{gap.gap_id}",
                task_type=ResearchTaskType.PRACTICE_TASK,
                priority=priority,
                description=f"Practice applying knowledge for: {gap.concept_name}",
                queries=gap.suggested_practice_tasks,
                target_concept=gap.concept_id,
                expected_outcome=f"Practical experience with {gap.concept_name}",
                estimated_duration_hours=task.estimated_duration_hours * 0.5,
                dependencies=[task.task_id],
                metadata={"gap_type": "practice", "gap_id": gap.gap_id},
            )
            tasks.append(practice_task)
        
        return tasks

    def _generate_evidence_gap_tasks(self, gap: EvidenceGap) -> List[ResearchTask]:
        """Generate research tasks for an evidence gap."""
        tasks: List[ResearchTask] = []
        priority = self._severity_to_priority[gap.severity]
        
        # Evidence research task
        task = ResearchTask(
            task_id=f"task_evidence_{gap.gap_id}",
            task_type=ResearchTaskType.EVIDENCE_RESEARCH,
            priority=priority,
            description=f"Research and collect evidence for: {gap.concept_name}",
            queries=gap.suggested_research_queries,
            target_concept=gap.concept_id,
            expected_outcome=f"High-quality evidence for {gap.concept_name} meeting quality threshold {gap.quality_threshold}",
            estimated_duration_hours=self._estimate_duration_for_gap(gap.severity),
            metadata={"gap_type": "evidence", "gap_id": gap.gap_id},
        )
        tasks.append(task)
        
        return tasks

    def _estimate_duration_for_gap(self, severity: Any) -> float:
        """Estimate research duration based on gap severity."""
        if severity in [GapSeverity.CRITICAL, EvidenceGapSeverity.CRITICAL]:
            return 8.0  # 8 hours for critical gaps
        elif severity in [GapSeverity.HIGH, EvidenceGapSeverity.HIGH]:
            return 4.0  # 4 hours for high gaps
        elif severity in [GapSeverity.MEDIUM, EvidenceGapSeverity.MEDIUM]:
            return 2.0  # 2 hours for medium gaps
        else:
            return 1.0  # 1 hour for low gaps

    def prioritize_tasks(self, plan: ResearchPlan) -> ResearchPlan:
        """Reorder research tasks by priority and dependencies."""
        # Sort by priority (critical first), then by dependencies
        priority_order = {
            ResearchPriority.CRITICAL: 0,
            ResearchPriority.HIGH: 1,
            ResearchPriority.MEDIUM: 2,
            ResearchPriority.LOW: 3,
        }
        
        # Create a map of tasks for dependency resolution
        task_map = {t.task_id: t for t in plan.research_tasks}
        
        # Topological sort based on dependencies
        sorted_tasks: List[ResearchTask] = []
        remaining = set(plan.research_tasks)
        
        while remaining:
            # Find tasks with no unsatisfied dependencies
            ready = [
                t for t in remaining
                if all(dep in task_map and task_map[dep] not in remaining for dep in t.dependencies)
            ]
            
            if not ready:
                # Circular dependency or missing dependency - break with remaining
                ready = list(remaining)
            
            # Sort ready tasks by priority
            ready.sort(key=lambda t: priority_order[t.priority])
            
            for task in ready:
                sorted_tasks.append(task)
                remaining.remove(task)
        
        plan.research_tasks = sorted_tasks
        return plan
