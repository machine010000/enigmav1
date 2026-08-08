from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.models import FreelanceJob
from app.work_market.job_analyzer import JobAnalysisResult
from app.work_market.job_readiness import JobReadinessResult
from app.work_market.job_gap_analysis import GapAnalysisResult


@dataclass
class ClientGoalsContext:
    """Context about client goals."""
    primary_goal: str
    secondary_goals: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    timeline_expectations: str = ""
    budget_expectations: str = ""


@dataclass
class DeliverableContext:
    """Context about expected deliverables."""
    primary_deliverables: List[str] = field(default_factory=list)
    secondary_deliverables: List[str] = field(default_factory=list)
    deliverable_formats: List[str] = field(default_factory=list)
    delivery_phases: List[Dict[str, Any]] = field(default_factory=list)
    quality_standards: List[str] = field(default_factory=list)


@dataclass
class TimelineContext:
    """Context about timeline."""
    estimated_duration: str = ""
    key_milestones: List[Dict[str, Any]] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)
    buffer_time: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ScopeContext:
    """Context about project scope."""
    in_scope: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    optional_additions: List[str] = field(default_factory=list)


@dataclass
class RiskContext:
    """Context about project risks."""
    identified_risks: List[str] = field(default_factory=list)
    risk_mitigation: Dict[str, str] = field(default_factory=dict)
    contingency_plans: List[str] = field(default_factory=list)
    risk_level: str = ""


@dataclass
class ValueContext:
    """Context about value proposition."""
    business_value: str = ""
    roi_projection: str = ""
    competitive_advantages: List[str] = field(default_factory=list)
    unique_selling_points: List[str] = field(default_factory=list)
    long_term_benefits: List[str] = field(default_factory=list)


@dataclass
class ProposalContextResult:
    """Comprehensive proposal context result."""
    work_id: str
    client_goals: ClientGoalsContext
    deliverables: DeliverableContext
    timeline: TimelineContext
    scope: ScopeContext
    risks: RiskContext
    value: ValueContext
    pricing_context: Dict[str, Any] = field(default_factory=dict)
    terms_context: Dict[str, Any] = field(default_factory=dict)
    communication_context: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)


class ProposalContextGenerator(ABC):
    """Contract for generating proposal context."""

    @abstractmethod
    def generate_proposal_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
        gap_analysis: GapAnalysisResult,
    ) -> ProposalContextResult:
        """
        Generate structured proposal context.

        Generates:
        - Client goals context
        - Expected deliverables
        - Suggested timeline
        - Suggested scope
        - Suggested risks
        - Suggested value

        Returns comprehensive proposal context (not proposal text).
        """
        pass


