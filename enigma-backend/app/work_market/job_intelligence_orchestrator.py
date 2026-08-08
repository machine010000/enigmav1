from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.expert_domains.contracts import ReadinessScore
from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.models import FreelanceJob
from app.work_market.job_classifier import JobClassificationOrchestrator, JobClassificationResult
from app.work_market.job_mapper import JobMappingOrchestrator, CapabilityMappingResult, TaskMappingResult
from app.work_market.job_analyzer import JobAnalysisOrchestrator, JobAnalysisResult
from app.work_market.job_readiness import JobReadinessOrchestrator, JobReadinessResult
from app.work_market.job_recommendation import JobRecommendationOrchestrator, JobRecommendationResult
from app.work_market.job_gap_analysis import JobGapAnalysisOrchestrator, GapAnalysisResult
from app.work_market.job_proposal_context import ProposalContextOrchestrator, ProposalContextResult
from app.work_market.expert_domain_adapter import ExpertDomainAdapter


@dataclass
class JobIntelligenceResult:
    """Complete job intelligence result."""
    job_id: str
    classification: JobClassificationResult
    work_specification: WorkSpecification
    capability_mapping: CapabilityMappingResult
    task_mapping: TaskMappingResult
    analysis: JobAnalysisResult
    readiness: JobReadinessResult
    recommendation: JobRecommendationResult
    gap_analysis: GapAnalysisResult
    proposal_context: ProposalContextResult
    processing_time_seconds: float = 0.0
    processed_at: datetime = field(default_factory=datetime.utcnow)


