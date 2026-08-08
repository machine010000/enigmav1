from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.job_analyzer import JobAnalysisResult
from app.work_market.job_readiness import JobReadinessResult


class GapSeverity(str, Enum):
    """Severity levels for gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GapType(str, Enum):
    """Types of gaps."""
    KNOWLEDGE = "knowledge"
    EVIDENCE = "evidence"
    CAPABILITY = "capability"
    EXECUTION_TEMPLATE = "execution_template"
    DELIVERABLE = "deliverable"
    EXPERIENCE = "experience"


@dataclass
class KnowledgeGap:
    """Gap in knowledge."""
    gap_id: str
    knowledge_area: str
    severity: GapSeverity
    description: str
    impact: str
    remediation: str
    estimated_time_to_close: str
    sources_to_consult: List[str] = field(default_factory=list)


@dataclass
class EvidenceGap:
    """Gap in evidence."""
    gap_id: str
    evidence_type: str
    severity: GapSeverity
    description: str
    impact: str
    remediation: str
    potential_sources: List[str] = field(default_factory=list)


@dataclass
class CapabilityGap:
    """Gap in capability."""
    gap_id: str
    capability: str
    severity: GapSeverity
    description: str
    impact: str
    remediation: str
    development_path: List[str] = field(default_factory=list)


@dataclass
class ExecutionTemplateGap:
    """Gap in execution template."""
    gap_id: str
    task: str
    severity: GapSeverity
    description: str
    impact: str
    remediation: str
    template_requirements: List[str] = field(default_factory=list)


@dataclass
class DeliverableGap:
    """Gap in deliverable definition."""
    gap_id: str
    deliverable: str
    severity: GapSeverity
    description: str
    impact: str
    remediation: str
    specification_requirements: List[str] = field(default_factory=list)


@dataclass
class ExperienceGap:
    """Gap in experience."""
    gap_id: str
    experience_area: str
    severity: GapSeverity
    description: str
    impact: str
    remediation: str
    suggested_projects: List[str] = field(default_factory=list)


@dataclass
class GapAnalysisResult:
    """Comprehensive gap analysis result."""
    work_id: str
    knowledge_gaps: List[KnowledgeGap] = field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = field(default_factory=list)
    capability_gaps: List[CapabilityGap] = field(default_factory=list)
    execution_template_gaps: List[ExecutionTemplateGap] = field(default_factory=list)
    deliverable_gaps: List[DeliverableGap] = field(default_factory=list)
    experience_gaps: List[ExperienceGap] = field(default_factory=list)
    total_gaps: int = 0
    critical_gaps: int = 0
    high_gaps: int = 0
    medium_gaps: int = 0
    low_gaps: int = 0
    closure_priority: List[str] = field(default_factory=list)
    estimated_closure_time: str = ""
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


class JobGapAnalyzer(ABC):
    """Contract for gap analysis."""

    @abstractmethod
    def analyze_gaps(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> GapAnalysisResult:
        """
        Analyze gaps for job execution.

        Identifies:
        - Missing knowledge
        - Missing evidence
        - Missing capabilities
        - Missing execution templates
        - Missing deliverable specifications
        - Missing experience

        Returns comprehensive gap analysis.
        """
        pass


class SEOJobGapAnalyzer(JobGapAnalyzer):
    """
    Analyzes gaps for SEO jobs.

    Identifies all gaps that need to be closed for successful execution.
    """

    def analyze_gaps(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> GapAnalysisResult:
        """Analyze gaps for job execution."""
        # Analyze knowledge gaps
        knowledge_gaps = self._analyze_knowledge_gaps(job_readiness)
        
        # Analyze evidence gaps
        evidence_gaps = self._analyze_evidence_gaps(job_readiness)
        
        # Analyze capability gaps
        capability_gaps = self._analyze_capability_gaps(job_readiness)
        
        # Analyze execution template gaps
        execution_template_gaps = self._analyze_execution_template_gaps(work_spec, job_readiness)
        
        # Analyze deliverable gaps
        deliverable_gaps = self._analyze_deliverable_gaps(work_spec, job_analysis)
        
        # Analyze experience gaps
        experience_gaps = self._analyze_experience_gaps(job_readiness)
        
        # Calculate gap statistics
        total_gaps = (
            len(knowledge_gaps)
            + len(evidence_gaps)
            + len(capability_gaps)
            + len(execution_template_gaps)
            + len(deliverable_gaps)
            + len(experience_gaps)
        )
        
        critical_gaps = sum(
            1 for gap in knowledge_gaps + evidence_gaps + capability_gaps
            if gap.severity == GapSeverity.CRITICAL
        )
        
        high_gaps = sum(
            1 for gap in knowledge_gaps + evidence_gaps + capability_gaps
            if gap.severity == GapSeverity.HIGH
        )
        
        medium_gaps = sum(
            1 for gap in knowledge_gaps + evidence_gaps + capability_gaps
            if gap.severity == GapSeverity.MEDIUM
        )
        
        low_gaps = sum(
            1 for gap in knowledge_gaps + evidence_gaps + capability_gaps
            if gap.severity == GapSeverity.LOW
        )
        
        # Determine closure priority
        closure_priority = self._determine_closure_priority(
            knowledge_gaps,
            evidence_gaps,
            capability_gaps,
        )
        
        # Estimate closure time
        estimated_closure_time = self._estimate_closure_time(
            critical_gaps,
            high_gaps,
            medium_gaps,
            low_gaps,
        )
        
        return GapAnalysisResult(
            work_id=work_spec.work_id,
            knowledge_gaps=knowledge_gaps,
            evidence_gaps=evidence_gaps,
            capability_gaps=capability_gaps,
            execution_template_gaps=execution_template_gaps,
            deliverable_gaps=deliverable_gaps,
            experience_gaps=experience_gaps,
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            high_gaps=high_gaps,
            medium_gaps=medium_gaps,
            low_gaps=low_gaps,
            closure_priority=closure_priority,
            estimated_closure_time=estimated_closure_time,
        )

    def _analyze_knowledge_gaps(self, job_readiness: JobReadinessResult) -> List[KnowledgeGap]:
        """Analyze knowledge gaps."""
        gaps = []
        
        for knowledge in job_readiness.knowledge_readiness.missing_knowledge:
            # Determine severity based on importance
            severity = self._determine_knowledge_severity(knowledge)
            
            gaps.append(KnowledgeGap(
                gap_id=f"knowledge_gap_{len(gaps)}",
                knowledge_area=knowledge,
                severity=severity,
                description=f"Missing knowledge in {knowledge}",
                impact="May limit ability to execute certain aspects of the job",
                remediation=f"Conduct research on {knowledge} and acquire relevant knowledge",
                estimated_time_to_close="1-2 weeks" if severity == GapSeverity.CRITICAL else "3-5 days",
                sources_to_consult=self._get_knowledge_sources(knowledge),
            ))
        
        return gaps

    def _determine_knowledge_severity(self, knowledge: str) -> GapSeverity:
        """Determine severity of knowledge gap."""
        critical_keywords = ["technical", "audit", "core", "vital", "critical"]
        high_keywords = ["strategy", "planning", "architecture"]
        
        knowledge_lower = knowledge.lower()
        
        if any(keyword in knowledge_lower for keyword in critical_keywords):
            return GapSeverity.CRITICAL
        elif any(keyword in knowledge_lower for keyword in high_keywords):
            return GapSeverity.HIGH
        else:
            return GapSeverity.MEDIUM

    def _get_knowledge_sources(self, knowledge: str) -> List[str]:
        """Get recommended sources for knowledge acquisition."""
        sources = []
        
        if "technical" in knowledge.lower():
            sources.extend(["Google Webmaster Guidelines", "Search Central", "Technical SEO blogs"])
        elif "keyword" in knowledge.lower():
            sources.extend(["Google Keyword Planner", "Ahrefs", "SEMrush", "Moz"])
        elif "optimization" in knowledge.lower():
            sources.extend(["Moz Guide", "SEMrush Academy", "HubSpot SEO Guide"])
        else:
            sources.extend(["Industry blogs", "Case studies", "Research papers"])
        
        return sources[:3]

    def _analyze_evidence_gaps(self, job_readiness: JobReadinessResult) -> List[EvidenceGap]:
        """Analyze evidence gaps."""
        gaps = []
        
        for evidence in job_readiness.evidence_readiness.missing_evidence:
            # Determine severity
            severity = self._determine_evidence_severity(evidence)
            
            gaps.append(EvidenceGap(
                gap_id=f"evidence_gap_{len(gaps)}",
                evidence_type=evidence,
                severity=severity,
                description=f"Missing evidence: {evidence}",
                impact="Reduces confidence in approach and may lead to suboptimal results",
                remediation=f"Gather evidence from {evidence} through research and case studies",
                potential_sources=self._get_evidence_sources(evidence),
            ))
        
        return gaps

    def _determine_evidence_severity(self, evidence: str) -> GapSeverity:
        """Determine severity of evidence gap."""
        if "audit" in evidence.lower() or "metrics" in evidence.lower():
            return GapSeverity.HIGH
        elif "case study" in evidence.lower():
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW

    def _get_evidence_sources(self, evidence: str) -> List[str]:
        """Get potential sources for evidence."""
        sources = []
        
        if "audit" in evidence.lower():
            sources.extend(["Previous audit reports", "Industry benchmarks", "Performance data"])
        elif "keyword" in evidence.lower():
            sources.extend(["Keyword tools", "Search data", "Competitor analysis"])
        elif "case study" in evidence.lower():
            sources.extend(["Industry case studies", "Success stories", "White papers"])
        else:
            sources.extend(["Research papers", "Industry reports", "Expert opinions"])
        
        return sources[:3]

    def _analyze_capability_gaps(self, job_readiness: JobReadinessResult) -> List[CapabilityGap]:
        """Analyze capability gaps."""
        gaps = []
        
        for capability in job_readiness.capability_readiness.missing_capabilities:
            # Determine severity
            severity = self._determine_capability_severity(capability)
            
            gaps.append(CapabilityGap(
                gap_id=f"capability_gap_{len(gaps)}",
                capability=capability,
                severity=severity,
                description=f"Missing capability: {capability}",
                impact="Cannot execute tasks requiring this capability",
                remediation=f"Develop {capability} through training and practice",
                development_path=self._get_capability_development_path(capability),
            ))
        
        return gaps

    def _determine_capability_severity(self, capability: str) -> GapSeverity:
        """Determine severity of capability gap."""
        critical_capabilities = ["technical_seo_audit", "keyword_research"]
        
        if capability in critical_capabilities:
            return GapSeverity.CRITICAL
        elif "audit" in capability.lower() or "research" in capability.lower():
            return GapSeverity.HIGH
        else:
            return GapSeverity.MEDIUM

    def _get_capability_development_path(self, capability: str) -> List[str]:
        """Get development path for capability."""
        path = []
        
        if "audit" in capability.lower():
            path.extend(["Learn audit tools", "Practice on test sites", "Study audit frameworks"])
        elif "research" in capability.lower():
            path.extend(["Learn research methodologies", "Practice with tools", "Study industry trends"])
        elif "optimization" in capability.lower():
            path.extend(["Learn optimization techniques", "Practice on content", "Study best practices"])
        else:
            path.extend(["Study fundamentals", "Practice exercises", "Build portfolio"])
        
        return path

    def _analyze_execution_template_gaps(
        self,
        work_spec: WorkSpecification,
        job_readiness: JobReadinessResult,
    ) -> List[ExecutionTemplateGap]:
        """Analyze execution template gaps."""
        gaps = []
        
        # Check if tasks have execution templates
        for task in work_spec.required_tasks:
            # In production, this would check if template exists
            # For now, assume gaps for complex tasks
            if "audit" in task.lower() or "analysis" in task.lower():
                gaps.append(ExecutionTemplateGap(
                    gap_id=f"template_gap_{len(gaps)}",
                    task=task,
                    severity=GapSeverity.MEDIUM,
                    description=f"Execution template not available for {task}",
                    impact="May lead to inconsistent execution",
                    remediation=f"Create execution template for {task}",
                    template_requirements=["Steps", "Quality gates", "Validation checkpoints"],
                ))
        
        return gaps

    def _analyze_deliverable_gaps(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
    ) -> List[DeliverableGap]:
        """Analyze deliverable specification gaps."""
        gaps = []
        
        # Check if deliverables are well-defined
        if not work_spec.expected_outcome or len(work_spec.expected_outcome) < 50:
            gaps.append(DeliverableGap(
                gap_id=f"deliverable_gap_{len(gaps)}",
                deliverable="Expected outcome",
                severity=GapSeverity.HIGH,
                description="Expected outcome is not well-defined",
                impact="May lead to misaligned expectations and client dissatisfaction",
                remediation="Clarify expected outcomes with client and document deliverables",
                specification_requirements=["Specific metrics", "Success criteria", "Delivery format"],
            ))
        
        # Check for missing deliverable specifications
        category = work_spec.metadata.get("category", "seo_audit")
        required_deliverables = self._get_required_deliverables(category)
        
        for deliverable in required_deliverables:
            if deliverable not in work_spec.expected_outcome.lower():
                gaps.append(DeliverableGap(
                    gap_id=f"deliverable_gap_{len(gaps)}",
                    deliverable=deliverable,
                    severity=GapSeverity.MEDIUM,
                    description=f"Deliverable specification missing: {deliverable}",
                    impact="May lead to incomplete deliverable set",
                    remediation=f"Define specification for {deliverable}",
                    specification_requirements=["Content", "Format", "Timeline"],
                ))
        
        return gaps

    def _get_required_deliverables(self, category: str) -> List[str]:
        """Get required deliverables for category."""
        deliverable_map = {
            "seo_audit": ["audit report", "action plan", "priority recommendations"],
            "keyword_research": ["keyword list", "search volume data", "competition analysis"],
            "technical_seo": ["technical report", "fix recommendations", "performance metrics"],
            "local_seo": ["local optimization report", "citation list", "GBP optimization"],
            "ecommerce_seo": ["product optimization", "site structure analysis", "performance report"],
            "content_optimization": ["content audit", "optimization recommendations", "content calendar"],
            "link_building": ["link strategy", "outreach plan", "backlink report"],
            "seo_strategy": ["strategy document", "roadmap", "KPI definitions"],
        }
        
        return deliverable_map.get(category, ["report", "recommendations"])

    def _analyze_experience_gaps(self, job_readiness: JobReadinessResult) -> List[ExperienceGap]:
        """Analyze experience gaps."""
        gaps = []
        
        experience_level = job_readiness.experience_readiness.experience_level
        
        if experience_level in ["beginner", "intermediate"]:
            gaps.append(ExperienceGap(
                gap_id=f"experience_gap_{len(gaps)}",
                experience_area="General SEO execution",
                severity=GapSeverity.MEDIUM if experience_level == "intermediate" else GapSeverity.HIGH,
                description=f"Experience level is {experience_level}, may be insufficient for complex jobs",
                impact="May lead to longer execution time and higher risk of errors",
                remediation="Gain experience through smaller projects and mentorship",
                suggested_projects=[
                    "Small business SEO audit",
                    "Keyword research for local business",
                    "On-page optimization for blog",
                ],
            ))
        
        # Check for specific experience gaps
        if job_readiness.experience_readiness.similar_jobs_completed < 3:
            gaps.append(ExperienceGap(
                gap_id=f"experience_gap_{len(gaps)}",
                experience_area="Similar job experience",
                severity=GapSeverity.MEDIUM,
                description=f"Only {job_readiness.experience_readiness.similar_jobs_completed} similar jobs completed",
                impact="May lack context for handling edge cases",
                remediation="Complete more similar projects to build experience",
                suggested_projects=["Practice projects", "Pro bono work", "Personal projects"],
            ))
        
        return gaps

    def _determine_closure_priority(
        self,
        knowledge_gaps: List[KnowledgeGap],
        evidence_gaps: List[EvidenceGap],
        capability_gaps: List[CapabilityGap],
    ) -> List[str]:
        """Determine priority order for gap closure."""
        priority = []
        
        # Critical gaps first
        for gap in knowledge_gaps + evidence_gaps + capability_gaps:
            if gap.severity == GapSeverity.CRITICAL and gap.gap_id not in priority:
                priority.append(gap.gap_id)
        
        # High gaps next
        for gap in knowledge_gaps + evidence_gaps + capability_gaps:
            if gap.severity == GapSeverity.HIGH and gap.gap_id not in priority:
                priority.append(gap.gap_id)
        
        # Medium gaps
        for gap in knowledge_gaps + evidence_gaps + capability_gaps:
            if gap.severity == GapSeverity.MEDIUM and gap.gap_id not in priority:
                priority.append(gap.gap_id)
        
        # Low gaps last
        for gap in knowledge_gaps + evidence_gaps + capability_gaps:
            if gap.severity == GapSeverity.LOW and gap.gap_id not in priority:
                priority.append(gap.gap_id)
        
        return priority

    def _estimate_closure_time(
        self,
        critical_gaps: int,
        high_gaps: int,
        medium_gaps: int,
        low_gaps: int,
    ) -> str:
        """Estimate time required to close all gaps."""
        # Time estimates per gap severity (in weeks)
        time_per_gap = {
            GapSeverity.CRITICAL: 2,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 0.5,
            GapSeverity.LOW: 0.25,
        }
        
        total_weeks = (
            critical_gaps * time_per_gap[GapSeverity.CRITICAL]
            + high_gaps * time_per_gap[GapSeverity.HIGH]
            + medium_gaps * time_per_gap[GapSeverity.MEDIUM]
            + low_gaps * time_per_gap[GapSeverity.LOW]
        )
        
        if total_weeks < 1:
            return "Less than 1 week"
        elif total_weeks < 2:
            return "1-2 weeks"
        elif total_weeks < 4:
            return "2-4 weeks"
        elif total_weeks < 8:
            return "1-2 months"
        else:
            return "2+ months"


class JobGapAnalysisOrchestrator:
    """
    Orchestrates job gap analysis.
    """

    def __init__(self) -> None:
        self._analyzer = SEOJobGapAnalyzer()

    def analyze_gaps(
        self,
        work_spec: WorkSpecification,
        job_analysis: JobAnalysisResult,
        job_readiness: JobReadinessResult,
    ) -> GapAnalysisResult:
        """Analyze gaps for job execution."""
        return self._analyzer.analyze_gaps(work_spec, job_analysis, job_readiness)
