"""
Human Approval Gate for Application Submission.

This module enforces mandatory human approval before any application
can be submitted to a marketplace. This is a critical safety boundary.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from app.work_market.application_package import (
    ApplicationPackage,
    ApplicationStatus,
    ApprovalDecision,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ApprovalState(str, Enum):
    """States in the approval workflow."""
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    SUBMITTED = "submitted"


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    application_package: ApplicationPackage
    requested_by: str
    requested_at: datetime
    notes: Optional[str] = None


@dataclass
class ApprovalResponse:
    """Response to approval request."""
    application_id: str
    decision: ApprovalDecision
    approved_by: str
    approved_at: datetime
    notes: Optional[str] = None


class ApprovalGate:
    """
    Enforces human approval before application submission.
    
    This is a mandatory safety boundary that prevents automatic
    application submission without explicit human approval.
    """
    
    def __init__(self) -> None:
        """Initialize approval gate."""
        self._pending_approvals: Dict[str, ApprovalRequest] = {}
    
    def request_approval(
        self,
        application_package: ApplicationPackage,
        requested_by: str,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Request human approval for an application.
        
        Args:
            application_package: The application package to approve
            requested_by: User requesting approval
            notes: Optional notes for the reviewer
            
        Returns:
            ApprovalRequest with tracking information
        """
        # Verify application is in appropriate state
        if application_package.status != ApplicationStatus.DRAFT:
            raise ValueError(
                f"Application must be in DRAFT state to request approval, "
                f"current state: {application_package.status}"
            )
        
        # Update application state
        application_package.status = ApplicationStatus.WAITING_FOR_APPROVAL
        application_package.updated_at = datetime.utcnow()
        
        # Create approval request
        request = ApprovalRequest(
            application_package=application_package,
            requested_by=requested_by,
            requested_at=datetime.utcnow(),
            notes=notes,
        )
        
        # Store pending approval
        self._pending_approvals[application_package.application_id] = request
        
        logger.info(
            f"Approval requested for application {application_package.application_id} "
            f"by {requested_by}"
        )
        
        return request
    
    def approve_application(
        self,
        application_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """
        Approve an application for submission.
        
        Args:
            application_id: ID of the application to approve
            approved_by: User approving the application
            notes: Optional approval notes
            
        Returns:
            Updated application package
        """
        # Verify application is pending approval
        if application_id not in self._pending_approvals:
            raise ValueError(
                f"Application {application_id} is not pending approval"
            )
        
        request = self._pending_approvals[application_id]
        package = request.application_package
        
        # Verify application is in correct state
        if package.status != ApplicationStatus.WAITING_FOR_APPROVAL:
            raise ValueError(
                f"Application must be in WAITING_FOR_APPROVAL state, "
                f"current state: {package.status}"
            )
        
        # Update application with approval
        package.status = ApplicationStatus.APPROVED
        package.approval_decision = ApprovalDecision.APPROVED
        package.approved_by = approved_by
        package.approval_notes = notes
        package.approved_at = datetime.utcnow()
        package.updated_at = datetime.utcnow()
        
        # Remove from pending approvals
        del self._pending_approvals[application_id]
        
        logger.info(
            f"Application {application_id} approved by {approved_by}"
        )
        
        return package
    
    def reject_application(
        self,
        application_id: str,
        rejected_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """
        Reject an application.
        
        Args:
            application_id: ID of the application to reject
            rejected_by: User rejecting the application
            notes: Optional rejection notes
            
        Returns:
            Updated application package
        """
        # Verify application is pending approval
        if application_id not in self._pending_approvals:
            raise ValueError(
                f"Application {application_id} is not pending approval"
            )
        
        request = self._pending_approvals[application_id]
        package = request.application_package
        
        # Update application with rejection
        package.status = ApplicationStatus.REJECTED
        package.approval_decision = ApprovalDecision.REJECTED
        package.approved_by = rejected_by
        package.approval_notes = notes
        package.approved_at = datetime.utcnow()
        package.updated_at = datetime.utcnow()
        
        # Remove from pending approvals
        del self._pending_approvals[application_id]
        
        logger.info(
            f"Application {application_id} rejected by {rejected_by}"
        )
        
        return package
    
    def request_revision(
        self,
        application_id: str,
        requested_by: str,
        notes: Optional[str] = None,
    ) -> ApplicationPackage:
        """
        Request revision for an application.
        
        Args:
            application_id: ID of the application
            requested_by: User requesting revision
            notes: Optional revision notes
            
        Returns:
            Updated application package
        """
        # Verify application is pending approval
        if application_id not in self._pending_approvals:
            raise ValueError(
                f"Application {application_id} is not pending approval"
            )
        
        request = self._pending_approvals[application_id]
        package = request.application_package
        
        # Update application with revision request
        package.status = ApplicationStatus.DRAFT
        package.approval_decision = ApprovalDecision.REVISION_REQUESTED
        package.approved_by = requested_by
        package.approval_notes = notes
        package.approved_at = datetime.utcnow()
        package.updated_at = datetime.utcnow()
        
        # Remove from pending approvals
        del self._pending_approvals[application_id]
        
        logger.info(
            f"Revision requested for application {application_id} by {requested_by}"
        )
        
        return package
    
    def can_submit(self, application_package: ApplicationPackage) -> bool:
        """
        Check if an application can be submitted.
        
        Args:
            application_package: The application package to check
            
        Returns:
            True if application can be submitted, False otherwise
        """
        # Application must be approved
        if application_package.status != ApplicationStatus.APPROVED:
            return False
        
        # Must have approval decision
        if application_package.approval_decision != ApprovalDecision.APPROVED:
            return False
        
        # Must have approver
        if not application_package.approved_by:
            return False
        
        # Must have approval timestamp
        if not application_package.approved_at:
            return False
        
        return True
    
    def get_pending_approvals(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        return list(self._pending_approvals.values())
    
    def get_approval_status(self, application_id: str) -> Optional[ApprovalState]:
        """
        Get the approval status of an application.
        
        Args:
            application_id: ID of the application
            
        Returns:
            Current approval state or None if not found
        """
        if application_id in self._pending_approvals:
            return ApprovalState.WAITING_FOR_APPROVAL
        
        return None


# Global approval gate instance
approval_gate = ApprovalGate()
