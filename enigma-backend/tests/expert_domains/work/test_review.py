import pytest

from app.expert_domains.work.review import (
    Review,
    ReviewType,
    ReviewStatus,
    ReviewDecision,
    ReviewChecklistItem,
    ReviewChecklist,
    ReviewValidationRule,
    ReviewApproval,
    ReviewPolicy,
)


class TestReviewChecklistItem:
    """Tests for ReviewChecklistItem."""

    def test_review_checklist_item_creation(self):
        """Test creating a review checklist item."""
        item = ReviewChecklistItem(
            item_id="item1",
            title="Check formatting",
            description="Verify document formatting",
            is_required=True,
            weight=1.0,
        )
        assert item.item_id == "item1"
        assert item.is_required is True
        assert item.weight == 1.0


class TestReviewChecklist:
    """Tests for ReviewChecklist."""

    def test_review_checklist_creation(self):
        """Test creating a review checklist."""
        checklist = ReviewChecklist(
            checklist_id="check1",
            name="Quality Review Checklist",
            description="Checklist for quality reviews",
            review_type=ReviewType.QUALITY,
            checklist_items=[
                ReviewChecklistItem(
                    item_id="item1",
                    title="Check formatting",
                    description="Verify document formatting",
                )
            ],
        )
        assert checklist.checklist_id == "check1"
        assert checklist.review_type == ReviewType.QUALITY
        assert len(checklist.checklist_items) == 1


class TestReviewValidationRule:
    """Tests for ReviewValidationRule."""

    def test_review_validation_rule_creation(self):
        """Test creating a review validation rule."""
        rule = ReviewValidationRule(
            rule_id="rule1",
            name="Mandatory approval",
            description="All required items must be approved",
            rule_type="mandatory",
            action_on_failure="block",
        )
        assert rule.rule_id == "rule1"
        assert rule.rule_type == "mandatory"
        assert rule.action_on_failure == "block"


class TestReview:
    """Tests for Review."""

    def test_review_creation(self):
        """Test creating a review."""
        review = Review(
            review_id="rev1",
            target_type="deliverable",
            target_id="del1",
            review_type=ReviewType.QUALITY,
            reviewer="quality_specialist",
        )
        assert review.review_id == "rev1"
        assert review.target_type == "deliverable"
        assert review.review_type == ReviewType.QUALITY
        assert review.status == ReviewStatus.PENDING

    def test_review_with_decision(self):
        """Test review with decision."""
        review = Review(
            review_id="rev1",
            target_type="deliverable",
            target_id="del1",
            review_type=ReviewType.QUALITY,
            reviewer="quality_specialist",
            status=ReviewStatus.COMPLETED,
            decision=ReviewDecision.APPROVED,
            overall_score=0.9,
        )
        assert review.status == ReviewStatus.COMPLETED
        assert review.decision == ReviewDecision.APPROVED
        assert review.overall_score == 0.9


class TestReviewApproval:
    """Tests for ReviewApproval."""

    def test_review_approval_creation(self):
        """Test creating a review approval."""
        approval = ReviewApproval(
            approval_id="app1",
            review_id="rev1",
            approver="manager",
            approval_status="approved",
            comments="Approved with minor changes",
        )
        assert approval.approval_id == "app1"
        assert approval.review_id == "rev1"
        assert approval.approver == "manager"
        assert approval.approval_status == "approved"


class TestReviewPolicy:
    """Tests for ReviewPolicy."""

    def test_review_policy_creation(self):
        """Test creating a review policy."""
        policy = ReviewPolicy(
            policy_id="policy1",
            name="Standard Review Policy",
            description="Standard policy for deliverable reviews",
            target_type="deliverable",
            required_review_types=[ReviewType.QUALITY, ReviewType.TECHNICAL],
            minimum_reviewers=2,
            required_approvals=1,
        )
        assert policy.policy_id == "policy1"
        assert policy.target_type == "deliverable"
        assert len(policy.required_review_types) == 2
        assert policy.minimum_reviewers == 2
        assert policy.required_approvals == 1
