from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScopeStatus(str, Enum):
    """Status for scope validation."""
    CLEAR = "clear"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    IMPOSSIBLE = "impossible"


class ScopeIssueType(str, Enum):
    """Types of scope issues."""
    MISSING_REQUIREMENTS = "missing_requirements"
    UNCLEAR_OBJECTIVES = "unclear_objectives"
    CONFLICTING_REQUIREMENTS = "conflicting_requirements"
    UNDEFINED_BOUNDARIES = "undefined_boundaries"
    UNREALISTIC_TIMELINE = "unrealistic_timeline"
    INSUFFICIENT_BUDGET = "insufficient_budget"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    RESOURCE_CONSTRAINTS = "resource_constraints"
    COMPLIANCE_ISSUES = "compliance_issues"


@dataclass(frozen=True)
class ScopeIssue:
    """A scope issue identified during validation."""
    issue_id: str
    issue_type: ScopeIssueType
    description: str
    severity: str  # low, medium, high, critical
    blocking: bool = False
    suggested_resolution: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScopeValidation:
    """A scope validation for a work specification."""
    validation_id: str
    work_specification_id: str
    scope_status: ScopeStatus
    scope_issues: List[ScopeIssue] = field(default_factory=list)
    clarity_score: float = 0.0  # 0.0 to 1.0
    completeness_score: float = 0.0  # 0.0 to 1.0
    feasibility_score: float = 0.0  # 0.0 to 1.0
    overall_score: float = 0.0  # 0.0 to 1.0
    validated_at: datetime = field(default_factory=datetime.utcnow)
    validated_by: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    required_clarifications: List[str] = field(default_factory=list)
    missing_elements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScopeRequirement:
    """A requirement for scope validation."""
    requirement_id: str
    requirement_type: str  # objective, deliverable, timeline, budget, resource
    description: str
    is_mandatory: bool = True
    validation_criteria: List[str] = field(default_factory=list)
    weight: float = 1.0  # Importance weight
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScopeValidationFramework:
    """Framework for scope validation."""

    def __init__(self):
        self._scope_requirements: Dict[str, ScopeRequirement] = {}

    def validate_scope(
        self,
        work_specification_id: str,
        has_objectives: bool,
        has_deliverables: bool,
        has_timeline: bool,
        has_budget: bool,
        has_requirements: bool,
        technical_feasibility: Optional[float] = None,
        resource_availability: Optional[float] = None,
    ) -> ScopeValidation:
        """Validate scope for a work specification."""
        issues = []
        clarity_score = 0.0
        completeness_score = 0.0
        feasibility_score = 0.0

        # Check for missing elements
        missing_elements = []
        if not has_objectives:
            missing_elements.append("objectives")
            issues.append(ScopeIssue(
                issue_id="missing_objectives",
                issue_type=ScopeIssueType.UNCLEAR_OBJECTIVES,
                description="Work objectives are not defined",
                severity="high",
                blocking=True,
                suggested_resolution="Define clear business objectives",
            ))
        if not has_deliverables:
            missing_elements.append("deliverables")
            issues.append(ScopeIssue(
                issue_id="missing_deliverables",
                issue_type=ScopeIssueType.MISSING_REQUIREMENTS,
                description="Deliverables are not specified",
                severity="high",
                blocking=True,
                suggested_resolution="Specify expected deliverables",
            ))
        if not has_timeline:
            missing_elements.append("timeline")
            issues.append(ScopeIssue(
                issue_id="missing_timeline",
                issue_type=ScopeIssueType.UNDEFINED_BOUNDARIES,
                description="Timeline is not specified",
                severity="medium",
                blocking=False,
                suggested_resolution="Specify project timeline",
            ))
        if not has_budget:
            missing_elements.append("budget")
            issues.append(ScopeIssue(
                issue_id="missing_budget",
                issue_type=ScopeIssueType.MISSING_REQUIREMENTS,
                description="Budget is not specified",
                severity="medium",
                blocking=False,
                suggested_resolution="Specify budget constraints",
            ))
        if not has_requirements:
            missing_elements.append("requirements")
            issues.append(ScopeIssue(
                issue_id="missing_requirements",
                issue_type=ScopeIssueType.MISSING_REQUIREMENTS,
                description="Requirements are not specified",
                severity="high",
                blocking=True,
                suggested_resolution="Specify functional and technical requirements",
            ))

        # Calculate scores
        total_elements = 5  # objectives, deliverables, timeline, budget, requirements
        present_elements = total_elements - len(missing_elements)
        completeness_score = present_elements / total_elements

        if len(missing_elements) == 0:
            clarity_score = 1.0
        elif len(missing_elements) <= 2:
            clarity_score = 0.5
        else:
            clarity_score = 0.0

        # Feasibility
        if technical_feasibility is not None and resource_availability is not None:
            feasibility_score = (technical_feasibility + resource_availability) / 2.0
        elif technical_feasibility is not None:
            feasibility_score = technical_feasibility
        elif resource_availability is not None:
            feasibility_score = resource_availability
        else:
            feasibility_score = 0.5  # Default middle value

        # Overall score
        overall_score = (clarity_score * 0.4 + completeness_score * 0.3 + feasibility_score * 0.3)

        # Determine scope status
        if len(issues) == 0:
            scope_status = ScopeStatus.CLEAR
        elif any(issue.blocking for issue in issues):
            if overall_score < 0.3:
                scope_status = ScopeStatus.IMPOSSIBLE
            else:
                scope_status = ScopeStatus.AMBIGUOUS
        elif len(missing_elements) > 0:
            scope_status = ScopeStatus.MISSING
        else:
            scope_status = ScopeStatus.AMBIGUOUS

        # Recommendations
        recommendations = []
        if scope_status == ScopeStatus.MISSING:
            recommendations.append("Add missing scope elements")
        if scope_status == ScopeStatus.AMBIGUOUS:
            recommendations.append("Clarify ambiguous requirements")
        if scope_status == ScopeStatus.IMPOSSIBLE:
            recommendations.append("Revise scope to make it feasible")

        return ScopeValidation(
            validation_id=f"validation_{work_specification_id}",
            work_specification_id=work_specification_id,
            scope_status=scope_status,
            scope_issues=issues,
            clarity_score=clarity_score,
            completeness_score=completeness_score,
            feasibility_score=feasibility_score,
            overall_score=overall_score,
            recommendations=recommendations,
            required_clarifications=[issue.suggested_resolution for issue in issues if issue.blocking],
            missing_elements=missing_elements,
        )

    def can_proceed(self, validation: ScopeValidation) -> bool:
        """Check if work can proceed based on scope validation."""
        return validation.scope_status == ScopeStatus.CLEAR

    def get_blocking_issues(self, validation: ScopeValidation) -> List[ScopeIssue]:
        """Get blocking issues from scope validation."""
        return [issue for issue in validation.scope_issues if issue.blocking]

    def add_scope_requirement(self, requirement: ScopeRequirement) -> bool:
        """Add a scope requirement."""
        if requirement.requirement_id in self._scope_requirements:
            return False
        self._scope_requirements[requirement.requirement_id] = requirement
        return True

    def get_scope_requirement(self, requirement_id: str) -> Optional[ScopeRequirement]:
        """Get a scope requirement by ID."""
        return self._scope_requirements.get(requirement_id)
