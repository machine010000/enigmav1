from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.work_market.models import FreelanceJob, JobSource, JobRecommendation
from app.work_market.job_classifier import SEOJobClassifier
from app.work_market.job_analyzer import SEOJobAnalyzer
from app.work_market.job_readiness import SEOJobReadinessCalculator, JobReadinessResult
from app.expert_domains.contracts import ReadinessScore
from app.expert_domains.work.work_specification import WorkSpecification


@dataclass
class JobIntakeResult:
    """Result of job intake and normalization."""
    job_id: str
    intake_status: str  # "success", "failed", "partial"
    normalized_job: Optional[FreelanceJob] = None
    profession: Optional[str] = None
    task_type: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    readiness_assessment: Optional[JobReadinessResult] = None
    execution_capability: Optional[Dict[str, Any]] = None
    recommendation: Optional[JobRecommendation] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.utcnow)


class JobIntakeOrchestrator:
    """
    Orchestrates the complete job intake and normalization pipeline.
    
    Pipeline:
    External Job → Intake → Normalize → Classify → Extract Capabilities → 
    Assess Readiness → Evaluate Execution Capability → Recommendation
    """

    def __init__(self) -> None:
        self._job_classifier = SEOJobClassifier()
        self._job_analyzer = SEOJobAnalyzer()
        self._job_readiness_calculator = SEOJobReadinessCalculator()
        self._job_gap_analyzer = None  # Not used in current implementation

    def ingest_job(
        self,
        raw_job_data: Dict[str, Any],
        source: JobSource = JobSource.OTHER,
    ) -> JobIntakeResult:
        """
        Ingest a raw job from external source and process through the pipeline.
        
        Args:
            raw_job_data: Raw job data from external source
            source: Source of the job
            
        Returns:
            JobIntakeResult with complete analysis
        """
        result = JobIntakeResult(
            job_id=raw_job_data.get("job_id", f"job_{uuid.uuid4().hex[:8]}"),
            intake_status="in_progress",
        )

        try:
            # Step 1: Normalize job data
            normalized_job = self._normalize_job(raw_job_data, source)
            result.normalized_job = normalized_job

            # Step 2: Classify job (profession, task type)
            classification_result = self._job_classifier.classify(normalized_job)
            classification = {
                "profession": classification_result.category.value,
                "task_type": classification_result.category.value,
                "domain_id": "seo",
                "task_id": classification_result.category.value,
            }
            result.profession = classification.get("profession")
            result.task_type = classification.get("task_type")

            # Step 3: Analyze job requirements
            work_spec = self._create_work_specification(normalized_job, classification, [])
            analysis = self._job_analyzer.analyze(normalized_job, work_spec)
            
            # Step 4: Extract required capabilities
            required_capabilities = self._extract_capabilities(normalized_job, classification)
            result.required_capabilities = required_capabilities

            # Step 5: Assess readiness
            work_spec = self._create_work_specification(normalized_job, classification, required_capabilities)
            domain_readiness = self._get_domain_readiness(classification.get("domain_id", "seo"))
            
            readiness_result = self._job_readiness_calculator.calculate_readiness(
                work_spec=work_spec,
                job_analysis=analysis,
                domain_readiness=domain_readiness,
            )
            result.readiness_assessment = readiness_result

            # Step 6: Evaluate execution capability
            execution_capability = self._evaluate_execution_capability(
                normalized_job,
                classification,
                required_capabilities,
                readiness_result,
            )
            result.execution_capability = execution_capability

            # Step 7: Generate recommendation
            recommendation = self._generate_recommendation(
                readiness_result,
                execution_capability,
                analysis,
            )
            result.recommendation = recommendation

            result.intake_status = "success"

        except Exception as e:
            result.intake_status = "failed"
            result.errors.append(f"Job intake failed: {str(e)}")

        return result

    def _normalize_job(
        self,
        raw_job_data: Dict[str, Any],
        source: JobSource,
    ) -> FreelanceJob:
        """Normalize raw job data to FreelanceJob contract."""
        job_id = raw_job_data.get("job_id", f"job_{uuid.uuid4().hex[:8]}")
        title = raw_job_data.get("title", "Untitled Job")
        description = raw_job_data.get("description", "")
        budget = raw_job_data.get("budget")
        currency = raw_job_data.get("currency", "USD")
        deadline_str = raw_job_data.get("deadline")
        skills = raw_job_data.get("skills", [])
        source_url = raw_job_data.get("source_url", "")
        client_info = raw_job_data.get("client_information", {})

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except (ValueError, TypeError):
                pass

        return FreelanceJob(
            job_id=job_id,
            source=source,
            title=title,
            description=description,
            client_information=client_info,
            budget=budget,
            currency=currency,
            deadline=deadline,
            skills=skills,
            source_url=source_url,
            discovered_at=datetime.utcnow(),
            normalized_at=datetime.utcnow(),
            metadata={"raw_data": raw_job_data},
        )

    def _extract_capabilities(
        self,
        job: FreelanceJob,
        classification: Dict[str, Any],
    ) -> List[str]:
        """Extract required capabilities from job."""
        capabilities = []
        
        # Add skills as capabilities
        capabilities.extend(job.skills)
        
        # Add profession-specific capabilities
        profession = classification.get("profession")
        if profession:
            capabilities.append(f"{profession}_expertise")
        
        # Add task-specific capabilities
        task_type = classification.get("task_type")
        if task_type:
            capabilities.append(f"{task_type}_execution")
        
        return list(set(capabilities))

    def _create_work_specification(
        self,
        job: FreelanceJob,
        classification: Dict[str, Any],
        required_capabilities: List[str],
    ) -> WorkSpecification:
        """Create work specification from job."""
        return WorkSpecification(
            work_id=f"work_{uuid.uuid4().hex[:8]}",
            title=job.title,
            description=job.description,
            business_goal=classification.get("task_type", "general_task"),
            business_context=f"Freelance job from {job.source.value}",
            industry="general",
            target_audience="client",
            expected_outcome=self._extract_deliverables(job)[0] if self._extract_deliverables(job) else "completed_work",
            constraints=self._extract_constraints(job),
            required_capabilities=required_capabilities,
            required_tasks=[classification.get("task_type", "general_task")],
        )

    def _extract_deliverables(self, job: FreelanceJob) -> List[str]:
        """Extract deliverables from job description."""
        # Simple extraction - in production would use NLP
        deliverables = []
        description_lower = job.description.lower()
        
        if "report" in description_lower:
            deliverables.append("comprehensive_report")
        if "audit" in description_lower:
            deliverables.append("audit_report")
        if "analysis" in description_lower:
            deliverables.append("analysis_document")
        if "implementation" in description_lower:
            deliverables.append("implementation_plan")
        if "optimization" in description_lower:
            deliverables.append("optimization_results")
        
        return deliverables if deliverables else ["standard_deliverables"]

    def _extract_acceptance_criteria(self, job: FreelanceJob) -> List[str]:
        """Extract acceptance criteria from job."""
        criteria = []
        
        if job.budget:
            criteria.append(f"within_budget_{job.currency}")
        if job.deadline:
            criteria.append("delivered_by_deadline")
        
        criteria.extend([f"skill_{skill}" for skill in job.skills])
        
        return criteria if criteria else ["meets_requirements"]

    def _extract_success_metrics(self, job: FreelanceJob) -> Dict[str, Any]:
        """Extract success metrics from job."""
        metrics = {
            "client_satisfaction": "high",
            "quality_score": ">= 0.8",
        }
        
        if job.budget:
            metrics["cost_efficiency"] = "within_budget"
        
        return metrics

    def _extract_constraints(self, job: FreelanceJob) -> Dict[str, Any]:
        """Extract constraints from job."""
        constraints = {}
        
        if job.budget:
            constraints["max_budget"] = job.budget
            constraints["currency"] = job.currency
        
        if job.deadline:
            constraints["deadline"] = job.deadline
        
        return constraints

    def _estimate_duration(self, job: FreelanceJob) -> Optional[float]:
        """Estimate duration in hours based on job complexity."""
        # Simple estimation based on description length and budget
        description_length = len(job.description)
        budget = job.budget or 0
        
        if budget > 1000:
            return 40.0
        elif budget > 500:
            return 20.0
        elif budget > 100:
            return 10.0
        elif description_length > 500:
            return 8.0
        else:
            return 4.0

    def _get_domain_readiness(self, domain_id: str) -> ReadinessScore:
        """Get domain readiness score."""
        # In production, would fetch from actual domain
        return ReadinessScore(
            domain_id=domain_id,
            knowledge_readiness=0.8,
            execution_readiness=0.7,
            evidence_readiness=0.75,
            learning_readiness=0.8,
            overall_readiness=0.75,
        )

    def _evaluate_execution_capability(
        self,
        job: FreelanceJob,
        classification: Dict[str, Any],
        required_capabilities: List[str],
        readiness_result: JobReadinessResult,
    ) -> Dict[str, Any]:
        """Evaluate execution capability for the job."""
        return {
            "can_execute": readiness_result.overall_readiness.overall_readiness >= 0.6,
            "confidence": readiness_result.confidence,
            "missing_capabilities": readiness_result.capability_readiness.missing_capabilities,
            "resource_availability": readiness_result.execution_readiness.resource_availability,
            "execution_complexity": readiness_result.execution_readiness.execution_complexity,
            "estimated_success_probability": readiness_result.overall_readiness.overall_readiness,
            "requires_learning": len(readiness_result.knowledge_readiness.missing_knowledge) > 0,
            "requires_research": len(readiness_result.evidence_readiness.missing_evidence) > 0,
            "blockers": readiness_result.blockers,
            "risks": readiness_result.risks,
        }

    def _generate_recommendation(
        self,
        readiness_result: JobReadinessResult,
        execution_capability: Dict[str, Any],
        analysis: Any,
    ) -> JobRecommendation:
        """Generate recommendation based on assessment."""
        overall_score = readiness_result.overall_readiness.overall_readiness
        
        if execution_capability["blockers"]:
            return JobRecommendation.REJECT
        
        if execution_capability["requires_learning"]:
            return JobRecommendation.LEARN_FIRST
        
        if execution_capability["requires_research"]:
            return JobRecommendation.RESEARCH_FIRST
        
        if overall_score >= 0.8:
            return JobRecommendation.APPLY
        
        if overall_score >= 0.6:
            return JobRecommendation.APPLY
        
        return JobRecommendation.REJECT


# Default instance
job_intake_orchestrator = JobIntakeOrchestrator()
