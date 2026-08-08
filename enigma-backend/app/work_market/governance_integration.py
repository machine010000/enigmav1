from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.knowledge_governance import (
    CandidateKnowledge,
    GovernedKnowledge,
    KnowledgeGovernanceService,
    GovernanceEvent,
    KnowledgeConflict,
)
from app.work_market.research_executor import ResearchExecutionResult


@dataclass
class GovernanceSubmissionResult:
    """Result of submitting candidate knowledge to governance."""
    candidate_id: str
    governed_knowledge: Optional[GovernedKnowledge] = None
    success: bool = False
    validation_passed: bool = False
    conflicts_detected: List[KnowledgeConflict] = field(default_factory=list)
    governance_events: List[GovernanceEvent] = field(default_factory=list)
    error_message: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GovernanceIntegrationResult:
    """Result of governance integration for a research execution."""
    job_id: str
    domain_id: str
    total_candidates: int
    successful_submissions: int
    failed_submissions: int
    governed_knowledge: List[GovernedKnowledge] = field(default_factory=list)
    submission_results: List[GovernanceSubmissionResult] = field(default_factory=list)
    all_conflicts: List[KnowledgeConflict] = field(default_factory=list)
    all_governance_events: List[GovernanceEvent] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GovernanceIntegration:
    """
    Integrates research results with Knowledge Governance.
    
    Takes CandidateKnowledge from research execution and submits it
    through the Knowledge Governance pipeline to produce GovernedKnowledge.
    
    This ensures ALL research results go through governance before being
    considered trusted knowledge. No bypass is allowed.
    """

    def __init__(self, governance_service: Optional[KnowledgeGovernanceService] = None) -> None:
        self._governance_service = governance_service

    async def integrate_research_results(
        self,
        research_result: ResearchExecutionResult,
    ) -> GovernanceIntegrationResult:
        """
        Integrate research results with knowledge governance.
        
        Args:
            research_result: Result from research execution with candidate knowledge
            
        Returns:
            GovernanceIntegrationResult with governed knowledge and submission status
        """
        if self._governance_service is None:
            # Governance service not available - return failure
            return GovernanceIntegrationResult(
                job_id=research_result.job_id,
                domain_id=research_result.domain_id,
                total_candidates=len(research_result.all_candidate_knowledge),
                successful_submissions=0,
                failed_submissions=len(research_result.all_candidate_knowledge),
                metadata={
                    "error": "Governance service not available",
                    "note": "Research results cannot be trusted without governance",
                },
            )
        
        submission_results: List[GovernanceSubmissionResult] = []
        governed_knowledge: List[GovernedKnowledge] = []
        all_conflicts: List[KnowledgeConflict] = []
        all_governance_events: List[GovernanceEvent] = []
        
        successful_count = 0
        failed_count = 0
        
        for candidate in research_result.all_candidate_knowledge:
            try:
                submission_result = await self._submit_candidate(candidate, research_result.job_id)
                submission_results.append(submission_result)
                
                if submission_result.success:
                    successful_count += 1
                    if submission_result.governed_knowledge:
                        governed_knowledge.append(submission_result.governed_knowledge)
                else:
                    failed_count += 1
                
                all_conflicts.extend(submission_result.conflicts_detected)
                all_governance_events.extend(submission_result.governance_events)
                
            except Exception as e:
                submission_results.append(
                    GovernanceSubmissionResult(
                        candidate_id=candidate.id,
                        success=False,
                        error_message=str(e),
                    )
                )
                failed_count += 1
        
        return GovernanceIntegrationResult(
            job_id=research_result.job_id,
            domain_id=research_result.domain_id,
            total_candidates=len(research_result.all_candidate_knowledge),
            successful_submissions=successful_count,
            failed_submissions=failed_count,
            governed_knowledge=governed_knowledge,
            submission_results=submission_results,
            all_conflicts=all_conflicts,
            all_governance_events=all_governance_events,
            metadata={
                "plan_id": research_result.plan_id,
                "research_duration_seconds": research_result.total_duration_seconds,
            },
        )

    async def _submit_candidate(
        self,
        candidate: CandidateKnowledge,
        job_id: str,
    ) -> GovernanceSubmissionResult:
        """
        Submit a single candidate to governance.
        
        Args:
            candidate: The candidate knowledge to submit
            job_id: The job identifier for provenance
            
        Returns:
            GovernanceSubmissionResult with submission outcome
        """
        if self._governance_service is None:
            return GovernanceSubmissionResult(
                candidate_id=candidate.id,
                success=False,
                error_message="Governance service not available",
            )
        
        try:
            # Submit through governance pipeline
            governed = self._governance_service.submit_candidate(
                candidate,
                actor=f"job_research_engine_{job_id}",
            )
            
            # Get governance history for audit trail
            governance_events = self._governance_service.get_governance_history(governed.name)
            
            return GovernanceSubmissionResult(
                candidate_id=candidate.id,
                governed_knowledge=governed,
                success=True,
                validation_passed=True,
                governance_events=governance_events,
            )
            
        except Exception as e:
            return GovernanceSubmissionResult(
                candidate_id=candidate.id,
                success=False,
                error_message=str(e),
            )

    def get_governed_knowledge_for_job(
        self,
        job_id: str,
        domain_id: str,
    ) -> List[GovernedKnowledge]:
        """
        Retrieve all governed knowledge relevant to a job.
        
        Args:
            job_id: The job identifier
            domain_id: The domain identifier
            
        Returns:
            List of governed knowledge for the job
        """
        if self._governance_service is None:
            return []
        
        # Get all governed knowledge for the domain
        all_governed = self._governance_service.list_governed_knowledge(status="published")
        
        # Filter by domain (stored in metadata)
        relevant = [
            k for k in all_governed
            if k.metadata.get("domain_id") == domain_id
        ]
        
        return relevant

    def verify_no_governance_bypass(
        self,
        research_result: ResearchExecutionResult,
        governance_result: GovernanceIntegrationResult,
    ) -> bool:
        """
        Verify that no governance bypass occurred.
        
        This is a security check to ensure all candidate knowledge
        went through governance before being used.
        
        Args:
            research_result: The research execution result
            governance_result: The governance integration result
            
        Returns:
            True if no bypass detected, False otherwise
        """
        # Check that all candidates were submitted
        if research_result.total_tasks != governance_result.total_candidates:
            return False
        
        # Check that all submissions have governance events
        for submission in governance_result.submission_results:
            if submission.success and not submission.governance_events:
                return False
        
        # Check that no candidate has governed knowledge without governance events
        for submission in governance_result.submission_results:
            if submission.governed_knowledge and not submission.validation_passed:
                return False
        
        return True
