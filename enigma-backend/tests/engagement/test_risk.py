import pytest

from app.engagement.risk import (
    RiskType,
    RiskSeverity,
    RiskImpact,
    RiskLikelihood,
    RiskFactor,
    RiskAssessment,
    RiskThreshold,
    RiskAssessmentFramework,
)


class TestRiskFactor:
    """Tests for RiskFactor."""

    def test_risk_factor_creation(self):
        """Test creating a risk factor."""
        factor = RiskFactor(
            risk_id="risk1",
            risk_type=RiskType.TECHNICAL,
            name="Technical Risk",
            description="Technical implementation risk",
            severity=RiskSeverity.HIGH,
            impact=RiskImpact.SIGNIFICANT,
            likelihood=RiskLikelihood.LIKELY,
        )
        assert factor.risk_id == "risk1"
        assert factor.risk_type == RiskType.TECHNICAL
        assert factor.severity == RiskSeverity.HIGH


class TestRiskAssessment:
    """Tests for RiskAssessment."""

    def test_risk_assessment_creation(self):
        """Test creating a risk assessment."""
        assessment = RiskAssessment(
            assessment_id="assessment1",
            work_specification_id="work1",
            overall_risk_score=50.0,
            risk_category="medium",
        )
        assert assessment.assessment_id == "assessment1"
        assert assessment.overall_risk_score == 50.0
        assert assessment.risk_category == "medium"


class TestRiskAssessmentFramework:
    """Tests for RiskAssessmentFramework."""

    def test_framework_initialization(self):
        """Test framework initialization."""
        framework = RiskAssessmentFramework()
        assert framework is not None

    def test_calculate_risk_score(self):
        """Test risk score calculation."""
        framework = RiskAssessmentFramework()
        score = framework.calculate_risk_score(
            RiskSeverity.HIGH,
            RiskImpact.SIGNIFICANT,
            RiskLikelihood.LIKELY,
        )
        assert 0.0 <= score <= 100.0

    def test_determine_risk_category(self):
        """Test risk category determination."""
        framework = RiskAssessmentFramework()
        assert framework.determine_risk_category(20.0) == "low"
        assert framework.determine_risk_category(40.0) == "medium"
        assert framework.determine_risk_category(60.0) == "high"
        assert framework.determine_risk_category(80.0) == "critical"

    def test_add_threshold(self):
        """Test adding a risk threshold."""
        framework = RiskAssessmentFramework()
        threshold = RiskThreshold(
            threshold_id="threshold1",
            risk_type=RiskType.TECHNICAL,
            maximum_acceptable_score=50.0,
        )
        result = framework.add_threshold(threshold)
        assert result is True

    def test_get_threshold(self):
        """Test getting a risk threshold."""
        framework = RiskAssessmentFramework()
        threshold = RiskThreshold(
            threshold_id="threshold1",
            risk_type=RiskType.TECHNICAL,
            maximum_acceptable_score=50.0,
        )
        framework.add_threshold(threshold)
        retrieved = framework.get_threshold("threshold1")
        assert retrieved is not None
        assert retrieved.threshold_id == "threshold1"
