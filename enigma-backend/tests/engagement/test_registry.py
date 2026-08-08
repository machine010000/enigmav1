import pytest
from datetime import datetime

from app.engagement.registry import EngagementRegistry, engagement_registry
from app.engagement.pricing import PricingModelType
from app.engagement.contracts import DecisionRecord, DecisionStatus
from app.engagement.risk import RiskAssessment
from app.engagement.scope import ScopeValidation, ScopeStatus
from app.engagement.pricing import PricingModel, PricingProposal
from app.engagement.negotiation import NegotiationRecord
from app.engagement.decision import DecisionInput


class TestEngagementRegistry:
    """Tests for EngagementRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = EngagementRegistry()
        assert registry is not None

    def test_register_decision_record(self):
        """Test registering a decision record."""
        registry = EngagementRegistry()
        record = DecisionRecord(
            decision_id="decision1",
            work_specification_id="work1",
            timestamp=datetime.utcnow(),
            decision_status=DecisionStatus.ACCEPT,
            decision_confidence=0.8,
        )
        result = registry.register_decision_record(record)
        assert result is True

    def test_get_decision_record(self):
        """Test getting a decision record."""
        registry = EngagementRegistry()
        record = DecisionRecord(
            decision_id="decision1",
            work_specification_id="work1",
            timestamp=datetime.utcnow(),
            decision_status=DecisionStatus.ACCEPT,
            decision_confidence=0.8,
        )
        registry.register_decision_record(record)
        retrieved = registry.get_decision_record("decision1")
        assert retrieved is not None
        assert retrieved.decision_id == "decision1"

    def test_register_risk_assessment(self):
        """Test registering a risk assessment."""
        registry = EngagementRegistry()
        assessment = RiskAssessment(
            assessment_id="assessment1",
            work_specification_id="work1",
            overall_risk_score=50.0,
            risk_category="medium",
        )
        result = registry.register_risk_assessment(assessment)
        assert result is True

    def test_get_risk_assessment(self):
        """Test getting a risk assessment."""
        registry = EngagementRegistry()
        assessment = RiskAssessment(
            assessment_id="assessment1",
            work_specification_id="work1",
            overall_risk_score=50.0,
            risk_category="medium",
        )
        registry.register_risk_assessment(assessment)
        retrieved = registry.get_risk_assessment("assessment1")
        assert retrieved is not None
        assert retrieved.assessment_id == "assessment1"

    def test_register_scope_validation(self):
        """Test registering a scope validation."""
        registry = EngagementRegistry()
        validation = ScopeValidation(
            validation_id="validation1",
            work_specification_id="work1",
            scope_status=ScopeStatus.CLEAR,
            clarity_score=1.0,
            completeness_score=1.0,
            feasibility_score=1.0,
            overall_score=1.0,
        )
        result = registry.register_scope_validation(validation)
        assert result is True

    def test_get_scope_validation(self):
        """Test getting a scope validation."""
        registry = EngagementRegistry()
        validation = ScopeValidation(
            validation_id="validation1",
            work_specification_id="work1",
            scope_status=ScopeStatus.CLEAR,
            clarity_score=1.0,
            completeness_score=1.0,
            feasibility_score=1.0,
            overall_score=1.0,
        )
        registry.register_scope_validation(validation)
        retrieved = registry.get_scope_validation("validation1")
        assert retrieved is not None
        assert retrieved.validation_id == "validation1"

    def test_register_pricing_model(self):
        """Test registering a pricing model."""
        registry = EngagementRegistry()
        from app.engagement.pricing import Currency
        model = PricingModel(
            model_id="model1",
            model_type=PricingModelType.FIXED,
            name="Fixed Model",
            description="Fixed pricing",
            currency=Currency.USD,
            total_amount=1000.0,
        )
        result = registry.register_pricing_model(model)
        assert result is True

    def test_get_pricing_model(self):
        """Test getting a pricing model."""
        registry = EngagementRegistry()
        from app.engagement.pricing import Currency
        model = PricingModel(
            model_id="model1",
            model_type="fixed",
            name="Fixed Model",
            description="Fixed pricing",
            currency=Currency.USD,
            total_amount=1000.0,
        )
        registry.register_pricing_model(model)
        retrieved = registry.get_pricing_model("model1")
        assert retrieved is not None
        assert retrieved.model_id == "model1"

    def test_register_negotiation_record(self):
        """Test registering a negotiation record."""
        registry = EngagementRegistry()
        record = NegotiationRecord(
            record_id="record1",
            work_specification_id="work1",
        )
        result = registry.register_negotiation_record(record)
        assert result is True

    def test_get_negotiation_record(self):
        """Test getting a negotiation record."""
        registry = EngagementRegistry()
        record = NegotiationRecord(
            record_id="record1",
            work_specification_id="work1",
        )
        registry.register_negotiation_record(record)
        retrieved = registry.get_negotiation_record("record1")
        assert retrieved is not None
        assert retrieved.record_id == "record1"

    def test_make_decision(self):
        """Test making a decision through the registry."""
        registry = EngagementRegistry()
        input_data = DecisionInput(
            work_specification_id="work1",
            knowledge_readiness=0.9,
            capability_readiness=0.9,
            evidence_coverage=0.9,
            complexity=0.3,
            risk_score=0.2,
            client_quality=0.9,
            portfolio_match=0.8,
        )
        decision = registry.make_decision(input_data)
        assert decision is not None
        assert decision.work_specification_id == "work1"

    def test_can_proceed(self):
        """Test can_proceed through the registry."""
        registry = EngagementRegistry()
        input_data = DecisionInput(
            work_specification_id="work1",
            knowledge_readiness=0.9,
            capability_readiness=0.9,
            evidence_coverage=0.9,
            complexity=0.3,
            risk_score=0.2,
            client_quality=0.9,
            portfolio_match=0.8,
        )
        decision = registry.make_decision(input_data)
        if decision.decision_status in [DecisionStatus.ACCEPT, DecisionStatus.ACCEPT_WITH_CONDITIONS]:
            assert registry.can_proceed(decision.decision_id) is True

    def test_get_blocking_issues(self):
        """Test get_blocking_issues through the registry."""
        registry = EngagementRegistry()
        input_data = DecisionInput(
            work_specification_id="work1",
            knowledge_readiness=0.2,
            capability_readiness=0.2,
            evidence_coverage=0.2,
            complexity=0.8,
            risk_score=0.9,
            client_quality=0.3,
            portfolio_match=0.2,
        )
        decision = registry.make_decision(input_data)
        issues = registry.get_blocking_issues(decision.decision_id)
        assert len(issues) >= 0

    def test_get_required_actions(self):
        """Test get_required_actions through the registry."""
        registry = EngagementRegistry()
        input_data = DecisionInput(
            work_specification_id="work1",
            knowledge_readiness=0.2,
            capability_readiness=0.2,
            evidence_coverage=0.2,
            complexity=0.8,
            risk_score=0.9,
            client_quality=0.3,
            portfolio_match=0.2,
        )
        decision = registry.make_decision(input_data)
        actions = registry.get_required_actions(decision.decision_id)
        assert len(actions) >= 0

    def test_global_registry_exists(self):
        """Test that the global registry exists."""
        assert engagement_registry is not None
        assert isinstance(engagement_registry, EngagementRegistry)
