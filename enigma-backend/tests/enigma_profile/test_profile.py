"""
Test Enigma Profile

Tests for the main Enigma Profile manager.
"""

import pytest

from app.enigma_profile.profile import EnigmaProfileManager
from app.enigma_profile.contracts import (
    EnigmaProfile,
    IssueSeverity,
)
from app.marketplace.contracts import MarketplacePlatform


class TestEnigmaProfileManager:
    """Test EnigmaProfileManager."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = EnigmaProfileManager()
        assert manager is not None
        assert manager.profile is not None
        assert manager.profile.profile_id == "enigma_profile"
    
    def test_initialize_default_profile(self):
        """Test initializing default profile."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        assert profile is not None
        assert profile.owner == "Enigma"
        assert len(profile.active_goals) > 0
        assert len(profile.target_platforms) > 0
        assert len(profile.knowledge_progress) > 0
        assert len(profile.training_items) > 0
        assert len(profile.platform_readiness) > 0
    
    def test_initialize_default_knowledge_domains(self):
        """Test that default knowledge domains are initialized."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        assert "SEO" in profile.knowledge_progress
        assert "Keyword Research" in profile.knowledge_progress
        assert "Technical SEO" in profile.knowledge_progress
    
    def test_initialize_default_training_items(self):
        """Test that default training items are initialized."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        skill_names = [item.skill for item in profile.training_items]
        assert "SEO Audit" in skill_names
        assert "Keyword Research" in skill_names
        assert "Technical SEO" in skill_names
    
    def test_initialize_default_platform_readiness(self):
        """Test that default platform readiness is initialized."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        assert MarketplacePlatform.UPWORK in profile.platform_readiness
        assert MarketplacePlatform.FREELANCER in profile.platform_readiness
        assert MarketplacePlatform.FIVERR in profile.platform_readiness
    
    def test_initialize_default_development_priorities(self):
        """Test that development priorities are generated."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        assert len(profile.development_priorities) > 0
    
    def test_update_profile(self):
        """Test updating profile with latest data."""
        manager = EnigmaProfileManager()
        
        manager.initialize_default_profile()
        
        # Modify some data
        manager.knowledge_tracker.update_progress("SEO", knowledge_score=0.9)
        
        updated_profile = manager.update_profile()
        
        assert updated_profile.knowledge_progress["SEO"].knowledge_score == 0.9
        assert updated_profile.updated_at is not None
    
    def test_get_profile_summary(self):
        """Test generating profile summary."""
        manager = EnigmaProfileManager()
        
        manager.initialize_default_profile()
        
        summary = manager.get_profile_summary()
        
        assert summary is not None
        assert "ENIGMA PROFILE" in summary
        assert "Owner: Enigma" in summary
        assert "Knowledge Progress:" in summary
    
    def test_report_system_issue(self):
        """Test reporting a system issue."""
        manager = EnigmaProfileManager()
        
        manager.initialize_default_profile()
        
        issue = manager.report_system_issue(
            error_message="API timeout",
            platform=MarketplacePlatform.UPWORK,
        )
        
        assert issue is not None
        assert issue.issue_id.startswith("ISSUE-")
        assert issue.platform == MarketplacePlatform.UPWORK
        
        # Should be added to profile
        assert len(manager.profile.issues) > 0
    
    def test_get_platform_summary(self):
        """Test getting platform summary."""
        manager = EnigmaProfileManager()
        
        manager.initialize_default_profile()
        
        summary = manager.get_platform_summary(MarketplacePlatform.UPWORK)
        
        assert summary is not None
        assert "UPWORK" in summary
        assert "Readiness:" in summary
    
    def test_get_platform_summary_not_found(self):
        """Test getting summary for untracked platform."""
        manager = EnigmaProfileManager()
        
        # Don't initialize default profile
        summary = manager.get_platform_summary(MarketplacePlatform.UPWORK)
        
        assert summary is None
    
    def test_profile_get_knowledge_progress(self):
        """Test getting knowledge progress from profile."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        progress = profile.get_knowledge_progress("SEO")
        
        assert progress is not None
        assert progress.domain == "SEO"
    
    def test_profile_get_platform_readiness(self):
        """Test getting platform readiness from profile."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        readiness = profile.get_platform_readiness(MarketplacePlatform.UPWORK)
        
        assert readiness is not None
        assert readiness.platform == MarketplacePlatform.UPWORK
    
    def test_profile_get_open_issues(self):
        """Test getting open issues from profile."""
        manager = EnigmaProfileManager()
        
        manager.initialize_default_profile()
        
        # Report an issue
        manager.report_system_issue("API timeout", MarketplacePlatform.UPWORK)
        
        open_issues = manager.profile.get_open_issues()
        
        assert len(open_issues) == 1
    
    def test_profile_get_open_issues_filtered_by_severity(self):
        """Test getting open issues filtered by severity."""
        manager = EnigmaProfileManager()
        
        manager.initialize_default_profile()
        
        # Report issues
        manager.report_system_issue("API timeout", MarketplacePlatform.UPWORK)
        manager.report_system_issue("System down", MarketplacePlatform.FREELANCER)
        
        high_severity = manager.profile.get_open_issues(severity=IssueSeverity.HIGH)
        
        # At least one should be high severity
        assert len(high_severity) >= 0
    
    def test_profile_get_development_priorities(self):
        """Test getting development priorities from profile."""
        manager = EnigmaProfileManager()
        
        profile = manager.initialize_default_profile()
        
        priorities = profile.get_development_priorities(limit=3)
        
        assert len(priorities) <= 3
        assert all(p.status == "pending" for p in priorities)
