import pytest

from app.expert_domains.work.acceptance import (
    AcceptanceCriterion,
    AcceptancePriority,
    MeasurementType,
    ValidationMethod,
    AcceptanceCriteriaSet,
    AcceptanceResult,
    AcceptanceChecklist,
)


class TestAcceptanceCriterion:
    """Tests for AcceptanceCriterion."""

    def test_acceptance_criterion_creation(self):
        """Test creating an acceptance criterion."""
        criterion = AcceptanceCriterion(
            criterion_id="crit1",
            requirement="Response time < 200ms",
            description="API response time must be under 200ms",
            measurement_type=MeasurementType.THRESHOLD,
            threshold_value=200.0,
            validation_method=ValidationMethod.AUTOMATED,
        )
        assert criterion.criterion_id == "crit1"
        assert criterion.measurement_type == MeasurementType.THRESHOLD
        assert criterion.threshold_value == 200.0
        assert criterion.validation_method == ValidationMethod.AUTOMATED

    def test_acceptance_criterion_with_range(self):
        """Test acceptance criterion with range measurement."""
        criterion = AcceptanceCriterion(
            criterion_id="crit1",
            requirement="Coverage between 80-90%",
            description="Code coverage must be between 80-90%",
            measurement_type=MeasurementType.RANGE,
            threshold_min=80.0,
            threshold_max=90.0,
        )
        assert criterion.measurement_type == MeasurementType.RANGE
        assert criterion.threshold_min == 80.0
        assert criterion.threshold_max == 90.0


class TestAcceptanceCriteriaSet:
    """Tests for AcceptanceCriteriaSet."""

    def test_acceptance_criteria_set_creation(self):
        """Test creating an acceptance criteria set."""
        criteria_set = AcceptanceCriteriaSet(
            criteria_set_id="set1",
            name="API Quality Criteria",
            description="Quality criteria for API deliverables",
            target_type="deliverable",
            target_id="del1",
        )
        assert criteria_set.criteria_set_id == "set1"
        assert criteria_set.target_type == "deliverable"
        assert criteria_set.target_id == "del1"

    def test_acceptance_criteria_set_with_criteria(self):
        """Test acceptance criteria set with criteria."""
        criterion1 = AcceptanceCriterion(
            criterion_id="crit1",
            requirement="Response time < 200ms",
            description="API response time must be under 200ms",
            measurement_type=MeasurementType.THRESHOLD,
            threshold_value=200.0,
        )
        criterion2 = AcceptanceCriterion(
            criterion_id="crit2",
            requirement="Availability > 99%",
            description="API availability must be over 99%",
            measurement_type=MeasurementType.THRESHOLD,
            threshold_value=99.0,
        )
        criteria_set = AcceptanceCriteriaSet(
            criteria_set_id="set1",
            name="API Quality Criteria",
            description="Quality criteria for API deliverables",
            target_type="deliverable",
            target_id="del1",
            criteria=[criterion1, criterion2],
            overall_pass_threshold=1.0,
        )
        assert len(criteria_set.criteria) == 2
        assert criteria_set.overall_pass_threshold == 1.0


class TestAcceptanceResult:
    """Tests for AcceptanceResult."""

    def test_acceptance_result_creation(self):
        """Test creating an acceptance result."""
        result = AcceptanceResult(
            result_id="res1",
            criteria_set_id="set1",
            target_id="del1",
            passed=True,
            passed_criteria=["crit1", "crit2"],
            overall_score=1.0,
        )
        assert result.result_id == "res1"
        assert result.passed is True
        assert len(result.passed_criteria) == 2
        assert result.overall_score == 1.0

    def test_acceptance_result_with_failures(self):
        """Test acceptance result with failures."""
        result = AcceptanceResult(
            result_id="res1",
            criteria_set_id="set1",
            target_id="del1",
            passed=False,
            passed_criteria=["crit1"],
            failed_criteria=["crit2"],
            overall_score=0.5,
        )
        assert result.passed is False
        assert len(result.failed_criteria) == 1
        assert result.overall_score == 0.5


class TestAcceptanceChecklist:
    """Tests for AcceptanceChecklist."""

    def test_acceptance_checklist_creation(self):
        """Test creating an acceptance checklist."""
        checklist = AcceptanceChecklist(
            checklist_id="check1",
            name="Deliverable Checklist",
            description="Checklist for deliverable validation",
            checklist_items=[
                {"item": "Executive Summary", "required": True},
                {"item": "Technical Analysis", "required": True},
            ],
            requires_evidence=True,
            requires_signoff=True,
        )
        assert checklist.checklist_id == "check1"
        assert len(checklist.checklist_items) == 2
        assert checklist.requires_evidence is True
        assert checklist.requires_signoff is True