class SEOProposalContextGenerator(ProposalContextGenerator):
    """
    Generates proposal context for SEO jobs.

    Provides structured context for proposal creation without generating text.
    """

    def generate_proposal_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
        gap_analysis: GapAnalysisResult,
    ) -> ProposalContextResult:
        """Generate structured proposal context."""
        # Generate client goals context
        client_goals = self._generate_client_goals_context(job, work_spec, job_analysis)
        
        # Generate deliverables context
        deliverables = self._generate_deliverables_context(work_spec, job_analysis)
        
        # Generate timeline context
        timeline = self._generate_timeline_context(job_analysis, work_spec)
        
        # Generate scope context
        scope = self._generate_scope_context(work_spec, job_analysis, gap_analysis)
        
        # Generate risk context
        risks = self._generate_risk_context(job_analysis, job_readiness)
        
        # Generate value context
        value = self._generate_value_context(job, work_spec, job_analysis)
        
        # Generate pricing context
        pricing_context = self._generate_pricing_context(job, job_analysis)
        
        # Generate terms context
        terms_context = self._generate_terms_context(job, work_spec, job_analysis)
        
        # Generate communication context
        communication_context = self._generate_communication_context(job, work_spec)
        
        return ProposalContextResult(
            work_id=work_spec.work_id,
            client_goals=client_goals,
            deliverables=deliverables,
            timeline=timeline,
            scope=scope,
            risks=risks,
            value=value,
            pricing_context=pricing_context,
            terms_context=terms_context,
            communication_context=communication_context,
        )

    def _generate_client_goals_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
    ) -> ClientGoalsContext:
        """Generate client goals context."""
        primary_goal = work_spec.business_goal
        secondary_goals = job_analysis.client_needs.secondary_needs
        
        # Success metrics from expected outcome
        success_metrics = job_analysis.client_needs.success_criteria
        
        # Timeline expectations
        timeline_expectations = job_analysis.timeline_analysis.estimated_duration
        
        # Budget expectations
        budget_expectations = f"${job.budget:.2f}" if job.budget else "Budget not specified"
        
        return ClientGoalsContext(
            primary_goal=primary_goal,
            secondary_goals=secondary_goals,
            success_metrics=success_metrics,
            timeline_expectations=timeline_expectations,
            budget_expectations=budget_expectations,
        )

    def _generate_deliverables_context(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
    ) -> DeliverableContext:
        """Generate deliverables context."""
        # Primary deliverables from expected outcome
        primary_deliverables = [work_spec.expected_outcome]
        
        # Secondary deliverables based on category
        category = work_spec.metadata.get("category", "seo_audit")
        secondary_deliverables = self._get_category_deliverables(category)
        
        # Deliverable formats
        deliverable_formats = ["PDF report", "Spreadsheet data", "Video walkthrough"]
        
        # Delivery phases
        delivery_phases = [
            {
                "phase": "Discovery",
                "deliverables": ["Initial assessment", "Requirements document"],
                "duration": "1-2 days",
            },
            {
                "phase": "Execution",
                "deliverables": ["Progress updates", "Draft deliverables"],
                "duration": job_analysis.timeline_analysis.estimated_duration,
            },
            {
                "phase": "Delivery",
                "deliverables": ["Final deliverables", "Documentation"],
                "duration": "1-2 days",
            },
        ]
        
        # Quality standards
        quality_standards = [
            "Industry best practices",
            "Google guidelines compliance",
            "Actionable recommendations",
            "Data-driven insights",
        ]
        
        return DeliverableContext(
            primary_deliverables=primary_deliverables,
            secondary_deliverables=secondary_deliverables,
            deliverable_formats=deliverable_formats,
            delivery_phases=delivery_phases,
            quality_standards=quality_standards,
        )

    def _get_category_deliverables(self, category: str) -> List[str]:
        """Get category-specific deliverables."""
        deliverable_map = {
            "seo_audit": ["Technical audit report", "Action plan", "Priority recommendations"],
            "keyword_research": ["Keyword list", "Search volume data", "Competition analysis"],
            "technical_seo": ["Technical report", "Fix recommendations", "Performance metrics"],
            "local_seo": ["Local optimization report", "Citation list", "GBP optimization"],
            "ecommerce_seo": ["Product optimization", "Site structure analysis", "Performance report"],
            "content_optimization": ["Content audit", "Optimization recommendations", "Content calendar"],
            "link_building": ["Link strategy", "Outreach plan", "Backlink report"],
            "seo_strategy": ["Strategy document", "Roadmap", "KPI definitions"],
        }
        
        return deliverable_map.get(category, ["Report", "Recommendations"])

    def _generate_timeline_context(
        self,
        job_analysis: JobAnalysisResult,
        work_spec: WorkSpecification,
    ) -> TimelineContext:
        """Generate timeline context."""
        estimated_duration = job_analysis.timeline_analysis.estimated_duration
        
        # Key milestones from analysis
        key_milestones = job_analysis.timeline_analysis.milestones
        
        # Critical path
        critical_path = job_analysis.timeline_analysis.critical_path
        
        # Buffer time based on complexity
        buffer_time = "1 week" if work_spec.complexity == "very_complex" else "3 days" if work_spec.complexity == "complex" else "1 day"
        
        # Dependencies
        dependencies = [
            "Client access to analytics",
            "Website access",
            "Client approval of approach",
        ]
        
        return TimelineContext(
            estimated_duration=estimated_duration,
            key_milestones=key_milestones,
            critical_path=critical_path,
            buffer_time=buffer_time,
            dependencies=dependencies,
        )

    def _generate_scope_context(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        gap_analysis: GapAnalysisResult,
    ) -> ScopeContext:
        """Generate scope context."""
        # In scope from required capabilities
        in_scope = work_spec.required_capabilities
        
        # Out of scope based on constraints
        out_of_scope = [
            "Website development",
            "Content creation (unless specified)",
            "Paid advertising",
            "Social media management",
        ]
        
        # Assumptions
        assumptions = [
            "Client has website access",
            "Client has analytics access",
            "Client will provide necessary information",
            "Website platform is supported",
        ]
        
        # Constraints from work spec
        constraints = work_spec.constraints
        
        # Optional additions based on recommended capabilities
        optional_additions = work_spec.recommended_capabilities
        
        return ScopeContext(
            in_scope=in_scope,
            out_of_scope=out_of_scope,
            assumptions=assumptions,
            constraints=constraints,
            optional_additions=optional_additions,
        )

    def _generate_risk_context(
        self,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> RiskContext:
        """Generate risk context."""
        # Identified risks
        identified_risks = job_analysis.risk_analysis.technical_risks + job_analysis.risk_analysis.client_risks
        
        # Risk mitigation
        risk_mitigation = job_analysis.risk_analysis.mitigation_strategies
        
        # Contingency plans
        contingency_plans = [
            "Extended timeline if issues discovered",
            "Additional resources if complexity increases",
            "Scope adjustment if budget constraints",
        ]
        
        # Risk level
        risk_level = job_analysis.risk_analysis.overall_risk.value
        
        return RiskContext(
            identified_risks=identified_risks,
            risk_mitigation=risk_mitigation,
            contingency_plans=contingency_plans,
            risk_level=risk_level,
        )

    def _generate_value_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
    ) -> ValueContext:
        """Generate value context."""
        # Business value from business goal
        business_value = f"Achieve {work_spec.business_goal}"
        
        # ROI projection
        roi_projection = self._generate_roi_projection(job, job_analysis)
        
        # Competitive advantages
        competitive_advantages = job_analysis.competition_analysis.differentiation_opportunities
        
        # Unique selling points
        unique_selling_points = [
            "Data-driven approach",
            "Industry best practices",
            "Comprehensive analysis",
            "Actionable recommendations",
        ]
        
        # Long-term benefits
        long_term_benefits = [
            "Sustainable SEO improvements",
            "Knowledge transfer",
            "Process documentation",
            "Ongoing optimization framework",
        ]
        
        return ValueContext(
            business_value=business_value,
            roi_projection=roi_projection,
            competitive_advantages=competitive_advantages,
            unique_selling_points=unique_selling_points,
            long_term_benefits=long_term_benefits,
        )

    def _generate_roi_projection(self, job: FreelanceJob, job_analysis: JobAnalysisResult) -> str:
        """Generate ROI projection."""
        if job.budget:
            # Simple ROI projection based on budget
            if job.budget > 3000:
                return "Expected ROI: 3-5x investment within 6 months"
            elif job.budget > 1000:
                return "Expected ROI: 2-3x investment within 6 months"
            else:
                return "Expected ROI: 1.5-2x investment within 6 months"
        return "ROI depends on implementation and market conditions"

    def _generate_pricing_context(
        self,
        job: FreelanceJob,
        job_analysis: JobAnalysisResult,
    ) -> Dict[str, Any]:
        """Generate pricing context."""
        context = {}
        
        # Budget range
        if job.budget:
            context["client_budget"] = job.budget
            context["currency"] = job.currency
        
        # Estimated cost range
        estimated_range = job_analysis.budget_analysis.estimated_cost_range
        context["estimated_cost_range"] = estimated_range
        
        # Budget adequacy
        context["budget_adequacy"] = job_analysis.budget_analysis.budget_adequacy
        
        # Payment terms
        context["suggested_payment_terms"] = [
            "50% upfront",
            "50% on delivery",
        ]
        
        # Cost breakdown
        context["cost_breakdown"] = job_analysis.budget_analysis.cost_breakdown
        
        return context

    def _generate_terms_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
    ) -> Dict[str, Any]:
        """Generate terms context."""
        context = {}
        
        # Timeline terms
        context["timeline_terms"] = {
            "estimated_duration": job_analysis.timeline_analysis.estimated_duration,
            "deadline_feasibility": job_analysis.timeline_analysis.deadline_feasibility,
            "milestone_based": True,
        }
        
        # Scope terms
        context["scope_terms"] = {
            "flexible_scope": work_spec.complexity != "simple",
            "change_management": "Included for scope changes",
            "approval_process": "Client approval required for major changes",
        }
        
        # Quality terms
        context["quality_terms"] = {
            "quality_guarantee": "Revisions included for deliverables",
            "satisfaction_guarantee": "Client satisfaction focused",
            "industry_standards": "Google guidelines and best practices",
        }
        
        # Support terms
        context["support_terms"] = {
            "post_delivery_support": "30 days support included",
            "clarification_support": "Unlimited clarification during project",
        }
        
        return context

    def _generate_communication_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
    ) -> Dict[str, Any]:
        """Generate communication context."""
        context = {}
        
        # Communication frequency
        context["communication_frequency"] = {
            "updates": "Weekly",
            "milestones": "At each milestone",
            "urgent": "As needed",
        }
        
        # Communication channels
        context["communication_channels"] = [
            "Email",
            "Video calls",
            "Project management tool",
        ]
        
        # Reporting
        context["reporting"] = {
            "progress_reports": "Weekly",
            "milestone_reports": "At each milestone",
            "final_report": "Comprehensive final report",
        }
        
        # Client involvement
        context["client_involvement"] = {
            "required": "Access to analytics and website",
            "approvals": "Milestone approvals required",
            "feedback": "Regular feedback sessions",
        }
        
        return context


class ProposalContextOrchestrator:
    """
    Orchestrates proposal context generation.
    """

    def __init__(self) -> None:
        self._generator = SEOProposalContextGenerator()

    def generate_proposal_context(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
        gap_analysis: GapAnalysisResult,
    ) -> ProposalContextResult:
        """Generate structured proposal context."""
        return self._generator.generate_proposal_context(
            job,
            work_spec,
            job_analysis,
            job_readiness,
            gap_analysis,
        )
