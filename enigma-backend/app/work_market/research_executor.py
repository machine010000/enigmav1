from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.research_service import ResearchService, ResearchReport
from app.knowledge_governance import CandidateKnowledge, Evidence, SourceType
from app.work_market.research_plan_generator import ResearchPlan, ResearchTask, ResearchTaskType


class ResearchExecutionStatus(str, Enum):
    """Status of research execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class ResearchTaskResult:
    """Result of executing a single research task."""
    task_id: str
    status: ResearchExecutionStatus
    queries_executed: List[str] = field(default_factory=list)
    search_results: List[ResearchReport] = field(default_factory=list)
    candidate_knowledge: Optional[CandidateKnowledge] = None
    error_message: Optional[str] = None
    executed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchExecutionResult:
    """Result of executing a research plan."""
    plan_id: str
    job_id: str
    domain_id: str
    status: ResearchExecutionStatus
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    task_results: List[ResearchTaskResult] = field(default_factory=list)
    all_candidate_knowledge: List[CandidateKnowledge] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResearchExecutor:
    """
    Executes research plans using the existing ResearchService.
    
    Takes a ResearchPlan and executes each research task, converting
    results into CandidateKnowledge for governance processing.
    """

    def __init__(self, research_service: Optional[ResearchService] = None) -> None:
        self._research_service = research_service or ResearchService()

    async def execute_plan(self, plan: ResearchPlan) -> ResearchExecutionResult:
        """
        Execute a research plan.
        
        Args:
            plan: The research plan to execute
            
        Returns:
            ResearchExecutionResult with task results and candidate knowledge
        """
        started_at = datetime.utcnow()
        task_results: List[ResearchTaskResult] = []
        all_candidate_knowledge: List[CandidateKnowledge] = []
        
        completed_count = 0
        failed_count = 0
        
        for task in plan.research_tasks:
            task_result = await self._execute_task(task, plan.job_id, plan.domain_id)
            task_results.append(task_result)
            
            if task_result.status == ResearchExecutionStatus.COMPLETED:
                completed_count += 1
                if task_result.candidate_knowledge:
                    all_candidate_knowledge.append(task_result.candidate_knowledge)
            elif task_result.status == ResearchExecutionStatus.FAILED:
                failed_count += 1
        
        completed_at = datetime.utcnow()
        total_duration = (completed_at - started_at).total_seconds()
        
        # Determine overall status
        if failed_count == 0:
            overall_status = ResearchExecutionStatus.COMPLETED
        elif completed_count == 0:
            overall_status = ResearchExecutionStatus.FAILED
        else:
            overall_status = ResearchExecutionStatus.PARTIALLY_COMPLETED
        
        return ResearchExecutionResult(
            plan_id=plan.plan_id,
            job_id=plan.job_id,
            domain_id=plan.domain_id,
            status=overall_status,
            total_tasks=plan.total_tasks,
            completed_tasks=completed_count,
            failed_tasks=failed_count,
            task_results=task_results,
            all_candidate_knowledge=all_candidate_knowledge,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_seconds=total_duration,
        )

    async def _execute_task(
        self,
        task: ResearchTask,
        job_id: str,
        domain_id: str,
    ) -> ResearchTaskResult:
        """
        Execute a single research task.
        
        Args:
            task: The research task to execute
            job_id: The job identifier
            domain_id: The domain identifier
            
        Returns:
            ResearchTaskResult with execution results
        """
        try:
            if task.task_type == ResearchTaskType.KNOWLEDGE_RESEARCH:
                return await self._execute_knowledge_research(task, job_id, domain_id)
            elif task.task_type == ResearchTaskType.EVIDENCE_RESEARCH:
                return await self._execute_evidence_research(task, job_id, domain_id)
            elif task.task_type == ResearchTaskType.PRACTICE_TASK:
                return await self._execute_practice_task(task, job_id, domain_id)
            else:
                return ResearchTaskResult(
                    task_id=task.task_id,
                    status=ResearchExecutionStatus.FAILED,
                    error_message=f"Unknown task type: {task.task_type}",
                )
        except Exception as e:
            return ResearchTaskResult(
                task_id=task.task_id,
                status=ResearchExecutionStatus.FAILED,
                error_message=str(e),
            )

    async def _execute_knowledge_research(
        self,
        task: ResearchTask,
        job_id: str,
        domain_id: str,
    ) -> ResearchTaskResult:
        """Execute a knowledge research task."""
        search_results: List[ResearchReport] = []
        queries_executed: List[str] = []
        
        for query in task.queries:
            report = await self._research_service.web_search(query, max_results=10)
            search_results.append(report)
            queries_executed.append(query)
        
        # Convert to CandidateKnowledge
        candidate_knowledge = self._convert_to_candidate_knowledge(
            task,
            search_results,
            job_id,
            domain_id,
        )
        
        return ResearchTaskResult(
            task_id=task.task_id,
            status=ResearchExecutionStatus.COMPLETED,
            queries_executed=queries_executed,
            search_results=search_results,
            candidate_knowledge=candidate_knowledge,
            metadata={"task_type": "knowledge_research"},
        )

    async def _execute_evidence_research(
        self,
        task: ResearchTask,
        job_id: str,
        domain_id: str,
    ) -> ResearchTaskResult:
        """Execute an evidence research task."""
        search_results: List[ResearchReport] = []
        queries_executed: List[str] = []
        
        for query in task.queries:
            report = await self._research_service.knowledge_search(query, max_results=10)
            search_results.append(report)
            queries_executed.append(query)
        
        # Convert to CandidateKnowledge (evidence-focused)
        candidate_knowledge = self._convert_to_candidate_knowledge(
            task,
            search_results,
            job_id,
            domain_id,
        )
        
        return ResearchTaskResult(
            task_id=task.task_id,
            status=ResearchExecutionStatus.COMPLETED,
            queries_executed=queries_executed,
            search_results=search_results,
            candidate_knowledge=candidate_knowledge,
            metadata={"task_type": "evidence_research"},
        )

    async def _execute_practice_task(
        self,
        task: ResearchTask,
        job_id: str,
        domain_id: str,
    ) -> ResearchTaskResult:
        """Execute a practice task."""
        # Practice tasks are not executed by research service
        # They would be executed by domain-specific workers
        # For now, we return a placeholder result
        
        return ResearchTaskResult(
            task_id=task.task_id,
            status=ResearchExecutionStatus.COMPLETED,
            queries_executed=[],
            search_results=[],
            candidate_knowledge=None,
            metadata={
                "task_type": "practice_task",
                "note": "Practice tasks require domain-specific execution",
            },
        )

    def _convert_to_candidate_knowledge(
        self,
        task: ResearchTask,
        search_results: List[ResearchReport],
        job_id: str,
        domain_id: str,
    ) -> Optional[CandidateKnowledge]:
        """Convert research results to CandidateKnowledge."""
        if not search_results:
            return None
        
        # Collect all evidence from search results
        all_evidence: List[Evidence] = []
        
        for report in search_results:
            candidate = report.to_candidate_knowledge()
            if candidate and candidate.evidence:
                all_evidence.extend(candidate.evidence)
        
        if not all_evidence:
            return None
        
        # Create CandidateKnowledge
        return CandidateKnowledge(
            id=f"candidate_{task.task_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=task.target_concept,
            definition=f"Research findings for {task.target_concept} from job {job_id}",
            evidence=all_evidence,
            source=f"research_executor_{domain_id}",
            submitted_at=datetime.utcnow(),
            metadata={
                "job_id": job_id,
                "domain_id": domain_id,
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "queries": task.queries,
            },
        )
