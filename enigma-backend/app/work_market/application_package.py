from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.work_market.proposal_strategy import (
    ProposalStrategy,
    CapabilityClaim,
    ClientRequirement,
    Deliverable,
    Risk,
    Assumption,
    ClientQuestion,
)


class ApplicationStatus(str, Enum):
    """Status of an application."""
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"


class ApprovalDecision(str, Enum):
    """Human approval decision."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


@dataclass
class ProposalSection:
    """A section of the proposal."""
    section_id: str
    title: str
    content: str
    order: int = 0


@dataclass
class Proposal:
    """The client-facing proposal."""
    proposal_id: str
    job_id: str
    job_understanding: str
    proposed_approach: str
    relevant_capabilities: List[CapabilityClaim] = field(default_factory=list)
    supporting_evidence: Dict[str, str] = field(default_factory=list)  # evidence_id -> description
    deliverables: List[Deliverable] = field(default_factory=list)
    timeline: str = ""
    budget_proposal: str = ""
    assumptions: List[Assumption] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    client_questions: List[ClientQuestion] = field(default_factory=list)
    sections: List[ProposalSection] = field(default_factory=list)
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApplicationPackage:
    """
    Complete application package for a job.
    
    Contains the proposal, evidence, and all supporting information
    needed for human review and approval.
    """
    application_id: str
    job_id: str
    proposal: Proposal
    strategy: ProposalStrategy
    status: ApplicationStatus = ApplicationStatus.DRAFT
    approval_decision: ApprovalDecision = ApprovalDecision.PENDING
    approval_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    evidence_provenance: Dict[str, str] = field(default_factory=dict)  # evidence_id -> source
    knowledge_used: List[str] = field(default_factory=list)  # knowledge_ids
    readiness_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationPackageResult:
    """Result of application package creation."""
    package: ApplicationPackage
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ApplicationPackageBuilder:
    """
    Builds application packages from proposal strategies.
    
    Ensures all claims are evidence-backed and no fabricated
    information is included.
    """

    def __init__(self) -> None:
        pass

    def build_package(
        self,
        job_id: str,
        strategy: ProposalStrategy,
        governed_knowledge: List[Any],
        evidence_map: Dict[str, Any],  # evidence_id -> evidence object
        readiness_score: float,
    ) -> ApplicationPackageResult:
        """
        Build an application package from a proposal strategy.
        
        Args:
            job_id: The job identifier
            strategy: The proposal strategy
            governed_knowledge: Available governed knowledge
            evidence_map: Mapping of evidence IDs to evidence objects
            readiness_score: The readiness score for this job
            
        Returns:
            ApplicationPackageResult with the package
        """
        application_id = f"app_{job_id}_{datetime.utcnow().timestamp()}"
        
        # Build the proposal
        proposal = self._build_proposal(
            job_id,
            strategy,
            governed_knowledge,
            evidence_map,
        )
        
        # Track evidence provenance
        evidence_provenance = self._track_evidence_provenance(
            strategy.capability_claims,
            evidence_map,
        )
        
        # Track knowledge used
        knowledge_used = self._track_knowledge_used(governed_knowledge)
        
        # Create the package
        package = ApplicationPackage(
            application_id=application_id,
            job_id=job_id,
            proposal=proposal,
            strategy=strategy,
            status=ApplicationStatus.WAITING_FOR_APPROVAL,
            approval_decision=ApprovalDecision.PENDING,
            evidence_provenance=evidence_provenance,
            knowledge_used=knowledge_used,
            readiness_score=readiness_score,
        )
        
        # Validate no fabricated claims
        fabricated_claims = [
            c for c in strategy.capability_claims
            if c.is_fabricated
        ]
        
        if fabricated_claims:
            return ApplicationPackageResult(
                package=package,
                success=False,
                errors=[
                    f"Application contains {len(fabricated_claims)} claims without evidence backing"
                ],
                warnings=[
                    f"Capability '{c.capability_name}' lacks evidence"
                    for c in fabricated_claims
                ],
            )
        
        return ApplicationPackageResult(package=package, success=True)

    def _build_proposal(
        self,
        job_id: str,
        strategy: ProposalStrategy,
        governed_knowledge: List[Any],
        evidence_map: Dict[str, Any],
    ) -> Proposal:
        """Build the client-facing proposal."""
        proposal_id = f"proposal_{job_id}"
        
        # Job understanding
        job_understanding = self._generate_job_understanding(strategy)
        
        # Proposed approach
        proposed_approach = self._generate_proposed_approach(strategy)
        
        # Supporting evidence descriptions
        supporting_evidence = self._generate_evidence_descriptions(
            strategy.capability_claims,
            evidence_map,
        )
        
        # Timeline
        timeline = self._generate_timeline(strategy)
        
        # Budget proposal
        budget_proposal = self._generate_budget_proposal(strategy)
        
        # Proposal sections
        sections = self._generate_proposal_sections(strategy)
        
        return Proposal(
            proposal_id=proposal_id,
            job_id=job_id,
            job_understanding=job_understanding,
            proposed_approach=proposed_approach,
            relevant_capabilities=strategy.capability_claims,
            supporting_evidence=supporting_evidence,
            deliverables=strategy.deliverables,
            timeline=timeline,
            budget_proposal=budget_proposal,
            assumptions=strategy.assumptions,
            risks=strategy.risks,
            client_questions=strategy.client_questions,
            sections=sections,
            confidence_score=strategy.confidence_score,
        )

    def _generate_job_understanding(self, strategy: ProposalStrategy) -> str:
        """Generate the job understanding section."""
        requirements_summary = "\n".join([
            f"- {req.description} ({req.priority})"
            for req in strategy.client_requirements
        ])
        
        return f"""Based on the job requirements, I understand that you need:

