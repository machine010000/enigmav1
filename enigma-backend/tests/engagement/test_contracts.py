import pytest
from datetime import datetime

from app.engagement.contracts import (
    DecisionStatus,
    DecisionPriority,
    DecisionRecord,
    DecisionGate,
    DecisionRequirement,
)


class TestDecisionStatus:
    """Tests for DecisionStatus enum."""

    def test_decision_status_values(self):
        """Test decision status values."""
        assert DecisionStatus.PENDING.value == "pending"
        assert DecisionStatus.NEED_RESEARCH.value == "need_research"
        assert DecisionStatus.NEED_LEARNING.value == "need_learning"
        assert DecisionStatus.NEED_NEGOTIATION.value == "need_negotiation"
        assert DecisionStatus.NEED_CLARIFICATION.value == "need_clarification"
        assert DecisionStatus.NEED_PORTFOLIO.value == "need_portfolio"
        assert DecisionStatus.REJECT.value == "reject"
        assert DecisionStatus.ACCEPT.value == "accept"
        assert DecisionStatus.ACCEPT_WITH_CONDITIONS.value == "accept_with_conditions"


class TestDecisionRecord:
    """Tests for DecisionRecord."""

    def test_decision_record_creation(self):
        """Test creating a decision record."""
        record = DecisionRecord(
            decision_id="decision1",
            work_specification_id="work1",
            timestamp=datetime.utcnow(),
            decision_status=DecisionStatus.ACCEPT,
            decision_confidence=0.8,
        )
        assert record.decision_id == "decision1"
        assert record.work_specification_id == "work1"
        assert record.decision_status == DecisionStatus.ACCEPT
        assert record.decision_confidence == 0.8

    def test_decision_record_with_gaps(self):
        """Test decision record with gaps."""
        record = DecisionRecord(
            decision_id="decision1",
            work_specification_id="work1",
            timestamp=datetime.utcnow(),
            decision_status=DecisionStatus.NEED_LEARNING,
            decision_confidence=0.6,
            missing_knowledge=["keyword_research"],
            missing_evidence=["case_studies"],
            missing_capabilities=["technical_seo"],
        )
        assert len(record.missing_knowledge) == 1
        assert len(record.missing_evidence) == 1
        assert len(record.missing_capabilities) == 1


class TestDecisionGate:
    """Tests for DecisionGate."""

    def test_decision_gate_creation(self):
        """Test creating a decision gate."""
        gate = DecisionGate(
            gate_id="execution_gate",
            name="Execution Gate",
            description="Gate that controls execution",
            required_status=[DecisionStatus.ACCEPT, DecisionStatus.ACCEPT_WITH_CONDITIONS],
            blocked_status=[DecisionStatus.REJECT, DecisionStatus.NEED_RESEARCH],
        )
        assert gate.gate_id == "execution_gate"
        assert len(gate.required_status) == 2
        assert len(gate.blocked_status) == 2


class TestDecisionRequirement:
    """Tests for DecisionRequirement."""

    def test_decision_requirement_creation(self):
        """Test creating a decision requirement."""
        requirement = DecisionRequirement(
            requirement_id="req1",
            requirement_type="knowledge",
            description="Knowledge about SEO required",
            is_blocking=True,
            priority="high",
        )
        assert requirement.requirement_id == "req1"
        assert requirement.requirement_type == "knowledge"
        assert requirement.is_blocking is True
        assert requirement.priority == "high"
