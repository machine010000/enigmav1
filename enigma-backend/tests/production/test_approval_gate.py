"""
Tests for Human Approval Gate.

These tests verify that the approval gate enforces mandatory
human approval before application submission.
"""
import pytest
from datetime import datetime

from app.work_market.approval_gate import (
    ApprovalGate,
    ApprovalState,
    ApprovalRequest,
)
from app.work_market.application_package import (
    ApplicationPackage,
    ApplicationStatus,
    ApprovalDecision,
    Proposal,
)
from app.work_market.proposal_strategy import (
    ProposalStrategy,
    ProposalTone,
)


class TestApprovalGate:
    """Test approval gate functionality."""
    
    def test_request_approval_creates_pending_request(self):
        """Test that requesting approval creates a pending request."""
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test job understanding",
                proposed_approach="Test approach",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
        )
        
        request = gate.request_approval(package, requested_by="user_123")
        
        assert request.application_package == package
        assert request.requested_by == "user_123"
        assert package.status == ApplicationStatus.WAITING_FOR_APPROVAL
        assert len(gate.get_pending_approvals()) == 1
    
    def test_approve_application_updates_status(self):
        """Test that approving an application updates its status."""
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test job understanding",
                proposed_approach="Test approach",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
        )
        
        gate.request_approval(package, requested_by="user_123")
        approved = gate.approve_application("app_001", approved_by="admin_456")
        
        assert approved.status == ApplicationStatus.APPROVED
        assert approved.approval_decision == ApprovalDecision.APPROVED
        assert approved.approved_by == "admin_456"
        assert approved.approved_at is not None
        assert len(gate.get_pending_approvals()) == 0
    
    def test_reject_application_updates_status(self):
        """Test that rejecting an application updates its status."""
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test job understanding",
                proposed_approach="Test approach",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
        )
        
        gate.request_approval(package, requested_by="user_123")
        rejected = gate.reject_application("app_001", rejected_by="admin_456")
        
        assert rejected.status == ApplicationStatus.REJECTED
        assert rejected.approval_decision == ApprovalDecision.REJECTED
        assert rejected.approved_by == "admin_456"
        assert len(gate.get_pending_approvals()) == 0
    
    def test_request_revision_returns_to_draft(self):
        """Test that requesting revision returns application to draft."""
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test job understanding",
                proposed_approach="Test approach",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
        )
        
        gate.request_approval(package, requested_by="user_123")
        revised = gate.request_revision("app_001", requested_by="admin_456")
        
        assert revised.status == ApplicationStatus.DRAFT
        assert revised.approval_decision == ApprovalDecision.REVISION_REQUESTED
        assert len(gate.get_pending_approvals()) == 0
    
    def test_can_submit_only_when_approved(self):
        """Test that application can only be submitted when approved."""
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test job understanding",
                proposed_approach="Test approach",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
        )
        
        # Cannot submit when draft
        assert gate.can_submit(package) is False
        
        # Request approval
        gate.request_approval(package, requested_by="user_123")
        
        # Cannot submit when waiting for approval
        assert gate.can_submit(package) is False
        
        # Approve
        gate.approve_application("app_001", approved_by="admin_456")
        
        # Can submit when approved
        assert gate.can_submit(package) is True
    
    def test_cannot_approve_non_pending_application(self):
        """Test that cannot approve application not pending approval."""
        gate = ApprovalGate()
        
        with pytest.raises(ValueError):
            gate.approve_application("app_001", approved_by="admin_456")
    
    def test_cannot_reject_non_pending_application(self):
        """Test that cannot reject application not pending approval."""
        gate = ApprovalGate()
        
        with pytest.raises(ValueError):
            gate.reject_application("app_001", rejected_by="admin_456")
    
    def test_cannot_request_approval_non_draft(self):
        """Test that cannot request approval for non-draft application."""
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test job understanding",
                proposed_approach="Test approach",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
            status=ApplicationStatus.APPROVED,
        )
        
        with pytest.raises(ValueError):
            gate.request_approval(package, requested_by="user_123")
