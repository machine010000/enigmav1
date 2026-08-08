import pytest
from datetime import datetime

from app.engagement.scope import (
    ScopeStatus,
    ScopeIssueType,
    ScopeIssue,
    ScopeValidation,
    ScopeRequirement,
    ScopeValidationFramework,
)


class TestScopeIssue:
    """Tests for ScopeIssue."""

    def test_scope_issue_creation(self):
        """Test creating a scope issue."""
        issue = ScopeIssue(
            issue_id="issue1",
            issue_type=ScopeIssueType.MISSING_REQUIREMENTS,
            description="Requirements are missing",
            severity="high",
            blocking=True,
        )
        assert issue.issue_id == "issue1"
        assert issue.issue_type == ScopeIssueType.MISSING_REQUIREMENTS
        assert issue.blocking is True


class TestScopeValidation:
    """Tests for ScopeValidation."""

    def test_scope_validation_creation(self):
        """Test creating a scope validation."""
        validation = ScopeValidation(
            validation_id="validation1",
            work_specification_id="work1",
            scope_status=ScopeStatus.CLEAR,
            clarity_score=1.0,
            completeness_score=1.0,
            feasibility_score=1.0,
            overall_score=1.0,
        )
        assert validation.validation_id == "validation1"
        assert validation.scope_status == ScopeStatus.CLEAR
        assert validation.overall_score == 1.0


class TestScopeValidationFramework:
    """Tests for ScopeValidationFramework."""

    def test_framework_initialization(self):
        """Test framework initialization."""
        framework = ScopeValidationFramework()
        assert framework is not None

    def test_validate_scope_clear(self):
        """Test scope validation with clear scope."""
        framework = ScopeValidationFramework()
        validation = framework.validate_scope(
            work_specification_id="work1",
            has_objectives=True,
            has_deliverables=True,
            has_timeline=True,
            has_budget=True,
            has_requirements=True,
        )
        assert validation.scope_status == ScopeStatus.CLEAR
        assert validation.overall_score > 0.8

    def test_validate_scope_missing(self):
        """Test scope validation with missing elements."""
        framework = ScopeValidationFramework()
        validation = framework.validate_scope(
            work_specification_id="work1",
            has_objectives=False,
            has_deliverables=False,
            has_timeline=True,
            has_budget=True,
            has_requirements=True,
        )
        # Missing objectives and deliverables are blocking, so status is AMBIGUOUS
        assert validation.scope_status in [ScopeStatus.MISSING, ScopeStatus.AMBIGUOUS]
        assert len(validation.missing_elements) > 0

    def test_can_proceed(self):
        """Test can_proceed method."""
        framework = ScopeValidationFramework()
        validation = framework.validate_scope(
            work_specification_id="work1",
            has_objectives=True,
            has_deliverables=True,
            has_timeline=True,
            has_budget=True,
            has_requirements=True,
        )
        assert framework.can_proceed(validation) is True

    def test_get_blocking_issues(self):
        """Test get_blocking_issues method."""
        framework = ScopeValidationFramework()
        validation = framework.validate_scope(
            work_specification_id="work1",
            has_objectives=False,
            has_deliverables=False,
            has_timeline=True,
            has_budget=True,
            has_requirements=True,
        )
        blocking = framework.get_blocking_issues(validation)
        assert len(blocking) > 0
