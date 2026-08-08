from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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
from app.work_market.application_package import Proposal, ProposalSection


@dataclass
class GeneratedProposal:
    """A generated client-facing proposal."""
    proposal: Proposal
    raw_text: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProposalGenerationResult:
    """Result of proposal generation."""
    generated: GeneratedProposal
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ProposalGenerator:
    """
    Generates client-facing proposals from proposal strategies.
    
    Creates professional, evidence-backed proposals that
    clearly communicate value and capabilities.
    """

    def __init__(self) -> None:
        pass

    def generate_proposal(
        self,
        job_id: str,
        strategy: ProposalStrategy,
        knowledge_selections: Optional[List[Any]] = None,
    ) -> ProposalGenerationResult:
        """
        Generate a client-facing proposal from strategy.
        
        Args:
            job_id: The job identifier
            strategy: The proposal strategy
            knowledge_selections: Selected knowledge items (optional)
            
        Returns:
            ProposalGenerationResult with the generated proposal
        """
        proposal_id = f"proposal_{job_id}"
        
        # Build proposal sections
        sections = self._build_all_sections(strategy, knowledge_selections)
        
        # Generate full proposal text
        raw_text = self._generate_full_text(sections)
        
        # Create proposal object
        proposal = Proposal(
            proposal_id=proposal_id,
            job_id=job_id,
            job_understanding=self._generate_job_understanding(strategy),
            proposed_approach=self._generate_proposed_approach(strategy),
            relevant_capabilities=strategy.capability_claims,
            supporting_evidence=self._generate_supporting_evidence(strategy),
            deliverables=strategy.deliverables,
            timeline=self._generate_timeline(strategy),
            budget_proposal=self._generate_budget_proposal(strategy),
            assumptions=strategy.assumptions,
            risks=strategy.risks,
            client_questions=strategy.client_questions,
            sections=sections,
            confidence_score=strategy.confidence_score,
        )
        
        generated = GeneratedProposal(
            proposal=proposal,
            raw_text=raw_text,
        )
        
        # Validate proposal has no fabricated claims
        fabricated_claims = [
            c for c in strategy.capability_claims
            if c.is_fabricated
        ]
        
        if fabricated_claims:
            return ProposalGenerationResult(
                generated=generated,
                success=False,
                errors=[
                    f"Proposal contains {len(fabricated_claims)} claims without evidence backing"
                ],
            )
        
        return ProposalGenerationResult(generated=generated, success=True)

    def _build_all_sections(
        self,
        strategy: ProposalStrategy,
        knowledge_selections: Optional[List[Any]] = None,
    ) -> List[ProposalSection]:
        """Build all proposal sections."""
        sections = [
            self._build_understanding_section(strategy),
            self._build_approach_section(strategy),
            self._build_capabilities_section(strategy),
            self._build_deliverables_section(strategy),
            self._build_timeline_section(strategy),
            self._build_risks_section(strategy),
            self._build_questions_section(strategy),
        ]
        
        return sections

    def _build_understanding_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the job understanding section."""
        content = self._generate_job_understanding(strategy)
        
        return ProposalSection(
            section_id="understanding",
            title="Job Understanding",
            content=content,
            order=1,
        )

    def _build_approach_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the proposed approach section."""
        content = self._generate_proposed_approach(strategy)
        
        return ProposalSection(
            section_id="approach",
            title="Proposed Approach",
            content=content,
            order=2,
        )

    def _build_capabilities_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the relevant capabilities section."""
        content = self._generate_capabilities_content(strategy)
        
        return ProposalSection(
            section_id="capabilities",
            title="Relevant Capabilities",
            content=content,
            order=3,
        )

    def _build_deliverables_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the deliverables section."""
        content = self._generate_deliverables_content(strategy)
        
        return ProposalSection(
            section_id="deliverables",
            title="Deliverables",
            content=content,
            order=4,
        )

    def _build_timeline_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the timeline section."""
        content = self._generate_timeline(strategy)
        
        return ProposalSection(
            section_id="timeline",
            title="Timeline",
            content=content,
            order=5,
        )

    def _build_risks_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the risks and mitigations section."""
        content = self._generate_risks_content(strategy)
        
        return ProposalSection(
            section_id="risks",
            title="Risks and Mitigations",
            content=content,
            order=6,
        )

    def _build_questions_section(self, strategy: ProposalStrategy) -> ProposalSection:
        """Build the questions for client section."""
        content = self._generate_questions_content(strategy)
        
        return ProposalSection(
            section_id="questions",
            title="Questions for Client",
            content=content,
            order=7,
        )

    def _generate_job_understanding(self, strategy: ProposalStrategy) -> str:
        """Generate job understanding text."""
        if not strategy.client_requirements:
            return "We understand you need professional services for your project."
        
        requirements_text = "\n".join([
            f"- {req.description} (Priority: {req.priority})"
            for req in strategy.client_requirements
        ])
        
        return f"""Based on your job description, we understand that you need:

{requirements_text}

We have analyzed these requirements and are confident in our ability to deliver."""

    def _generate_proposed_approach(self, strategy: ProposalStrategy) -> str:
        """Generate proposed approach text."""
        return f"""Our approach focuses on delivering exceptional results through:

1. **Thorough Analysis**: We begin by deeply understanding your requirements and objectives.

2. **Professional Execution**: We apply our expertise to deliver high-quality work that meets your standards.

3. **Clear Communication**: We maintain regular communication to ensure alignment and address any questions promptly.

4. **Quality Assurance**: We review and test our deliverables to ensure they meet acceptance criteria.

This approach ensures we deliver value while maintaining flexibility to adapt to your needs."""

    def _generate_capabilities_content(self, strategy: ProposalStrategy) -> str:
        """Generate capabilities section content."""
        if not strategy.capability_claims:
            return "Our capabilities align with your project requirements."
        
        content = "We bring the following relevant capabilities to this project:\n\n"
        
        for claim in strategy.capability_claims:
            content += f"**{claim.capability_name}**\n"
            content += f"{claim.claim}\n"
            if claim.evidence_ids:
                content += f"Supported by {len(claim.evidence_ids)} evidence items\n"
            content += f"Confidence: {claim.confidence:.0%}\n\n"
        
        return content

    def _generate_deliverables_content(self, strategy: ProposalStrategy) -> str:
        """Generate deliverables section content."""
        if not strategy.deliverables:
            return "Deliverables will be defined based on project scope."
        
        content = "We will deliver the following:\n\n"
        
        for deliverable in strategy.deliverables:
            content += f"**{deliverable.name}**\n"
            content += f"{deliverable.description}\n"
            if deliverable.estimated_hours > 0:
                content += f"Estimated effort: {deliverable.estimated_hours} hours\n"
            if deliverable.acceptance_criteria:
                content += "Acceptance criteria:\n"
                for criteria in deliverable.acceptance_criteria:
                    content += f"- {criteria}\n"
            content += "\n"
        
        return content

    def _generate_timeline(self, strategy: ProposalStrategy) -> str:
        """Generate timeline text."""
        days = strategy.estimated_timeline_days
        if days == 0:
            days = 7
        
        return f"""**Estimated Timeline: {days} days**

This timeline includes:
- Initial analysis and planning
- Core execution
- Review and revisions
- Final delivery

We will provide regular updates on progress and milestones."""

    def _generate_budget_proposal(self, strategy: ProposalStrategy) -> str:
        """Generate budget proposal text."""
        budget = strategy.estimated_budget
        
        if budget == 0:
            return """**Budget**

We will discuss the budget based on the specific scope and requirements. Our pricing is transparent and competitive, reflecting the quality and value we deliver."""

        return f"""**Budget Proposal**

Estimated budget: ${budget:.2f}

This estimate is based on the scope as currently understood. Any changes to scope will be discussed and agreed upon before implementation."""

    def _generate_risks_content(self, strategy: ProposalStrategy) -> str:
        """Generate risks section content."""
        if not strategy.risks:
            return "We have identified no significant risks at this stage."
        
        content = "We have identified the following potential risks and mitigation strategies:\n\n"
        
        for risk in strategy.risks:
            content += f"**{risk.description}**\n"
            content += f"Likelihood: {risk.likelihood}, Impact: {risk.impact}\n"
            content += f"Mitigation: {risk.mitigation}\n\n"
        
        return content

    def _generate_questions_content(self, strategy: ProposalStrategy) -> str:
        """Generate questions section content."""
        if not strategy.client_questions:
            return "We have no questions at this time."
        
        content = "To ensure we deliver exactly what you need, we have the following questions:\n\n"
        
        for question in strategy.client_questions:
            content += f"**Q: {question.question}**\n"
            content += f"Category: {question.category}, Priority: {question.priority}\n\n"
        
        return content

    def _generate_supporting_evidence(self, strategy: ProposalStrategy) -> Dict[str, str]:
        """Generate supporting evidence descriptions."""
        evidence_descriptions = {}
        
        for claim in strategy.capability_claims:
            for evidence_id in claim.evidence_ids:
                evidence_descriptions[evidence_id] = (
                    f"Evidence supporting {claim.capability_name}: {claim.claim}"
                )
        
        return evidence_descriptions

    def _generate_full_text(self, sections: List[ProposalSection]) -> str:
        """Generate full proposal text from sections."""
        sections_sorted = sorted(sections, key=lambda x: x.order)
        
        full_text = ""
        for section in sections_sorted:
            full_text += f"# {section.title}\n\n"
            full_text += f"{section.content}\n\n"
            full_text += "---\n\n"
        
        return full_text
