"""
Issue Intelligence

Tracking and analysis of errors, issues, and failures.
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.enigma_profile.contracts import (
    Issue,
    IssueSeverity,
    IssueType,
    IssueStatus,
)
from app.enigma_profile.repositories import IssueRepository
from app.marketplace.contracts import MarketplacePlatform


class IssueIntelligence:
    """
    Intelligence for error and issue tracking.
    
    Tracks system, marketplace, knowledge, execution, business, and client issues
    with severity classification and required actions.
    """
    
    def __init__(self, issue_repo: Optional[IssueRepository] = None):
        """Initialize issue intelligence.
        
        Args:
            issue_repo: Issue repository
        """
        self._issues: Dict[str, Issue] = {}
        self._issue_repo = issue_repo
    
    async def report_issue(
        self,
        source: str,
        type: IssueType,
        severity: IssueSeverity,
        detected_reason: str,
        impact: str = "",
        required_action: str = "",
        platform: Optional[MarketplacePlatform] = None,
        task: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Issue:
        """
        Report a new issue.
        
        Args:
            source: Source of the issue (system, platform, task)
            type: Type of issue
            severity: Severity level
            detected_reason: Reason for the issue
            impact: Impact description
            required_action: Required action to resolve
            platform: Platform (if applicable)
            task: Task (if applicable)
            metadata: Additional metadata
            
        Returns:
            Issue
        """
        issue_id = f"ISSUE-{uuid.uuid4().hex[:8].upper()}"
        
        issue = Issue(
            issue_id=issue_id,
            source=source,
            type=type,
            severity=severity,
            timestamp=datetime.utcnow().isoformat(),
            platform=platform,
            task=task,
            detected_reason=detected_reason,
            impact=impact,
            required_action=required_action,
            status=IssueStatus.OPEN,
            metadata=metadata or {},
        )
        
        self._issues[issue_id] = issue
        if self._issue_repo:
            await self._issue_repo.save_issue("enigma_profile", issue)
        return issue
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        Get an issue by ID.
        
        Args:
            issue_id: Issue ID
            
        Returns:
            Issue or None
        """
        return self._issues.get(issue_id)
    
    async def update_issue_status(self, issue_id: str, status: IssueStatus) -> None:
        """
        Update issue status.
        
        Args:
            issue_id: Issue ID
            status: New status
        """
        if issue_id in self._issues:
            self._issues[issue_id].status = status
            if status == IssueStatus.RESOLVED:
                self._issues[issue_id].resolved_at = datetime.utcnow().isoformat()
            if self._issue_repo:
                await self._issue_repo.save_issue("enigma_profile", self._issues[issue_id])
    
    async def resolve_issue(self, issue_id: str) -> None:
        """
        Mark an issue as resolved.
        
        Args:
            issue_id: Issue ID
        """
        await self.update_issue_status(issue_id, IssueStatus.RESOLVED)
    
    async def get_open_issues(self, severity: Optional[IssueSeverity] = None) -> List[Issue]:
        """
        Get open issues, optionally filtered by severity.
        
        Args:
            severity: Optional severity filter
            
        Returns:
            List of issues
        """
        if self._issue_repo:
            return await self._issue_repo.get_open_issues("enigma_profile", severity)
        
        issues = [i for i in self._issues.values() if i.status == IssueStatus.OPEN]
        
        if severity:
            issues = [i for i in issues if i.severity == severity]
        
        return issues
    
    def get_issues_by_type(self, type: IssueType) -> List[Issue]:
        """
        Get issues by type.
        
        Args:
            type: Issue type
            
        Returns:
            List of issues
        """
        return [i for i in self._issues.values() if i.type == type]
    
    def get_issues_by_platform(self, platform: MarketplacePlatform) -> List[Issue]:
        """
        Get issues by platform.
        
        Args:
            platform: Marketplace platform
            
        Returns:
            List of issues
        """
        return [i for i in self._issues.values() if i.platform == platform]
    
    def get_critical_issues(self) -> List[Issue]:
        """
        Get all critical issues.
        
        Returns:
            List of critical issues
        """
        return [i for i in self._issues.values() if i.severity == IssueSeverity.CRITICAL and i.status == IssueStatus.OPEN]
    
    def get_high_severity_issues(self) -> List[Issue]:
        """
        Get all high severity issues.
        
        Returns:
            List of high severity issues
        """
        return [i for i in self._issues.values() if i.severity == IssueSeverity.HIGH and i.status == IssueStatus.OPEN]
    
    def get_blocked_issues(self) -> List[Issue]:
        """
        Get all blocked issues.
        
        Returns:
            List of blocked issues
        """
        return [i for i in self._issues.values() if i.status == IssueStatus.BLOCKED]
    
    def generate_issue_summary(self) -> str:
        """
        Generate issue summary.
        
        Returns:
            Summary string
        """
        open_issues = self.get_open_issues()
        critical = self.get_critical_issues()
        high = self.get_high_severity_issues()
        blocked = self.get_blocked_issues()
        
        lines = [
            f"Total Open Issues: {len(open_issues)}",
            f"Critical: {len(critical)}",
            f"High: {len(high)}",
            f"Blocked: {len(blocked)}",
        ]
        
        if critical:
            lines.append("\nCritical Issues:")
            for issue in critical:
                lines.append(f"- {issue.issue_id}: {issue.detected_reason}")
        
        if high:
            lines.append("\nHigh Severity Issues:")
            for issue in high[:5]:  # Show top 5
                lines.append(f"- {issue.issue_id}: {issue.detected_reason}")
        
        return "\n".join(lines)
    
    async def auto_classify_system_error(
        self,
        error_message: str,
        platform: Optional[MarketplacePlatform] = None,
    ) -> Issue:
        """
        Auto-classify a system error and create an issue.
        
        Args:
            error_message: Error message
            platform: Platform (if applicable)
            
        Returns:
            Created issue
        """
        error_lower = error_message.lower()
        
        # Determine type and severity
        if "timeout" in error_lower:
            issue_type = IssueType.SYSTEM
            severity = IssueSeverity.MEDIUM
            reason = "Request timeout"
        elif "authentication" in error_lower or "unauthorized" in error_lower:
            issue_type = IssueType.API
            severity = IssueSeverity.HIGH
            reason = "Authentication failure"
        elif "api" in error_lower or "network" in error_lower:
            issue_type = IssueType.API
            severity = IssueSeverity.HIGH
            reason = "API unavailable or network error"
        elif "suspended" in error_lower:
            issue_type = IssueType.MARKETPLACE
            severity = IssueSeverity.CRITICAL
            reason = "Account suspended"
        else:
            issue_type = IssueType.SYSTEM
            severity = IssueSeverity.MEDIUM
            reason = error_message
        
        return await self.report_issue(
            source="system",
            type=issue_type,
            severity=severity,
            detected_reason=reason,
            impact="System operation affected",
            required_action="Investigate and resolve",
            platform=platform,
        )
    
    async def get_all_issues(self) -> List[Issue]:
        """Get all issues."""
        if self._issue_repo:
            return await self._issue_repo.get_all_issues("enigma_profile")
        return list(self._issues.values())