class JobIntelligenceOrchestrator:
    """
    Orchestrates complete job intelligence pipeline.

    Integrates:
    - Job Classification
    - Capability Mapping
    - Task Mapping
    - Job Analysis
    - Readiness Calculation
    - Recommendation Generation
    - Gap Analysis
    - Proposal Context Generation

    All components integrate with SEO Expert, Decision Layer, and existing contracts.
    """

    def __init__(self) -> None:
        self._classifier = JobClassificationOrchestrator()
        self._mapper = JobMappingOrchestrator()
        self._analyzer = JobAnalysisOrchestrator()
        self._readiness_calculator = JobReadinessOrchestrator()
        self._recommender = JobRecommendationOrchestrator()
        self._gap_analyzer = JobGapAnalysisOrchestrator()
        self._proposal_context_generator = ProposalContextOrchestrator()
        self._domain_adapter = ExpertDomainAdapter()

    def process_job(self, job: FreelanceJob) -> JobIntelligenceResult:
        """
        Process a marketplace job through complete intelligence pipeline.

        Pipeline:
        1. Classify job into SEO category
        2. Create WorkSpecification
        3. Map capabilities and tasks
        4. Analyze job comprehensively
        5. Calculate readiness from SEO Expert
        6. Generate recommendation
        7. Analyze gaps
        8. Generate proposal context

        Returns complete job intelligence.
        """
        start_time = datetime.utcnow()
        
        # Step 1: Classify job
        classification = self._classifier.classify_job(job)
        
        # Step 2: Create WorkSpecification
        work_spec = self._classifier.create_work_specification(job, classification)
        
        # Step 3: Map capabilities and tasks
        capability_mapping, task_mapping = self._mapper.map_work_specification(work_spec)
        
        # Step 4: Update WorkSpecification with mappings
        work_spec = self._mapper.update_work_specification(
            work_spec,
            capability_mapping,
            task_mapping,
        )
        
        # Step 5: Analyze job
        analysis = self._analyzer.analyze_job(job, work_spec)
        
        # Step 6: Get domain readiness from SEO Expert
        domain_readiness = self._get_domain_readiness()
        
        # Step 7: Calculate job readiness
        readiness = self._readiness_calculator.calculate_readiness(
            work_spec,
            analysis,
            domain_readiness,
        )
        
        # Step 8: Generate recommendation
        recommendation = self._recommender.recommend_job(
            job,
            work_spec,
            analysis,
            readiness,
        )
        
        # Step 9: Analyze gaps
        gap_analysis = self._gap_analyzer.analyze_gaps(
            work_spec,
            analysis,
            readiness,
        )
        
        # Step 10: Generate proposal context
        proposal_context = self._proposal_context_generator.generate_proposal_context(
            job,
            work_spec,
            analysis,
            readiness,
            gap_analysis,
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return JobIntelligenceResult(
            job_id=job.job_id,
            classification=classification,
            work_specification=work_spec,
            capability_mapping=capability_mapping,
            task_mapping=task_mapping,
            analysis=analysis,
            readiness=readiness,
            recommendation=recommendation,
            gap_analysis=gap_analysis,
            proposal_context=proposal_context,
            processing_time_seconds=processing_time,
        )

    def _get_domain_readiness(self) -> ReadinessScore:
        """Get readiness from SEO Expert Domain."""
        # Use adapter to get readiness
        return self._domain_adapter.get_domain_readiness()

    def process_job_batch(self, jobs: List[FreelanceJob]) -> List[JobIntelligenceResult]:
        """Process multiple jobs in batch."""
        results = []
        
        for job in jobs:
            result = self.process_job(job)
            results.append(result)
        
        return results

    def get_decision_context(self, intelligence: JobIntelligenceResult) -> Dict[str, Any]:
        """
        Get decision context for Decision Layer.

        Provides complete context for decision-making.
        """
        return {
            "job_id": intelligence.job_id,
            "recommendation": intelligence.recommendation.recommendation.value,
            "confidence": intelligence.recommendation.confidence,
            "reasoning": intelligence.recommendation.reasoning,
            "readiness": {
                "overall": intelligence.readiness.overall_readiness.overall_readiness,
                "knowledge": intelligence.readiness.knowledge_readiness.knowledge_coverage,
                "evidence": intelligence.readiness.evidence_readiness.evidence_coverage,
                "capability": intelligence.readiness.capability_readiness.capability_coverage,
                "execution": intelligence.readiness.execution_readiness.execution_coverage,
            },
            "risk": {
                "level": intelligence.analysis.risk_analysis.overall_risk.value,
                "technical_risks": intelligence.analysis.risk_analysis.technical_risks,
                "client_risks": intelligence.analysis.risk_analysis.client_risks,
            },
            "value": {
                "score": intelligence.recommendation.value_score,
                "budget": intelligence.analysis.budget_analysis.budget_adequacy,
                "timeline": intelligence.analysis.timeline_analysis.deadline_feasibility,
            },
            "gaps": {
                "total": intelligence.gap_analysis.total_gaps,
                "critical": intelligence.gap_analysis.critical_gaps,
                "high": intelligence.gap_analysis.high_gaps,
                "closure_time": intelligence.gap_analysis.estimated_closure_time,
            },
            "conditions": [
                {
                    "type": c.condition_type,
                    "description": c.description,
                    "required_action": c.required_action,
                    "impact": c.impact,
                }
                for c in intelligence.recommendation.conditions
            ],
            "success_probability": intelligence.recommendation.success_probability,
        }

    def get_proposal_context(self, intelligence: JobIntelligenceResult) -> Dict[str, Any]:
        """
        Get proposal context for proposal generation.

        Provides structured context for creating proposals.
        """
        return {
            "client_goals": {
                "primary": intelligence.proposal_context.client_goals.primary_goal,
                "secondary": intelligence.proposal_context.client_goals.secondary_goals,
                "success_metrics": intelligence.proposal_context.client_goals.success_metrics,
                "timeline": intelligence.proposal_context.client_goals.timeline_expectations,
                "budget": intelligence.proposal_context.client_goals.budget_expectations,
            },
            "deliverables": {
                "primary": intelligence.proposal_context.deliverables.primary_deliverables,
                "secondary": intelligence.proposal_context.deliverables.secondary_deliverables,
                "formats": intelligence.proposal_context.deliverables.deliverable_formats,
                "phases": intelligence.proposal_context.deliverables.delivery_phases,
            },
            "timeline": {
                "duration": intelligence.proposal_context.timeline.estimated_duration,
                "milestones": intelligence.proposal_context.timeline.key_milestones,
                "critical_path": intelligence.proposal_context.timeline.critical_path,
                "buffer": intelligence.proposal_context.timeline.buffer_time,
            },
            "scope": {
                "in_scope": intelligence.proposal_context.scope.in_scope,
                "out_of_scope": intelligence.proposal_context.scope.out_of_scope,
                "assumptions": intelligence.proposal_context.scope.assumptions,
                "constraints": intelligence.proposal_context.scope.constraints,
            },
            "risks": {
                "identified": intelligence.proposal_context.risks.identified_risks,
                "mitigation": intelligence.proposal_context.risks.risk_mitigation,
                "contingency": intelligence.proposal_context.risks.contingency_plans,
                "level": intelligence.proposal_context.risks.risk_level,
            },
            "value": {
                "business_value": intelligence.proposal_context.value.business_value,
                "roi": intelligence.proposal_context.value.roi_projection,
                "competitive_advantages": intelligence.proposal_context.value.competitive_advantages,
                "unique_selling_points": intelligence.proposal_context.value.unique_selling_points,
            },
            "pricing": intelligence.proposal_context.pricing_context,
            "terms": intelligence.proposal_context.terms_context,
            "communication": intelligence.proposal_context.communication_context,
        }

    def get_learning_context(self, intelligence: JobIntelligenceResult) -> Dict[str, Any]:
        """
        Get learning context for SEO Expert learning.

        Provides context for triggering learning activities.
        """
        return {
            "knowledge_gaps": [
                {
                    "area": gap.knowledge_area,
                    "severity": gap.severity.value,
                    "remediation": gap.remediation,
                    "sources": gap.sources_to_consult,
                }
                for gap in intelligence.gap_analysis.knowledge_gaps
            ],
            "evidence_gaps": [
                {
                    "type": gap.evidence_type,
                    "severity": gap.severity.value,
                    "remediation": gap.remediation,
                    "sources": gap.potential_sources,
                }
                for gap in intelligence.gap_analysis.evidence_gaps
            ],
            "research_requirements": intelligence.recommendation.research_requirements,
            "learning_requirements": intelligence.recommendation.learning_requirements,
            "category": intelligence.classification.category.value,
            "confidence": intelligence.classification.confidence,
        }


# Global instance for job intelligence
job_intelligence_orchestrator = JobIntelligenceOrchestrator()
