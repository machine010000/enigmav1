import pytest

from app.expert_domains.work.deliverables import (
    Deliverable,
    DeliverableType,
    DeliverableFormat,
    DeliverableStatus,
    DeliverableInstance,
    DeliverableRequirement,
)


class TestDeliverable:
    """Tests for Deliverable."""

    def test_deliverable_creation(self):
        """Test creating a deliverable."""
        deliverable = Deliverable(
            deliverable_id="del1",
            name="SEO Audit Report",
            description="Comprehensive SEO audit report",
            deliverable_type=DeliverableType.REPORT,
            format=DeliverableFormat.PDF,
            expected_audience="Client",
            quality_standard="High",
            validation_method="Manual review",
        )
        assert deliverable.deliverable_id == "del1"
        assert deliverable.deliverable_type == DeliverableType.REPORT
        assert deliverable.format == DeliverableFormat.PDF

    def test_deliverable_with_sections(self):
        """Test deliverable with required and optional sections."""
        deliverable = Deliverable(
            deliverable_id="del1",
            name="SEO Audit Report",
            description="Comprehensive SEO audit report",
            deliverable_type=DeliverableType.REPORT,
            format=DeliverableFormat.PDF,
            expected_audience="Client",
            quality_standard="High",
            validation_method="Manual review",
            required_sections=["Executive Summary", "Technical Analysis", "Recommendations"],
            optional_sections=["Appendix"],
        )
        assert len(deliverable.required_sections) == 3
        assert len(deliverable.optional_sections) == 1


class TestDeliverableInstance:
    """Tests for DeliverableInstance."""

    def test_deliverable_instance_creation(self):
        """Test creating a deliverable instance."""
        instance = DeliverableInstance(
            instance_id="inst1",
            deliverable_id="del1",
            work_id="work1",
        )
        assert instance.instance_id == "inst1"
        assert instance.deliverable_id == "del1"
        assert instance.work_id == "work1"
        assert instance.status == DeliverableStatus.NOT_STARTED

    def test_deliverable_instance_with_status(self):
        """Test deliverable instance with approved status."""
        instance = DeliverableInstance(
            instance_id="inst1",
            deliverable_id="del1",
            work_id="work1",
            status=DeliverableStatus.APPROVED,
            version="1.0",
            approved_by="client",
        )
        assert instance.status == DeliverableStatus.APPROVED
        assert instance.version == "1.0"
        assert instance.approved_by == "client"


class TestDeliverableRequirement:
    """Tests for DeliverableRequirement."""

    def test_deliverable_requirement_creation(self):
        """Test creating a deliverable requirement."""
        req = DeliverableRequirement(
            requirement_id="req1",
            deliverable_id="del1",
            requirement_type="content",
            description="Must include executive summary",
            is_mandatory=True,
            priority="high",
        )
        assert req.requirement_id == "req1"
        assert req.deliverable_id == "del1"
        assert req.requirement_type == "content"
        assert req.is_mandatory is True
