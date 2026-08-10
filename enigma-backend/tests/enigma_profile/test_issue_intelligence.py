"""
Test Issue Intelligence

Tests for error and issue tracking.
"""

import pytest
from datetime import datetime

from app.enigma_profile.issue_intelligence import IssueIntelligence
from app.enigma_profile.contracts import (
    Issue,
    IssueSeverity,
    IssueType,
    IssueStatus,
)
from app.marketplace.contracts import MarketplacePlatform


class TestIssueIntelligence:
    """Test IssueIntelligence."""
    
    def test_initialization(self):
        """Test intelligence initialization."""
        intelligence = IssueIntelligence()
        assert intelligence is not None
        assert intelligence._issues == {}
    
    def test_report_issue(self):
        """Test reporting an issue."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
            impact="Cannot fetch account data",
            required_action="Retry or investigate",
        )
        
        assert issue.issue_id is not None
        assert issue.issue_id.startswith("ISSUE-")
        assert issue.status == IssueStatus.OPEN
        assert issue.type == IssueType.API
        assert issue.severity == IssueSeverity.HIGH
    
    def test_get_issue(self):
        """Test getting an issue by ID."""
        intelligence = IssueIntelligence()
        
        reported = intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        retrieved = intelligence.get_issue(reported.issue_id)
        
        assert retrieved is not None
        assert retrieved.issue_id == reported.issue_id
    
    def test_get_issue_not_found(self):
        """Test getting nonexistent issue."""
        intelligence = IssueIntelligence()
        
        retrieved = intelligence.get_issue("NONEXISTENT")
        assert retrieved is None
    
    def test_update_issue_status(self):
        """Test updating issue status."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.update_issue_status(issue.issue_id, IssueStatus.IN_PROGRESS)
        
        updated = intelligence.get_issue(issue.issue_id)
        assert updated.status == IssueStatus.IN_PROGRESS
    
    def test_resolve_issue(self):
        """Test resolving an issue."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.resolve_issue(issue.issue_id)
        
        resolved = intelligence.get_issue(issue.issue_id)
        assert resolved.status == IssueStatus.RESOLVED
        assert resolved.resolved_at is not None
    
    def test_get_open_issues(self):
        """Test getting open issues."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.MEDIUM,
            detected_reason="System error",
        )
        
        open_issues = intelligence.get_open_issues()
        
        assert len(open_issues) == 2
    
    def test_get_open_issues_filtered_by_severity(self):
        """Test getting open issues filtered by severity."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.MEDIUM,
            detected_reason="System error",
        )
        
        high_severity = intelligence.get_open_issues(severity=IssueSeverity.HIGH)
        
        assert len(high_severity) == 1
        assert high_severity[0].severity == IssueSeverity.HIGH
    
    def test_get_issues_by_type(self):
        """Test getting issues by type."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.MEDIUM,
            detected_reason="System error",
        )
        
        api_issues = intelligence.get_issues_by_type(IssueType.API)
        
        assert len(api_issues) == 1
        assert api_issues[0].type == IssueType.API
    
    def test_get_issues_by_platform(self):
        """Test getting issues by platform."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="platform",
            type=IssueType.MARKETPLACE,
            severity=IssueSeverity.HIGH,
            detected_reason="Account suspended",
            platform=MarketplacePlatform.UPWORK,
        )
        
        upwork_issues = intelligence.get_issues_by_platform(MarketplacePlatform.UPWORK)
        
        assert len(upwork_issues) == 1
        assert upwork_issues[0].platform == MarketplacePlatform.UPWORK
    
    def test_get_critical_issues(self):
        """Test getting critical issues."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.CRITICAL,
            detected_reason="System down",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.HIGH,
            detected_reason="System error",
        )
        
        critical = intelligence.get_critical_issues()
        
        assert len(critical) == 1
        assert critical[0].severity == IssueSeverity.CRITICAL
    
    def test_get_high_severity_issues(self):
        """Test getting high severity issues."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.MEDIUM,
            detected_reason="System error",
        )
        
        high = intelligence.get_high_severity_issues()
        
        assert len(high) == 1
        assert high[0].severity == IssueSeverity.HIGH
    
    def test_get_blocked_issues(self):
        """Test getting blocked issues."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.update_issue_status(issue.issue_id, IssueStatus.BLOCKED)
        
        blocked = intelligence.get_blocked_issues()
        
        assert len(blocked) == 1
        assert blocked[0].status == IssueStatus.BLOCKED
    
    def test_generate_issue_summary(self):
        """Test generating issue summary."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.CRITICAL,
            detected_reason="System down",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.HIGH,
            detected_reason="System error",
        )
        
        summary = intelligence.generate_issue_summary()
        
        assert "Total Open Issues: 2" in summary
        assert "Critical: 1" in summary
        assert "High: 1" in summary
    
    def test_auto_classify_system_error_timeout(self):
        """Test auto-classifying timeout error."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.auto_classify_system_error(
            error_message="Request timeout",
            platform=MarketplacePlatform.UPWORK,
        )
        
        assert issue.type == IssueType.SYSTEM
        assert issue.severity == IssueSeverity.MEDIUM
        assert "timeout" in issue.detected_reason.lower()
    
    def test_auto_classify_system_error_auth(self):
        """Test auto-classifying authentication error."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.auto_classify_system_error(
            error_message="Authentication failed",
            platform=MarketplacePlatform.UPWORK,
        )
        
        assert issue.type == IssueType.API
        assert issue.severity == IssueSeverity.HIGH
        assert "authentication" in issue.detected_reason.lower()
    
    def test_auto_classify_system_error_suspended(self):
        """Test auto-classifying suspended account error."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.auto_classify_system_error(
            error_message="Account suspended",
            platform=MarketplacePlatform.UPWORK,
        )
        
        assert issue.type == IssueType.MARKETPLACE
        assert issue.severity == IssueSeverity.CRITICAL
        assert "suspended" in issue.detected_reason.lower()
    
    def test_get_all_issues(self):
        """Test getting all issues."""
        intelligence = IssueIntelligence()
        
        intelligence.report_issue(
            source="system",
            type=IssueType.API,
            severity=IssueSeverity.HIGH,
            detected_reason="API timeout",
        )
        
        intelligence.report_issue(
            source="system",
            type=IssueType.SYSTEM,
            severity=IssueSeverity.MEDIUM,
            detected_reason="System error",
        )
        
        all_issues = intelligence.get_all_issues()
        
        assert len(all_issues) == 2
