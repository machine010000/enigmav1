from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import re

from app.expert_domains.work.work_specification import WorkSpecification
from app.work_market.models import FreelanceJob


class RiskLevel(str, Enum):
    """Risk levels for job analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DifficultyLevel(str, Enum):
    """Difficulty levels for job analysis."""
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    VERY_HARD = "very_hard"


@dataclass
class ClientNeedsAnalysis:
    """Analysis of client needs."""
    primary_need: str
    secondary_needs: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    stakeholder_analysis: Dict[str, str] = field(default_factory=dict)


@dataclass
class BudgetAnalysis:
    """Analysis of job budget."""
    estimated_cost_range: tuple[float, float]  # (min, max)
    budget_adequacy: str  # adequate, insufficient, generous
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    value_proposition: str = ""


@dataclass
class TimelineAnalysis:
    """Analysis of job timeline."""
    estimated_duration: str  # e.g., "2-3 weeks"
    deadline_feasibility: str  # feasible, tight, impossible
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)


@dataclass
class RiskAnalysis:
    """Analysis of job risks."""
    overall_risk: RiskLevel
    technical_risks: List[str] = field(default_factory=list)
    client_risks: List[str] = field(default_factory=list)
    timeline_risks: List[str] = field(default_factory=list)
    budget_risks: List[str] = field(default_factory=list)
    mitigation_strategies: Dict[str, str] = field(default_factory=dict)


@dataclass
class CompetitionAnalysis:
    """Analysis of competitive landscape."""
    competition_level: str  # low, medium, high
    key_competitors: List[str] = field(default_factory=list)
    market_saturation: str = "medium"  # low, medium, high
    differentiation_opportunities: List[str] = field(default_factory=list)


@dataclass
class DifficultyAnalysis:
    """Analysis of job difficulty."""
    overall_difficulty: DifficultyLevel
    technical_difficulty: str  # low, medium, high
    scope_difficulty: str  # low, medium, high
    resource_difficulty: str  # low, medium, high
    complexity_factors: List[str] = field(default_factory=list)


@dataclass
class JobAnalysisResult:
    """Comprehensive job analysis result."""
    work_id: str
    client_needs: ClientNeedsAnalysis
    budget_analysis: BudgetAnalysis
    timeline_analysis: TimelineAnalysis
    risk_analysis: RiskAnalysis
    competition_analysis: CompetitionAnalysis
    difficulty_analysis: DifficultyAnalysis
    knowledge_requirements: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    execution_complexity: str = "moderate"
    confidence: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


class JobAnalyzer(ABC):
    """Contract for analyzing jobs."""

    @abstractmethod
    def analyze(self, job: FreelanceJob, work_spec: WorkSpecification) -> JobAnalysisResult:
        """
        Analyze a job comprehensively.

        Analyzes:
        - Client needs
        - Budget
        - Timeline
        - Risk
        - Competition
        - Difficulty
        - Knowledge requirements
        - Evidence requirements
        - Execution complexity

        Returns comprehensive analysis.
        """
        pass


class SEOJobAnalyzer(JobAnalyzer):
    """
    Analyzes SEO jobs comprehensively.

    Uses work specification and job details to provide detailed analysis.
    """

    def __init__(self) -> None:
        self._budget_estimates = self._initialize_budget_estimates()
        self._duration_estimates = self._initialize_duration_estimates()

    def _initialize_budget_estimates(self) -> Dict[str, tuple[float, float]]:
        """Initialize budget estimates for different job types."""
        return {
            "seo_audit": (500, 2000),
            "keyword_research": (300, 1500),
            "technical_seo": (800, 3000),
            "local_seo": (400, 1800),
            "ecommerce_seo": (1000, 5000),
            "content_optimization": (400, 2000),
            "link_building": (600, 2500),
            "seo_strategy": (1000, 4000),
            "on_page_seo": (500, 2000),
            "off_page_seo": (700, 3000),
        }

    def _initialize_duration_estimates(self) -> Dict[str, str]:
        """Initialize duration estimates for different job types."""
        return {
            "seo_audit": "1-2 weeks",
            "keyword_research": "3-5 days",
            "technical_seo": "2-4 weeks",
            "local_seo": "1-2 weeks",
            "ecommerce_seo": "3-6 weeks",
            "content_optimization": "1-3 weeks",
            "link_building": "4-8 weeks",
            "seo_strategy": "1-2 weeks",
            "on_page_seo": "1-2 weeks",
            "off_page_seo": "4-6 weeks",
        }

    def analyze(self, job: FreelanceJob, work_spec: WorkSpecification) -> JobAnalysisResult:
        """Analyze a job comprehensively."""
        # Analyze client needs
        client_needs = self._analyze_client_needs(job, work_spec)

        # Analyze budget
        budget_analysis = self._analyze_budget(job, work_spec)

        # Analyze timeline
        timeline_analysis = self._analyze_timeline(job, work_spec)

        # Analyze risks
        risk_analysis = self._analyze_risks(job, work_spec, client_needs, timeline_analysis)

        # Analyze competition
        competition_analysis = self._analyze_competition(job, work_spec)

        # Analyze difficulty
        difficulty_analysis = self._analyze_difficulty(job, work_spec, risk_analysis)

        # Determine knowledge requirements
        knowledge_requirements = self._determine_knowledge_requirements(work_spec)

        # Determine evidence requirements
        evidence_requirements = self._determine_evidence_requirements(work_spec)

        # Determine execution complexity
        execution_complexity = self._determine_execution_complexity(work_spec, difficulty_analysis)

        # Calculate overall confidence
        confidence = self._calculate_confidence(job, work_spec, risk_analysis)

        return JobAnalysisResult(
            work_id=work_spec.work_id,
            client_needs=client_needs,
            budget_analysis=budget_analysis,
            timeline_analysis=timeline_analysis,
            risk_analysis=risk_analysis,
            competition_analysis=competition_analysis,
            difficulty_analysis=difficulty_analysis,
            knowledge_requirements=knowledge_requirements,
            evidence_requirements=evidence_requirements,
            execution_complexity=execution_complexity,
            confidence=confidence,
        )

    def _analyze_client_needs(self, job: FreelanceJob, work_spec: WorkSpecification) -> ClientNeedsAnalysis:
        """Analyze client needs from job and work specification."""
        # Primary need from business goal
        primary_need = work_spec.business_goal

        # Secondary needs from description
        secondary_needs = self._extract_secondary_needs(job.description)

        # Pain points from description
        pain_points = self._extract_pain_points(job.description)

        # Success criteria from expected outcome
        success_criteria = self._extract_success_criteria(work_spec.expected_outcome)

        # Stakeholder analysis
        stakeholder_analysis = self._analyze_stakeholders(job.client_information)

        return ClientNeedsAnalysis(
            primary_need=primary_need,
            secondary_needs=secondary_needs,
            pain_points=pain_points,
            success_criteria=success_criteria,
            stakeholder_analysis=stakeholder_analysis,
        )

    def _extract_secondary_needs(self, description: str) -> List[str]:
        """Extract secondary needs from description."""
        needs = []
        need_patterns = [
            r"(?:also|additionally|plus|furthermore)(?:\s+(?:need|want|require))?\s+([^.!?]+)",
            r"(?:secondary|additional)(?:\s+(?:need|requirement))?\s+([^.!?]+)",
        ]

        for pattern in need_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                need = match.strip() if isinstance(match, str) else " ".join(match)
                if len(need) > 10:
                    needs.append(need)

        return needs[:5]  # Limit to top 5

    def _extract_pain_points(self, description: str) -> List[str]:
        """Extract pain points from description."""
        pain_points = []
        pain_patterns = [
            r"(?:problem|issue|challenge|struggle|difficulty)(?:\s+(?:is|are|with))?\s+([^.!?]+)",
            r"(?:not|don't|can't|unable|failing)(?:\s+(?:to|be))?\s+([^.!?]+)",
        ]

        for pattern in pain_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                pain = match.strip() if isinstance(match, str) else " ".join(match)
                if len(pain) > 10:
                    pain_points.append(pain)

        return pain_points[:5]

    def _extract_success_criteria(self, expected_outcome: str) -> List[str]:
        """Extract success criteria from expected outcome."""
        criteria = []
        # Split outcome into criteria
        if "and" in expected_outcome:
            criteria = [c.strip() for c in expected_outcome.split("and")]
        elif "," in expected_outcome:
            criteria = [c.strip() for c in expected_outcome.split(",")]
        else:
            criteria = [expected_outcome]

        return criteria[:5]

    def _analyze_stakeholders(self, client_info: Dict[str, Any]) -> Dict[str, str]:
        """Analyze stakeholders from client information."""
        stakeholders = {}
        
        if "company_size" in client_info:
            stakeholders["company"] = f"Company size: {client_info['company_size']}"
        
        if "team_size" in client_info:
            stakeholders["team"] = f"Team size: {client_info['team_size']}"
        
        if "decision_makers" in client_info:
            stakeholders["decision_makers"] = client_info["decision_makers"]

        return stakeholders

    def _analyze_budget(self, job: FreelanceJob, work_spec: WorkSpecification) -> BudgetAnalysis:
        """Analyze job budget."""
        # Get category from metadata
        category = work_spec.metadata.get("category", "seo_audit")
        
        # Get estimated cost range
        estimated_range = self._budget_estimates.get(category, (500, 2000))
        
        # Determine budget adequacy
        budget_adequacy = "adequate"
        if job.budget:
            if job.budget <= 0:
                budget_adequacy = "insufficient"
            elif job.budget < estimated_range[0]:
                budget_adequacy = "insufficient"
            elif job.budget > estimated_range[1] * 1.5:
                budget_adequacy = "generous"
        else:
            budget_adequacy = "insufficient"
        
        # Cost breakdown
        cost_breakdown = self._generate_cost_breakdown(work_spec, estimated_range)
        
        # Value proposition
        value_proposition = self._generate_value_proposition(work_spec, job.budget, estimated_range)
        
        return BudgetAnalysis(
            estimated_cost_range=estimated_range,
            budget_adequacy=budget_adequacy,
            cost_breakdown=cost_breakdown,
            value_proposition=value_proposition,
        )

    def _generate_cost_breakdown(self, work_spec: WorkSpecification, estimated_range: tuple[float, float]) -> Dict[str, float]:
        """Generate cost breakdown by task."""
        breakdown = {}
        
        # Simple breakdown based on required tasks
        num_tasks = len(work_spec.required_tasks)
        if num_tasks > 0:
            per_task_cost = (estimated_range[1] - estimated_range[0]) / num_tasks
            for i, task in enumerate(work_spec.required_tasks):
                breakdown[task] = estimated_range[0] + (i * per_task_cost)
        
        return breakdown

    def _generate_value_proposition(self, work_spec: WorkSpecification, budget: Optional[float], estimated_range: tuple[float, float]) -> str:
        """Generate value proposition."""
        if budget:
            if budget >= estimated_range[1]:
                return "Budget allows for comprehensive solution with premium deliverables"
            elif budget >= estimated_range[0]:
                return "Budget supports standard solution with core deliverables"
            else:
                return "Budget may require scope adjustment or phased approach"
        return "Budget not specified - will propose based on scope"

    def _analyze_timeline(self, job: FreelanceJob, work_spec: WorkSpecification) -> TimelineAnalysis:
        """Analyze job timeline."""
        # Get category from metadata
        category = work_spec.metadata.get("category", "seo_audit")
        
        # Get estimated duration
        estimated_duration = self._duration_estimates.get(category, "1-2 weeks")
        
        # Determine deadline feasibility
        deadline_feasibility = "feasible"
        if job.deadline:
            # Parse duration estimate to days
            duration_days = self._parse_duration_to_days(estimated_duration)
            time_until_deadline = (job.deadline - datetime.utcnow()).days
            
            if time_until_deadline < duration_days * 0.5:
                deadline_feasibility = "impossible"
            elif time_until_deadline < duration_days * 0.8:
                deadline_feasibility = "tight"
        
        # Generate milestones
        milestones = self._generate_milestones(work_spec, estimated_duration)
        
        # Determine critical path
        critical_path = self._determine_critical_path(work_spec)
        
        return TimelineAnalysis(
            estimated_duration=estimated_duration,
            deadline_feasibility=deadline_feasibility,
            milestones=milestones,
            critical_path=critical_path,
        )

    def _parse_duration_to_days(self, duration: str) -> int:
        """Parse duration string to days."""
        if "day" in duration:
            return int(re.findall(r'\d+', duration)[0])
        elif "week" in duration:
            weeks = int(re.findall(r'\d+', duration)[0])
            return weeks * 7
        elif "month" in duration:
            months = int(re.findall(r'\d+', duration)[0])
            return months * 30
        return 14  # Default to 2 weeks

    def _generate_milestones(self, work_spec: WorkSpecification, duration: str) -> List[Dict[str, Any]]:
        """Generate project milestones."""
        milestones = []
        
        # Initial milestone
        milestones.append({
            "name": "Project Kickoff",
            "description": "Initial consultation and requirements gathering",
            "estimated_completion": "Day 1-2",
        })
        
        # Midpoint milestone
        milestones.append({
            "name": "Progress Review",
            "description": "Review of initial findings and strategy",
            "estimated_completion": f"Day {self._parse_duration_to_days(duration) // 2}",
        })
        
        # Final milestone
        milestones.append({
            "name": "Delivery",
            "description": "Final deliverable submission",
            "estimated_completion": f"Day {self._parse_duration_to_days(duration)}",
        })
        
        return milestones

    def _determine_critical_path(self, work_spec: WorkSpecification) -> List[str]:
        """Determine critical path tasks."""
        # Use required tasks as critical path
        return work_spec.required_tasks[:5]

    def _analyze_risks(
        self,
        job: FreelanceJob,
        work_spec: WorkSpecification,
        client_needs: ClientNeedsAnalysis,
        timeline_analysis: TimelineAnalysis,
    ) -> RiskAnalysis:
        """Analyze job risks."""
        # Determine overall risk level
        overall_risk = self._determine_overall_risk(work_spec, timeline_analysis)
        
        # Technical risks
        technical_risks = self._identify_technical_risks(work_spec)
        
        # Client risks
        client_risks = self._identify_client_risks(job, client_needs)
        
        # Timeline risks
        timeline_risks = self._identify_timeline_risks(timeline_analysis)
        
        # Budget risks
        budget_risks = self._identify_budget_risks(job, work_spec)
        
        # Mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(
            technical_risks, client_risks, timeline_risks, budget_risks
        )
        
        return RiskAnalysis(
            overall_risk=overall_risk,
            technical_risks=technical_risks,
            client_risks=client_risks,
            timeline_risks=timeline_risks,
            budget_risks=budget_risks,
            mitigation_strategies=mitigation_strategies,
        )

    def _determine_overall_risk(self, work_spec: WorkSpecification, timeline_analysis: TimelineAnalysis) -> RiskLevel:
        """Determine overall risk level."""
        risk_score = 0
        
        # Complexity contributes to risk
        if work_spec.complexity == "very_complex":
            risk_score += 3
        elif work_spec.complexity == "complex":
            risk_score += 2
        elif work_spec.complexity == "moderate":
            risk_score += 1
        
        # Timeline contributes to risk
        if timeline_analysis.deadline_feasibility == "impossible":
            risk_score += 3
        elif timeline_analysis.deadline_feasibility == "tight":
            risk_score += 2
        
        # Determine risk level
        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _identify_technical_risks(self, work_spec: WorkSpecification) -> List[str]:
        """Identify technical risks."""
        risks = []
        
        if "technical_seo" in work_spec.metadata.get("category", ""):
            risks.append("Technical issues may be more complex than expected")
        
        if work_spec.complexity in ["complex", "very_complex"]:
            risks.append("High complexity may require specialized tools")
        
        if "ecommerce" in work_spec.industry.lower():
            risks.append("Ecommerce platforms have unique technical challenges")
        
        return risks[:5]

    def _identify_client_risks(self, job: FreelanceJob, client_needs: ClientNeedsAnalysis) -> List[str]:
        """Identify client-related risks."""
        risks = []
        
        if not job.client_information:
            risks.append("Limited client information available")
        
        if client_needs.pain_points:
            risks.append("Client may have unrealistic expectations")
        
        if job.budget and job.budget < 500:
            risks.append("Low budget may limit scope and quality")
        
        return risks[:5]

    def _identify_timeline_risks(self, timeline_analysis: TimelineAnalysis) -> List[str]:
        """Identify timeline-related risks."""
        risks = []
        
        if timeline_analysis.deadline_feasibility == "tight":
            risks.append("Tight deadline may require overtime or reduced scope")
        
        if timeline_analysis.deadline_feasibility == "impossible":
            risks.append("Deadline cannot be met with current scope")
        
        return risks[:5]

    def _identify_budget_risks(self, job: FreelanceJob, work_spec: WorkSpecification) -> List[str]:
        """Identify budget-related risks."""
        risks = []
        
        if not job.budget:
            risks.append("Budget not specified - may lead to scope creep")
        
        if job.budget and job.budget < 500:
            risks.append("Low budget may compromise quality")
        
        if work_spec.complexity == "very_complex" and job.budget and job.budget < 2000:
            risks.append("Complex work with low budget is high risk")
        
        return risks[:5]

    def _generate_mitigation_strategies(
        self,
        technical_risks: List[str],
        client_risks: List[str],
        timeline_risks: List[str],
        budget_risks: List[str],
    ) -> Dict[str, str]:
        """Generate mitigation strategies."""
        strategies = {}
        
        for i, risk in enumerate(technical_risks):
            strategies[f"technical_{i}"] = "Conduct thorough initial assessment to identify issues early"
        
        for i, risk in enumerate(client_risks):
            strategies[f"client_{i}"] = "Set clear expectations and communication protocols"
        
        for i, risk in enumerate(timeline_risks):
            strategies[f"timeline_{i}"] = "Propose phased approach with clear milestones"
        
        for i, risk in enumerate(budget_risks):
            strategies[f"budget_{i}"] = "Define clear scope and change management process"
        
        return strategies

    def _analyze_competition(self, job: FreelanceJob, work_spec: WorkSpecification) -> CompetitionAnalysis:
        """Analyze competitive landscape."""
        # Determine competition level based on budget and skills
        competition_level = "medium"
        
        if job.budget and job.budget > 3000:
            competition_level = "high"
        elif job.budget and job.budget < 500:
            competition_level = "low"
        
        # Market saturation based on category
        category = work_spec.metadata.get("category", "seo_audit")
        high_competition_categories = ["keyword_research", "link_building", "on_page_seo"]
        
        market_saturation = "medium"
        if category in high_competition_categories:
            market_saturation = "high"
        
        # Differentiation opportunities
        differentiation_opportunities = self._identify_differentiation_opportunities(work_spec)
        
        return CompetitionAnalysis(
            competition_level=competition_level,
            key_competitors=[],  # Would require external data
            market_saturation=market_saturation,
            differentiation_opportunities=differentiation_opportunities,
        )

    def _identify_differentiation_opportunities(self, work_spec: WorkSpecification) -> List[str]:
        """Identify opportunities for differentiation."""
        opportunities = []
        
        if work_spec.complexity == "very_complex":
            opportunities.append("Specialized expertise in complex SEO challenges")
        
        if "ecommerce" in work_spec.industry.lower():
            opportunities.append("Ecommerce-specific SEO experience")
        
        if work_spec.priority == "critical":
            opportunities.append("Rapid turnaround capability")
        
        return opportunities[:5]

    def _analyze_difficulty(self, job: FreelanceJob, work_spec: WorkSpecification, risk_analysis: RiskAnalysis) -> DifficultyAnalysis:
        """Analyze job difficulty."""
        # Determine overall difficulty
        overall_difficulty = self._determine_overall_difficulty(work_spec, risk_analysis)
        
        # Technical difficulty
        technical_difficulty = self._assess_technical_difficulty(work_spec)
        
        # Scope difficulty
        scope_difficulty = self._assess_scope_difficulty(work_spec)
        
        # Resource difficulty
        resource_difficulty = self._assess_resource_difficulty(job, work_spec)
        
        # Complexity factors
        complexity_factors = self._identify_complexity_factors(work_spec, risk_analysis)
        
        return DifficultyAnalysis(
            overall_difficulty=overall_difficulty,
            technical_difficulty=technical_difficulty,
            scope_difficulty=scope_difficulty,
            resource_difficulty=resource_difficulty,
            complexity_factors=complexity_factors,
        )

    def _determine_overall_difficulty(self, work_spec: WorkSpecification, risk_analysis: RiskAnalysis) -> DifficultyLevel:
        """Determine overall difficulty level."""
        difficulty_score = 0
        
        # Complexity contributes to difficulty
        if work_spec.complexity == "very_complex":
            difficulty_score += 3
        elif work_spec.complexity == "complex":
            difficulty_score += 2
        elif work_spec.complexity == "moderate":
            difficulty_score += 1
        
        # Risk contributes to difficulty
        if risk_analysis.overall_risk == RiskLevel.CRITICAL:
            difficulty_score += 3
        elif risk_analysis.overall_risk == RiskLevel.HIGH:
            difficulty_score += 2
        elif risk_analysis.overall_risk == RiskLevel.MEDIUM:
            difficulty_score += 1
        
        # Determine difficulty level
        if difficulty_score >= 5:
            return DifficultyLevel.VERY_HARD
        elif difficulty_score >= 3:
            return DifficultyLevel.HARD
        elif difficulty_score >= 1:
            return DifficultyLevel.MODERATE
        else:
            return DifficultyLevel.EASY

    def _assess_technical_difficulty(self, work_spec: WorkSpecification) -> str:
        """Assess technical difficulty."""
        if "technical" in work_spec.metadata.get("category", ""):
            return "high"
        elif work_spec.complexity in ["complex", "very_complex"]:
            return "high"
        else:
            return "medium"

    def _assess_scope_difficulty(self, work_spec: WorkSpecification) -> str:
        """Assess scope difficulty."""
        num_tasks = len(work_spec.required_tasks)
        if num_tasks > 10:
            return "high"
        elif num_tasks > 5:
            return "medium"
        else:
            return "low"

    def _assess_resource_difficulty(self, job: FreelanceJob, work_spec: WorkSpecification) -> str:
        """Assess resource difficulty."""
        if job.budget and job.budget < 500:
            return "high"
        elif work_spec.complexity == "very_complex":
            return "high"
        else:
            return "medium"

    def _identify_complexity_factors(self, work_spec: WorkSpecification, risk_analysis: RiskAnalysis) -> List[str]:
        """Identify factors contributing to complexity."""
        factors = []
        
        if work_spec.complexity == "very_complex":
            factors.append("High complexity requires specialized expertise")
        
        if len(work_spec.required_tasks) > 8:
            factors.append("Large number of required tasks")
        
        if risk_analysis.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            factors.append("High risk factors increase complexity")
        
        if "ecommerce" in work_spec.industry.lower():
            factors.append("Ecommerce platform complexity")
        
        return factors[:5]

    def _determine_knowledge_requirements(self, work_spec: WorkSpecification) -> List[str]:
        """Determine knowledge requirements from work specification."""
        requirements = []
        
        # Map capabilities to knowledge areas
        capability_to_knowledge = {
            "technical_seo_audit": "Technical SEO knowledge",
            "keyword_research": "Keyword research methodologies",
            "on_page_optimization": "On-page SEO best practices",
            "link_building": "Link building strategies",
            "content_optimization": "Content optimization techniques",
            "site_speed_optimization": "Performance optimization",
            "mobile_optimization": "Mobile-first indexing",
            "schema_markup": "Structured data implementation",
        }
        
        for capability in work_spec.required_capabilities:
            knowledge = capability_to_knowledge.get(capability, f"Knowledge in {capability}")
            requirements.append(knowledge)
        
        return list(set(requirements))

    def _determine_evidence_requirements(self, work_spec: WorkSpecification) -> List[str]:
        """Determine evidence requirements from work specification."""
        requirements = []
        
        # Evidence types needed for different capabilities
        capability_to_evidence = {
            "technical_seo_audit": "Technical audit reports, performance metrics",
            "keyword_research": "Keyword data, search volume metrics",
            "on_page_optimization": "On-page optimization case studies",
            "link_building": "Backlink analysis, successful link building examples",
            "content_optimization": "Content performance data",
        }
        
        for capability in work_spec.required_capabilities:
            evidence = capability_to_evidence.get(capability, f"Evidence for {capability}")
            requirements.append(evidence)
        
        return list(set(requirements))

    def _determine_execution_complexity(self, work_spec: WorkSpecification, difficulty_analysis: DifficultyAnalysis) -> str:
        """Determine execution complexity."""
        if difficulty_analysis.overall_difficulty == DifficultyLevel.VERY_HARD:
            return "very_complex"
        elif difficulty_analysis.overall_difficulty == DifficultyLevel.HARD:
            return "complex"
        elif difficulty_analysis.overall_difficulty == DifficultyLevel.MODERATE:
            return "moderate"
        else:
            return "simple"

    def _calculate_confidence(self, job: FreelanceJob, work_spec: WorkSpecification, risk_analysis: RiskAnalysis) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.7
        
        # Increase if job information is complete
        if job.budget and job.deadline and job.client_information:
            confidence += 0.1
        
        # Increase if work specification is well-defined
        if work_spec.required_capabilities and work_spec.required_tasks:
            confidence += 0.1
        
        # Decrease if risk is high
        if risk_analysis.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))


class JobAnalysisOrchestrator:
    """
    Orchestrates comprehensive job analysis.
    """

    def __init__(self) -> None:
        self._analyzer = SEOJobAnalyzer()

    def analyze_job(self, job: FreelanceJob, work_spec: WorkSpecification) -> JobAnalysisResult:
        """Analyze a job comprehensively."""
        return self._analyzer.analyze(job, work_spec)