{requirements_summary}

This aligns with our capabilities in the relevant domain."""

    def _generate_proposed_approach(self, strategy: ProposalStrategy) -> str:
        """Generate the proposed approach section."""
        approach = f"""Our approach focuses on delivering value through:

1. **Understanding**: Thorough analysis of your requirements
2. **Execution**: Professional delivery of all deliverables
3. **Communication**: Regular updates and feedback loops

Key capabilities we bring:
"""
        
        for claim in strategy.capability_claims:
            approach += f"- {claim.claim}\n"
        
        return approach

    def _generate_evidence_descriptions(
        self,
        capability_claims: List[CapabilityClaim],
        evidence_map: Dict[str, Any],
    ) -> Dict[str, str]:
        """Generate descriptions for supporting evidence."""
        descriptions = {}
        
        for claim in capability_claims:
            for evidence_id in claim.evidence_ids:
                evidence = evidence_map.get(evidence_id)
                if evidence:
                    descriptions[evidence_id] = f"Evidence for {claim.capability_name}"
        
        return descriptions

    def _generate_timeline(self, strategy: ProposalStrategy) -> str:
        """Generate the timeline section."""
        days = strategy.estimated_timeline_days
        if days == 0:
            days = 7  # Default
        
        return f"Estimated timeline: {days} days\n\nThis includes time for:\n- Initial analysis\n- Execution\n- Review and revisions"

    def _generate_budget_proposal(self, strategy: ProposalStrategy) -> str:
        """Generate the budget proposal section."""
        budget = strategy.estimated_budget
        if budget == 0:
            return "Budget to be discussed based on specific requirements"
        
        return f"Estimated budget: ${budget:.2f}\n\nThis is an estimate and may vary based on scope changes."

    def _generate_proposal_sections(self, strategy: ProposalStrategy) -> List[ProposalSection]:
        """Generate structured proposal sections."""
        sections = [
            ProposalSection(
                section_id="understanding",
                title="Job Understanding",
                content="Analysis of requirements and objectives",
                order=1,
            ),
            ProposalSection(
                section_id="approach",
                title="Proposed Approach",
                content="Our methodology and execution plan",
                order=2,
            ),
            ProposalSection(
                section_id="capabilities",
                title="Relevant Capabilities",
                content="Skills and experience relevant to this job",
                order=3,
            ),
            ProposalSection(
                section_id="deliverables",
                title="Deliverables",
                content="What will be delivered",
                order=4,
            ),
            ProposalSection(
                section_id="timeline",
                title="Timeline",
                content="Project schedule and milestones",
                order=5,
            ),
            ProposalSection(
                section_id="risks",
                title="Risks and Mitigations",
                content="Potential risks and how we address them",
                order=6,
            ),
            ProposalSection(
                section_id="questions",
                title="Questions for Client",
                content="Clarifications needed before starting",
                order=7,
            ),
        ]
        
        return sections

    def _track_evidence_provenance(
        self,
        capability_claims: List[CapabilityClaim],
        evidence_map: Dict[str, Any],
    ) -> Dict[str, str]:
        """Track the provenance of all evidence used."""
        provenance = {}
        
        for claim in capability_claims:
            for evidence_id in claim.evidence_ids:
                evidence = evidence_map.get(evidence_id)
                if evidence:
                    provenance[evidence_id] = claim.provenance
        
        return provenance

    def _track_knowledge_used(self, governed_knowledge: List[Any]) -> List[str]:
        """Track the knowledge items used in the proposal."""
        return [
            k.id if hasattr(k, 'id') else str(k)
            for k in governed_knowledge
        ]

    def approve_application(
        self,
        package: ApplicationPackage,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """Approve an application package."""
        package.status = ApplicationStatus.APPROVED
        package.approval_decision = ApprovalDecision.APPROVED
        package.approved_by = approved_by
        package.approval_notes = notes
        package.approved_at = datetime.utcnow()
        package.updated_at = datetime.utcnow()
        
        return package

    def reject_application(
        self,
        package: ApplicationPackage,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """Reject an application package."""
        package.status = ApplicationStatus.REJECTED
        package.approval_decision = ApprovalDecision.REJECTED
        package.approved_by = approved_by
        package.approval_notes = notes
        package.updated_at = datetime.utcnow()
        
        return package

    def request_revision(
        self,
        package: ApplicationPackage,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """Request revision of an application package."""
        package.status = ApplicationStatus.READY_FOR_REVIEW
        package.approval_decision = ApprovalDecision.REVISION_REQUESTED
        package.approved_by = approved_by
        package.approval_notes = notes
        package.updated_at = datetime.utcnow()
        
        return package
