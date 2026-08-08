from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.work_market.proposal_strategy import (
    ProposalStrategyGenerator,
    ProposalStrategy,
    ProposalStrategyResult,
)
from app.work_market.knowledge_selector import (
    RelevantKnowledgeSelector,
    KnowledgeSelectionResult,
)
from app.work_market.proposal_generator import (
    ProposalGenerator,
    ProposalGenerationResult,
)
from app.work_market.application_package import (
    ApplicationPackageBuilder,
    ApplicationPackage,
    ApplicationPackageResult,
    ApplicationStatus,
    ApprovalDecision,
)


class ProposalEngineStatus(str, Enum):
    """Status of the proposal engine."""
    IDLE = "idle"
    GENERATING_STRATEGY = "generating_strategy"
    SELECTING_KNOWLEDGE = "selecting_knowledge"
    GENERATING_PROPOSAL = "generating_proposal"
    BUILDING_PACKAGE = "building_package"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProposalEngineResult:
    """Result of the proposal engine."""
    job_id: str
    status: ProposalEngineStatus
    strategy_result: Optional[ProposalStrategyResult] = None
    knowledge_selection: Optional[KnowledgeSelectionResult] = None
    proposal_generation: Optional[ProposalGenerationResult] = None
    package_result: Optional[ApplicationPackageResult] = None
    application_package: Optional[ApplicationPackage] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProposalEngine:
    """
    Orchestrates the proposal and application package generation.
    
    Pipeline:
    READY Job → Proposal Strategy → Knowledge Selection → 
    Proposal Generation → Application Package → WAITING_FOR_APPROVAL
    
    Ensures all claims are evidence-backed and no fabricated
    information is included.
    """

    def __init__(
        self,
        strategy_generator: Optional[ProposalStrategyGenerator] = None,
        knowledge_selector: Optional[RelevantKnowledgeSelector] = None,
        proposal_generator: Optional[ProposalGenerator] = None,
        package_builder: Optional[ApplicationPackageBuilder] = None,
    ) -> None:
        self._strategy_generator = strategy_generator or ProposalStrategyGenerator()
        self._knowledge_selector = knowledge_selector or RelevantKnowledgeSelector()
        self._proposal_generator = proposal_generator or ProposalGenerator()
        self._package_builder = package_builder or ApplicationPackageBuilder()

    def generate_application(
        self,
        job_id: str,
        job_description: str,
        required_capabilities: List[str],
        available_capabilities: List[str],
        available_evidence: Dict[str, List[str]],  # capability_id -> evidence_ids
        governed_knowledge: List[Any],
        evidence_map: Dict[str, Any],  # evidence_id -> evidence object
        readiness_score: float,
    ) -> ProposalEngineResult:
        """
        Generate a complete application package for a job.
        
        Args:
            job_id: The job identifier
            job_description: The job description
            required_capabilities: Required capabilities for the job
            available_capabilities: Available capabilities
            available_evidence: Mapping of capabilities to evidence
            governed_knowledge: Available governed knowledge
            evidence_map: Mapping of evidence IDs to evidence objects
            readiness_score: The readiness score
            
        Returns:
            ProposalEngineResult with the application package
        """
        started_at = datetime.utcnow()
        
        result = ProposalEngineResult(
            job_id=job_id,
            status=ProposalEngineStatus.GENERATING_STRATEGY,
        )
        
        try:
            # Step 1: Generate proposal strategy
            result.status = ProposalEngineStatus.GENERATING_STRATEGY
            strategy_result = self._strategy_generator.generate_strategy(
                job_id=job_id,
                job_description=job_description,
                available_capabilities=available_capabilities,
                available_evidence=available_evidence,
                governed_knowledge=governed_knowledge,
            )
            result.strategy_result = strategy_result
            
            if not strategy_result.success:
                result.status = ProposalEngineStatus.FAILED
                result.errors = strategy_result.errors
                result.warnings = strategy_result.warnings
                result.completed_at = datetime.utcnow()
                result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
                return result
            
            # Step 2: Select relevant knowledge
            result.status = ProposalEngineStatus.SELECTING_KNOWLEDGE
            knowledge_selection = self._knowledge_selector.select_knowledge(
                job_id=job_id,
                job_description=job_description,
                required_capabilities=required_capabilities,
                governed_knowledge=governed_knowledge,
            )
            result.knowledge_selection = knowledge_selection
            
            # Step 3: Generate proposal
            result.status = ProposalEngineStatus.GENERATING_PROPOSAL
            proposal_generation = self._proposal_generator.generate_proposal(
                job_id=job_id,
                strategy=strategy_result.strategy,
                knowledge_selections=knowledge_selection.selections,
            )
            result.proposal_generation = proposal_generation
            
            if not proposal_generation.success:
                result.status = ProposalEngineStatus.FAILED
                result.errors = proposal_generation.errors
                result.completed_at = datetime.utcnow()
                result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
                return result
            
            # Step 4: Build application package
            result.status = ProposalEngineStatus.BUILDING_PACKAGE
            package_result = self._package_builder.build_package(
                job_id=job_id,
                strategy=strategy_result.strategy,
                governed_knowledge=governed_knowledge,
                evidence_map=evidence_map,
                readiness_score=readiness_score,
            )
            result.package_result = package_result
            result.application_package = package_result.package
            
            if not package_result.success:
                result.status = ProposalEngineStatus.FAILED
                result.errors = package_result.errors
                result.warnings = package_result.warnings
                result.completed_at = datetime.utcnow()
                result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
                return result
            
            # Complete
            result.status = ProposalEngineStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
            result.metadata = {
                "strategy_id": strategy_result.strategy.strategy_id,
                "application_id": package_result.package.application_id,
                "knowledge_selected": knowledge_selection.total_selected,
                "proposal_sections": len(proposal_generation.generated.proposal.sections),
                "confidence_score": strategy_result.strategy.confidence_score,
            }
            
        except Exception as e:
            result.status = ProposalEngineStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            result.total_duration_seconds = (result.completed_at - started_at).total_seconds()
        
        return result

    def approve_application(
        self,
        package: ApplicationPackage,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """Approve an application package."""
        return self._package_builder.approve_application(
            package,
            approved_by=approved_by,
            notes=notes,
        )

    def reject_application(
        self,
        package: ApplicationPackage,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """Reject an application package."""
        return self._package_builder.reject_application(
            package,
            approved_by=approved_by,
            notes=notes,
        )

    def request_revision(
        self,
        package: ApplicationPackage,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """Request revision of an application package."""
        return self._package_builder.request_revision(
            package,
            approved_by=approved_by,
            notes=notes,
        )

    def get_application_summary(self, package: ApplicationPackage) -> Dict[str, Any]:
        """
        Get a summary of the application package.
        
        Args:
            package: The application package
            
        Returns:
            Dictionary with summary information
        """
        return {
            "application_id": package.application_id,
            "job_id": package.job_id,
            "status": package.status.value,
            "approval_decision": package.approval_decision.value,
            "readiness_score": package.readiness_score,
            "proposal_confidence": package.proposal.confidence_score,
            "capability_claims": len(package.proposal.relevant_capabilities),
            "deliverables": len(package.proposal.deliverables),
            "risks": len(package.proposal.risks),
            "assumptions": len(package.proposal.assumptions),
            "client_questions": len(package.proposal.client_questions),
            "knowledge_used": len(package.knowledge_used),
            "created_at": package.created_at.isoformat(),
            "updated_at": package.updated_at.isoformat(),
            "approved_at": package.approved_at.isoformat() if package.approved_at else None,
            "approved_by": package.approved_by,
            "approval_notes": package.approval_notes,
        }


# Global instance
proposal_engine = ProposalEngine()
