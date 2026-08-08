import pytest

from app.expert_domains.work.requirements import (
    ClientRequirements,
    Requirement,
    RequirementType,
    RequirementPriority,
    BudgetConstraint,
    TimelineConstraint,
    PlatformConstraint,
    ComplianceRequirement,
)


class TestRequirement:
    """Tests for Requirement."""

    def test_requirement_creation(self):
        """Test creating a requirement."""
        req = Requirement(
            requirement_id="req1",
            requirement_type=RequirementType.FUNCTIONAL,
            title="Must support dark mode",
            description="The application must support dark mode",
        )
        assert req.requirement_id == "req1"
        assert req.requirement_type == RequirementType.FUNCTIONAL
        assert req.priority == RequirementPriority.MEDIUM
        assert req.is_mandatory is True

    def test_requirement_with_acceptance_criteria(self):
        """Test requirement with acceptance criteria."""
        req = Requirement(
            requirement_id="req1",
            requirement_type=RequirementType.FUNCTIONAL,
            title="Must support dark mode",
            description="The application must support dark mode",
            acceptance_criteria=["Dark mode toggle works", "Colors are accessible"],
            priority=RequirementPriority.HIGH,
        )
        assert len(req.acceptance_criteria) == 2
        assert req.priority == RequirementPriority.HIGH


class TestBudgetConstraint:
    """Tests for BudgetConstraint."""

    def test_budget_constraint_creation(self):
        """Test creating a budget constraint."""
        constraint = BudgetConstraint(
            constraint_id="budget1",
            maximum_budget=5000.0,
            currency="USD",
            billing_type="fixed",
        )
        assert constraint.constraint_id == "budget1"
        assert constraint.maximum_budget == 5000.0
        assert constraint.currency == "USD"
        assert constraint.billing_type == "fixed"


class TestTimelineConstraint:
    """Tests for TimelineConstraint."""

    def test_timeline_constraint_creation(self):
        """Test creating a timeline constraint."""
        constraint = TimelineConstraint(
            constraint_id="timeline1",
            duration="2 weeks",
            urgency="normal",
        )
        assert constraint.constraint_id == "timeline1"
        assert constraint.duration == "2 weeks"
        assert constraint.urgency == "normal"


class TestPlatformConstraint:
    """Tests for PlatformConstraint."""

    def test_platform_constraint_creation(self):
        """Test creating a platform constraint."""
        constraint = PlatformConstraint(
            constraint_id="platform1",
            platform_name="WordPress",
            platform_version="6.0",
            required_features=["REST API"],
        )
        assert constraint.constraint_id == "platform1"
        assert constraint.platform_name == "WordPress"
        assert constraint.platform_version == "6.0"
        assert len(constraint.required_features) == 1


class TestComplianceRequirement:
    """Tests for ComplianceRequirement."""

    def test_compliance_requirement_creation(self):
        """Test creating a compliance requirement."""
        requirement = ComplianceRequirement(
            requirement_id="compliance1",
            compliance_type="GDPR",
            description="Must comply with GDPR",
            required_actions=["Implement consent management"],
            documentation_required=True,
        )
        assert requirement.requirement_id == "compliance1"
        assert requirement.compliance_type == "GDPR"
        assert requirement.documentation_required is True


class TestClientRequirements:
    """Tests for ClientRequirements."""

    def test_client_requirements_creation(self):
        """Test creating client requirements."""
        reqs = ClientRequirements(
            requirements_id="reqs1",
            work_id="work1",
        )
        assert reqs.requirements_id == "reqs1"
        assert reqs.work_id == "work1"

    def test_client_requirements_with_components(self):
        """Test client requirements with all components."""
        functional_req = Requirement(
            requirement_id="req1",
            requirement_type=RequirementType.FUNCTIONAL,
            title="Must support dark mode",
            description="The application must support dark mode",
        )
        budget = BudgetConstraint(
            constraint_id="budget1",
            maximum_budget=5000.0,
        )
        timeline = TimelineConstraint(
            constraint_id="timeline1",
            duration="2 weeks",
        )

        reqs = ClientRequirements(
            requirements_id="reqs1",
            work_id="work1",
            functional_requirements=[functional_req],
            budget_constraints=[budget],
            timeline_constraints=[timeline],
            success_expectations=["Delivered on time", "Within budget"],
        )
        assert len(reqs.functional_requirements) == 1
        assert len(reqs.budget_constraints) == 1
        assert len(reqs.timeline_constraints) == 1
        assert len(reqs.success_expectations) == 2
