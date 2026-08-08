from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskType(str, Enum):
    """Types of risks."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    KNOWLEDGE = "knowledge"
    EXECUTION = "execution"
    FINANCIAL = "financial"
    LEGAL = "legal"
    PLATFORM = "platform"
    CLIENT = "client"


class RiskSeverity(str, Enum):
    """Severity levels for risks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskImpact(str, Enum):
    """Impact levels for risks."""
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"


class RiskLikelihood(str, Enum):
    """Likelihood levels for risks."""
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    CERTAIN = "certain"


@dataclass(frozen=True)
class RiskFactor:
    """A single risk factor."""
    risk_id: str
    risk_type: RiskType
    name: str
    description: str
    severity: RiskSeverity
    impact: RiskImpact
    likelihood: RiskLikelihood
    mitigation_strategy: str = ""
    owner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskAssessment:
    """A risk assessment for a work request."""
    assessment_id: str
    work_specification_id: str
    risk_factors: List[RiskFactor] = field(default_factory=list)
    overall_risk_score: float = 0.0  # 0 to 100
    risk_category: str = "medium"  # low, medium, high, critical
    technical_risk_score: float = 0.0  # 0 to 100
    business_risk_score: float = 0.0  # 0 to 100
    knowledge_risk_score: float = 0.0  # 0 to 100
    execution_risk_score: float = 0.0  # 0 to 100
    financial_risk_score: float = 0.0  # 0 to 100
    legal_risk_score: float = 0.0  # 0 to 100
    platform_risk_score: float = 0.0  # 0 to 100
    client_risk_score: float = 0.0  # 0 to 100
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    assessed_by: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskThreshold:
    """Threshold for risk acceptance."""
    threshold_id: str
    risk_type: RiskType
    maximum_acceptable_score: float  # 0 to 100
    requires_mitigation: bool = True
    blocking: bool = False
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskAssessmentFramework:
    """Framework for risk assessment."""

    def __init__(self):
        self._risk_thresholds: Dict[str, RiskThreshold] = {}

    def calculate_risk_score(
        self,
        severity: RiskSeverity,
        impact: RiskImpact,
        likelihood: RiskLikelihood,
    ) -> float:
        """Calculate a risk score from severity, impact, and likelihood."""
        severity_scores = {
            RiskSeverity.LOW: 1,
            RiskSeverity.MEDIUM: 2,
            RiskSeverity.HIGH: 3,
            RiskSeverity.CRITICAL: 4,
        }
        impact_scores = {
            RiskImpact.MINIMAL: 1,
            RiskImpact.MODERATE: 2,
            RiskImpact.SIGNIFICANT: 3,
            RiskImpact.SEVERE: 4,
            RiskImpact.CATASTROPHIC: 5,
        }
        likelihood_scores = {
            RiskLikelihood.RARE: 1,
            RiskLikelihood.UNLIKELY: 2,
            RiskLikelihood.POSSIBLE: 3,
            RiskLikelihood.LIKELY: 4,
            RiskLikelihood.CERTAIN: 5,
        }

        severity_score = severity_scores.get(severity, 2)
        impact_score = impact_scores.get(impact, 2)
        likelihood_score = likelihood_scores.get(likelihood, 2)

        # Weighted calculation
        score = (
            (severity_score * 0.3)
            + (impact_score * 0.4)
            + (likelihood_score * 0.3)
        ) / 5.0 * 100

        return min(score, 100.0)

    def assess_risk_by_type(
        self,
        risk_type: RiskType,
        risk_factors: List[RiskFactor],
    ) -> float:
        """Assess risk score for a specific risk type."""
        type_factors = [f for f in risk_factors if f.risk_type == risk_type]
        if not type_factors:
            return 0.0

        total_score = 0.0
        for factor in type_factors:
            score = self.calculate_risk_score(
                factor.severity,
                factor.impact,
                factor.likelihood,
            )
            total_score += score

        return min(total_score / len(type_factors), 100.0)

    def determine_risk_category(self, overall_score: float) -> str:
        """Determine risk category from overall score."""
        if overall_score < 25:
            return "low"
        elif overall_score < 50:
            return "medium"
        elif overall_score < 75:
            return "high"
        else:
            return "critical"

    def check_thresholds(
        self,
        assessment: RiskAssessment,
    ) -> Dict[str, bool]:
        """Check if risk assessment meets thresholds."""
        results = {}
        for threshold_id, threshold in self._risk_thresholds.items():
            if threshold.risk_type == RiskType.TECHNICAL:
                score = assessment.technical_risk_score
            elif threshold.risk_type == RiskType.BUSINESS:
                score = assessment.business_risk_score
            elif threshold.risk_type == RiskType.KNOWLEDGE:
                score = assessment.knowledge_risk_score
            elif threshold.risk_type == RiskType.EXECUTION:
                score = assessment.execution_risk_score
            elif threshold.risk_type == RiskType.FINANCIAL:
                score = assessment.financial_risk_score
            elif threshold.risk_type == RiskType.LEGAL:
                score = assessment.legal_risk_score
            elif threshold.risk_type == RiskType.PLATFORM:
                score = assessment.platform_risk_score
            elif threshold.risk_type == RiskType.CLIENT:
                score = assessment.client_risk_score
            else:
                score = assessment.overall_risk_score

            results[threshold_id] = score <= threshold.maximum_acceptable_score

        return results

    def add_threshold(self, threshold: RiskThreshold) -> bool:
        """Add a risk threshold."""
        if threshold.threshold_id in self._risk_thresholds:
            return False
        self._risk_thresholds[threshold.threshold_id] = threshold
        return True

    def get_threshold(self, threshold_id: str) -> Optional[RiskThreshold]:
        """Get a risk threshold by ID."""
        return self._risk_thresholds.get(threshold_id)
