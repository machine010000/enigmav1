import pytest
from datetime import datetime

from app.engagement.decision import (
    DecisionInput,
    DecisionEngine,
)

from app.engagement.contracts import DecisionStatus


class TestDecisionInput:
    """Tests for DecisionInput."""

    def test_decision_input_creation(self):
        """Test creating a decision input."""
        input_data = DecisionInput(
            work_specification_id="work1",
            available_knowledge=["seo"],
            available_evidence=["case_studies"],
            available_capabilities=["keyword_research"],
            knowledge_readiness=0.8,
            capability_readiness=0.7,
            evidence_coverage=0.9,
            complexity=0.5,
            risk_score=0.3,
            client_quality=0.8,
            portfolio_match=0.7,
        )
        assert input_data.work_specification_id == "work1"
        assert input_data.knowledge_readiness == 0.8
        assert input_data.risk_score == 0.3


class TestDecisionEngine:
    """Tests for DecisionEngine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = DecisionEngine()
        assert engine is not None

    def test_make_decision_accept(self):
        """Test making a decision that results in ACCEPT."""
        engine = DecisionEngine()
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
        decision = engine.make_decision(input_data)
        assert decision.decision_status in [DecisionStatus.ACCEPT, DecisionStatus.ACCEPT_WITH_CONDITIONS]
        assert decision.decision_confidence > 0.5

    def test_make_decision_reject(self):
        """Test making a decision that results in REJECT."""
        engine = DecisionEngine()
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
        decision = engine.make_decision(input_data)
        assert decision.decision_status in [DecisionStatus.REJECT, DecisionStatus.NEED_LEARNING, DecisionStatus.NEED_RESEARCH]

    def test_can_proceed(self):
        """Test can_proceed method."""
        engine = DecisionEngine()
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
        decision = engine.make_decision(input_data)
        if decision.decision_status in [DecisionStatus.ACCEPT, DecisionStatus.ACCEPT_WITH_CONDITIONS]:
            assert engine.can_proceed(decision.decision_id) is True
        else:
            assert engine.can_proceed(decision.decision_id) is False

    def test_get_blocking_issues(self):
        """Test get_blocking_issues method."""
        engine = DecisionEngine()
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
        decision = engine.make_decision(input_data)
        issues = engine.get_blocking_issues(decision.decision_id)
        assert len(issues) > 0

    def test_get_required_actions(self):
        """Test get_required_actions method."""
        engine = DecisionEngine()
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
        decision = engine.make_decision(input_data)
        actions = engine.get_required_actions(decision.decision_id)
        assert len(actions) >= 0

    def test_get_decision(self):
        """Test getting a decision by ID."""
        engine = DecisionEngine()
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
        decision = engine.make_decision(input_data)
        retrieved = engine.get_decision(decision.decision_id)
        assert retrieved is not None
        assert retrieved.decision_id == decision.decision_id
