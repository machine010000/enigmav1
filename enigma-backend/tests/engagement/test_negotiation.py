import pytest
from datetime import datetime

from app.engagement.negotiation import (
    NegotiationItemType,
    NegotiationStatus,
    NegotiationPriority,
    NegotiationItem,
    NegotiationRecord,
    NegotiationTemplate,
    NegotiationFramework,
)


class TestNegotiationItem:
    """Tests for NegotiationItem."""

    def test_negotiation_item_creation(self):
        """Test creating a negotiation item."""
        item = NegotiationItem(
            item_id="item1",
            item_type=NegotiationItemType.QUESTION,
            work_specification_id="work1",
            description="Need clarification on scope",
            current_value="Current scope",
            proposed_value="Proposed scope",
            priority=NegotiationPriority.HIGH,
        )
        assert item.item_id == "item1"
        assert item.item_type == NegotiationItemType.QUESTION
        assert item.priority == NegotiationPriority.HIGH


class TestNegotiationRecord:
    """Tests for NegotiationRecord."""

    def test_negotiation_record_creation(self):
        """Test creating a negotiation record."""
        record = NegotiationRecord(
            record_id="record1",
            work_specification_id="work1",
        )
        assert record.record_id == "record1"
        assert record.status == "active"


class TestNegotiationTemplate:
    """Tests for NegotiationTemplate."""

    def test_negotiation_template_creation(self):
        """Test creating a negotiation template."""
        template = NegotiationTemplate(
            template_id="template1",
            scenario_type="scope",
            name="Scope Negotiation Template",
            description="Template for scope negotiations",
            standard_questions=["What is the timeline?"],
        )
        assert template.template_id == "template1"
        assert template.scenario_type == "scope"


class TestNegotiationFramework:
    """Tests for NegotiationFramework."""

    def test_framework_initialization(self):
        """Test framework initialization."""
        framework = NegotiationFramework()
        assert framework is not None

    def test_create_negotiation_item(self):
        """Test creating a negotiation item."""
        framework = NegotiationFramework()
        item = framework.create_negotiation_item(
            item_id="item1",
            item_type=NegotiationItemType.QUESTION,
            work_specification_id="work1",
            description="Need clarification",
            current_value="Current",
            proposed_value="Proposed",
        )
        assert item.item_id == "item1"

    def test_start_negotiation(self):
        """Test starting a negotiation."""
        framework = NegotiationFramework()
        record = framework.start_negotiation(
            record_id="record1",
            work_specification_id="work1",
        )
        assert record.record_id == "record1"
        assert record.status == "active"

    def test_register_template(self):
        """Test registering a negotiation template."""
        framework = NegotiationFramework()
        template = NegotiationTemplate(
            template_id="template1",
            scenario_type="scope",
            name="Scope Template",
            description="Scope negotiation template",
        )
        result = framework.register_template(template)
        assert result is True

    def test_get_template(self):
        """Test getting a negotiation template."""
        framework = NegotiationFramework()
        template = NegotiationTemplate(
            template_id="template1",
            scenario_type="scope",
            name="Scope Template",
            description="Scope negotiation template",
        )
        framework.register_template(template)
        retrieved = framework.get_template("template1")
        assert retrieved is not None
        assert retrieved.template_id == "template1"
