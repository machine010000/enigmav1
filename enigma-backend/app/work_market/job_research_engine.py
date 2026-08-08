from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.work_market.models import FreelanceJob
from app.work_market.job_intake_orchestrator import JobIntakeResult
from app.work_market.knowledge_gap_analysis import (
    KnowledgeGapAnalyzer,
    KnowledgeGapAnalysisResult,
)
from app.work_market.evidence_gap_analysis import (
    EvidenceGapAnalyzer,
    EvidenceGapAnalysisResult,
)
from app.work_market.research_plan_generator import (
    ResearchPlanGenerator,
    ResearchPlan,
)
from app.work_market.research_executor import (
    ResearchExecutor,
    ResearchExecutionResult,
)
from app.work_market.governance_integration import (
    GovernanceIntegration,
    GovernanceIntegrationResult,
)
from app.work_market.readiness_recalculation import (
    ReadinessRecalculator,
    ReadinessRecalculationResult,
)
from app.knowledge_governance import GovernedKnowledge, KnowledgeGovernanceService
from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.job_readiness import JobReadinessResult
from app.work_market.job_analyzer import JobAnalysisResult


class ResearchEngineStatus(str, Enum):
    """Status of the research engine."""
    IDLE = "idle"
    ANALYZING_GAPS = "analyzing_gaps"
    GENERATING_PLAN = "generating_plan"
    EXECUTING_RESEARCH = "executing_research"
    INTEGRATING_GOVERNANCE = "integrating_governance"
    RECALCULATING_READINESS = "recalculating_readiness"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobResearchEngineResult:
    """Result of the job research engine."""
    job_id: str
    domain_id: str
    status: ResearchEngineStatus
    initial_recommendation: Optional[str] = None
    final_recommendation: Optional[str] = None
    knowledge_gap_analysis: Optional[KnowledgeGapAnalysisResult] = None
    evidence_gap_analysis: Optional[EvidenceGapAnalysisResult] = None
    research_plan: Optional[ResearchPlan] = None
    research_execution: Optional[ResearchExecutionResult] = None
    governance_integration: Optional[GovernanceIntegrationResult] = None
    readiness_recalculation: Optional[ReadinessRecalculationResult] = None
    governed_knowledge: List[GovernedKnowledge] = field(default_factory=list)
    readiness_summary: Dict[str, Any] = field(default_factory=dict)
    governance_bypass_detected: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobResearchEngine:
    """
    Orchestrates the complete job research and readiness engine.
    
    Pipeline:
    Normalized Job → Required Capabilities → Knowledge Gap Analysis → 
    Evidence Gap Analysis → Research Plan → Research Execution → 
    Candidate Knowledge → Knowledge Governance → Governed Knowledge → 
    Evidence Update → Readiness Recalculation → Final Recommendation
    
    Ensures all research results go through governance before being used.
    No governance bypass is allowed.
    """

    def __init__(
        self,
        knowledge_gap_analyzer: Optional[KnowledgeGapAnalyzer] = None,
        evidence_gap_analyzer: Optional[EvidenceGapAnalyzer] = None,
        research_plan_generator: Optional[ResearchPlanGenerator] = None,
        research_executor: Optional[ResearchExecutor] = None,
        governance_integration: Optional[GovernanceIntegration] = None,
        readiness_recalculator: Optional[ReadinessRecalculator] = None,
    ) -> None:
        self._knowledge_gap_analyzer = knowledge_gap_analyzer or KnowledgeGapAnalyzer()
        self._evidence_gap_analyzer = evidence_gap_analyzer or EvidenceGapAnalyzer()
        self._research_plan_generator = research_plan_generator or ResearchPlanGenerator()
        self._research_executor = research_executor or ResearchExecutor()
        self._governance_integration = governance_integration or GovernanceIntegration()
        self._readiness_recalculator = readiness_recalculator or ReadinessRecalculator()

    async def research_and_update_readiness(
        self,
        job_intake_result: JobIntakeResult,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        available_knowledge: List[GovernedKnowledge],
    ) -> JobResearchEngineResult:
        """
        Execute the complete research and readiness update pipeline.
        
        Args:
            job_intake_result: Result from job intake with initial assessment
            work_spec: Work specification for the job
            job_analysis: Job analysis result
            available_knowledge: Currently available governed knowledge
            
        Returns:
            JobResearchEngineResult with complete pipeline results
        """
        started_at = datetime.utcnow()
        job_id = job_intake_result.job_id
        domain_id = job_intake_result.profession or "seo"
        
        result = JobResearchEngineResult(
            job_id=job_id,
            domain_id=domain_id,
            status=ResearchEngineStatus.ANALYZING_GAPS,
            initial_recommendation=job_intake_result.recommendation.value if job_intake_result.recommendation else None,
        )
        
        try:
            # Step 1: Analyze knowledge gaps
            result.status = ResearchEngineStatus.ANALYZING_GAPS
            knowledge_gap_analysis = self._knowledge_gap_analyzer.analyze_gaps(
                job_id=job_id,
                domain_id=domain_id,
                required_knowledge=job_intake_result.required_capabilities,
                available_knowledge=available_knowledge,
            )
            result.knowledge_gap_analysis = knowledge_gap_analysis
            
            # Step 2: Analyze evidence gaps
            evidence_gap_analysis = self._evidence_gap_analyzer.analyze_gaps(
                job_id=job_id,
                domain_id=domain_id,
                required_evidence=job_intake_result.required_capabilities,
                available_knowledge=available_knowledge,
            )
            result.evidence_gap_analysis = evidence_gap_analysis
            
            # Step 3: Generate research plan
            result.status = ResearchEngineStatus.GENERATING_PLAN
            research_plan = self._research_plan_generator.generate_plan(
                job_id=job_id,
                domain_id=domain_id,
                knowledge_gap_analysis=knowledge_gap_analysis,
                evidence_gap_analysis=evidence_gap_analysis,
            )
            research_plan = self._research_plan_generator.prioritize_tasks(research_plan)
            result.research_plan = research_plan
            
            # Skip research if no gaps
            if research_plan.total_tasks == 0:
                result.status = ResearchEngineStatus.COMPLETED
                result.final_recommendation = result.initial_recommendation
                result.completed_at = datetime.utcnow()
                result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
                result.warnings.append("No gaps detected - no research needed")
                return result
            
            # Step 4: Execute research
            result.status = ResearchEngineStatus.EXECUTING_RESEARCH
            research_execution = await self._research_executor.execute_plan(research_plan)
            result.research_execution = research_execution
            
            # Step 5: Integrate with governance
            result.status = ResearchEngineStatus.INTEGRATING_GOVERNANCE
            governance_integration = await self._governance_integration.integrate_research_results(
                research_execution,
            )
            result.governance_integration = governance_integration
            result.governed_knowledge = governance_integration.governed_knowledge
            
            # Verify no governance bypass
            governance_bypass_detected = not self._governance_integration.verify_no_governance_bypass(
                research_execution,
                governance_integration,
            )
            result.governance_bypass_detected = governance_bypass_detected
            
            if governance_bypass_detected:
                result.errors.append("GOVERNANCE BYPASS DETECTED - Research results may not be trusted")
                result.status = ResearchEngineStatus.FAILED
                result.completed_at = datetime.utcnow()
                result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
                return result
            
            # Step 6: Recalculate readiness
            result.status = ResearchEngineStatus.RECALCULATING_READINESS
            readiness_recalculation = self._readiness_recalculator.recalculate_readiness(
                job_id=job_id,
                domain_id=domain_id,
                work_spec=work_spec,
                job_analysis=job_analysis,
                previous_readiness=job_intake_result.readiness_assessment,
                new_governed_knowledge=governance_integration.governed_knowledge,
                previous_recommendation=result.initial_recommendation,
            )
            result.readiness_recalculation = readiness_recalculation
            
            # Get readiness summary
            readiness_summary = self._readiness_recalculator.get_readiness_summary(
                readiness_recalculation,
            )
            result.readiness_summary = readiness_summary
            result.final_recommendation = readiness_recalculation.new_recommendation
            
            # Complete
            result.status = ResearchEngineStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
            
        except Exception as e:
            result.status = ResearchEngineStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
        
        return result

    def get_final_status(self, result: JobResearchEngineResult) -> str:
        """
        Get the final status (READY or NOT_READY) with details.
        
        Args:
            result: The research engine result
            
        Returns:
            "READY" or "NOT_READY"
        """
        if result.status != ResearchEngineStatus.COMPLETED:
            return "NOT_READY"
        
        if result.readiness_recalculation and result.readiness_recalculation.now_ready:
            return "READY"
        
        return "NOT_READY"

    def get_detailed_report(self, result: JobResearchEngineResult) -> Dict[str, Any]:
        """
        Get a detailed report of the research and readiness process.
        
        Args:
            result: The research engine result
            
        Returns:
            Dictionary with detailed report
        """
        report = {
            "job_id": result.job_id,
            "domain_id": result.domain_id,
            "status": result.status.value,
            "final_status": self.get_final_status(result),
            "initial_recommendation": result.initial_recommendation,
            "final_recommendation": result.final_recommendation,
            "duration_seconds": result.total_duration_seconds,
            "governance_bypass_detected": result.governance_bypass_detected,
        }
        
        if result.knowledge_gap_analysis:
            report["knowledge_gaps"] = {
                "total": result.knowledge_gap_analysis.total_gaps,
                "critical": result.knowledge_gap_analysis.critical_gaps,
                "high": result.knowledge_gap_analysis.high_gaps,
                "medium": result.knowledge_gap_analysis.medium_gaps,
                "low": result.knowledge_gap_analysis.low_gaps,
            }
        
        if result.evidence_gap_analysis:
            report["evidence_gaps"] = {
                "total": result.evidence_gap_analysis.total_gaps,
                "critical": result.evidence_gap_analysis.critical_gaps,
                "high": result.evidence_gap_analysis.high_gaps,
                "medium": result.evidence_gap_analysis.medium_gaps,
                "low": result.evidence_gap_analysis.low_gaps,
            }
        
        if result.research_plan:
            report["research_plan"] = {
                "total_tasks": result.research_plan.total_tasks,
                "critical_tasks": result.research_plan.critical_tasks,
                "high_tasks": result.research_plan.high_tasks,
                "estimated_hours": result.research_plan.estimated_total_hours,
            }
        
        if result.research_execution:
            report["research_execution"] = {
                "total_tasks": result.research_execution.total_tasks,
                "completed_tasks": result.research_execution.completed_tasks,
                "failed_tasks": result.research_execution.failed_tasks,
                "status": result.research_execution.status.value,
            }
        
        if result.governance_integration:
            report["governance_integration"] = {
                "total_candidates": result.governance_integration.total_candidates,
                "successful_submissions": result.governance_integration.successful_submissions,
                "failed_submissions": result.governance_integration.failed_submissions,
                "governed_knowledge_count": len(result.governance_integration.governed_knowledge),
            }
        
        if result.readiness_recalculation:
            report["readiness_recalculation"] = {
                "previous_readiness": result.readiness_recalculation.previous_readiness.overall_readiness.overall_readiness if result.readiness_recalculation.previous_readiness else None,
                "new_readiness": result.readiness_recalculation.new_readiness.overall_readiness.overall_readiness,
                "readiness_improved": result.readiness_recalculation.readiness_improved,
                "improvement_delta": result.readiness_recalculation.overall_delta,
                "now_ready": result.readiness_recalculation.now_ready,
            }
        
        report["readiness_summary"] = result.readiness_summary
        
        if result.errors:
            report["errors"] = result.errors
        
        if result.warnings:
            report["warnings"] = result.warnings
        
        return report


# Global instance
job_research_engine = JobResearchEngine()
