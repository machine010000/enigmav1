"""
Test Enigma Profile - Negative Cases

Tests for ensuring no fake knowledge, no fake evidence, no silent failures, and proper error handling.
"""

import pytest

from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.issue_intelligence import IssueIntelligence
from app.enigma_profile.contracts import (
    KnowledgeProgress,
    TrainingItem,
    SkillLevel,
    IssueSeverity,
    IssueType,
    IssueStatus,
)
from app.marketplace.contracts import MarketplacePlatform


class TestNoFakeKnowledge:
    """Test that missing knowledge is not treated as expert."""
    
    def test_missing_knowledge_not_expert(self):
        """Test that missing knowledge domain is not expert."""
        tracker = KnowledgeProgressTracker()
        
        # Unregistered domain
        level = tracker.get_skill_level("Nonexistent Domain")
        
        assert level == SkillLevel.UNKNOWN
        assert level != SkillLevel.EXPERT
        assert level != SkillLevel.OPERATIONAL
    
    def test_low_readiness_not_expert(self):
        """Test that low readiness is not expert."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.1,
            execution_score=0.1,
            evidence_score=0.1,
            confidence=0.1,
            readiness=0.1,
        )
        
        tracker.register_domain(progress)
        
        level = tracker.get_skill_level("SEO")
        
        assert level == SkillLevel.UNKNOWN
        assert level != SkillLevel.EXPERT


class TestNoFakeEvidence:
    """Test that missing evidence is not treated as portfolio."""
    
    def test_low_evidence_not_portfolio(self):
        """Test that low evidence score is not treated as portfolio."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.8,
            execution_score=0.8,
            evidence_score=0.1,  # Very low evidence
            confidence=0.8,
            readiness=0.65,
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        # Should identify evidence as a gap
        assert any("evidence" in gap.lower() for gap in gaps)
    
    def test_no_evidence_not_portfolio(self):
        """Test that zero evidence is not treated as portfolio."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.9,
            execution_score=0.9,
            evidence_score=0.0,  # No evidence
            confidence=0.9,
            readiness=0.72,
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        # Should identify evidence as a gap
        assert any("evidence" in gap.lower() for gap in gaps)


class TestNoSilentFailures:
    """Test that errors are not silent."""
    
    def test_update_progress_unregistered_domain(self):
        """Test that updating unregistered domain does not crash."""
        tracker = KnowledgeProgressTracker()
        
        # Should not crash, just do nothing
        tracker.update_progress("Nonexistent", knowledge_score=0.8)
        
        # Domain should still not exist
        assert tracker.get_progress("Nonexistent") is None
    
    def test_complete_training_unregistered_skill(self):
        """Test that completing unregistered training does not crash."""
        tracker = TrainingTracker()
        
        # Should not crash, just do nothing
        tracker.complete_training("Nonexistent")
        
        # Skill should still not exist
        assert tracker.get_training("Nonexistent") is None
    
    def test_get_platform_readiness_not_registered(self):
        """Test that getting unregistered platform readiness returns None."""
        intelligence = PlatformIntelligence()
        
        readiness = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        
        assert readiness is None
        # Should not crash or return fake data
    
    def test_resolve_nonexistent_issue(self):
        """Test that resolving nonexistent issue does not crash."""
        intelligence = IssueIntelligence()
        
        # Should not crash
        intelligence.resolve_issue("NONEXISTENT")
        
        # Should not create fake issue
        assert intelligence.get_issue("NONEXISTENT") is None


class TestFailedTaskNotSuccess:
    """Test that failed task is not treated as success."""
    
    def test_api_failure_not_healthy(self):
        """Test that API failure is not treated as healthy account."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.auto_classify_system_error(
            error_message="API timeout",
            platform=MarketplacePlatform.UPWORK,
        )
        
        # Should create an issue
        assert issue is not None
        assert issue.severity != IssueSeverity.LOW  # Should not be low severity
        assert issue.status == IssueStatus.OPEN  # Should be open, not resolved
    
    def test_suspended_account_not_healthy(self):
        """Test that suspended account is not treated as healthy."""
        intelligence = IssueIntelligence()
        
        issue = intelligence.auto_classify_system_error(
            error_message="Account suspended",
            platform=MarketplacePlatform.UPWORK,
        )
        
        # Should create critical issue
        assert issue.severity == IssueSeverity.CRITICAL
        assert issue.type == IssueType.MARKETPLACE


class TestUnknownPlatformEconomicsNotFree:
    """Test that unknown platform economics is not treated as free."""
    
    def test_unknown_economics_not_free(self):
        """Test that unknown economics is not treated as free."""
        intelligence = PlatformIntelligence()
        
        # No account state registered
        readiness = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        
        # Should return None, not fake readiness with free economics
        assert readiness is None
    
    def test_suspended_account_economics_not_free(self):
        """Test that suspended account economics is not free."""
        intelligence = PlatformIntelligence()
        
        from datetime import datetime
        from app.marketplace.account_state import (
            MarketplaceAccountState,
            AccountStatus,
            CreditBalance,
            FreshnessStatus,
        )
        
        account_state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.SUSPENDED,
            credits=CreditBalance(available=100, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        readiness = intelligence.analyze_from_account_state(
            MarketplacePlatform.UPWORK,
            account_state,
        )
        
        # Should have low economics score
        assert readiness.economics_score == 0.0
        # Should have blockers
        assert len(readiness.blockers) > 0


class TestStaleKnowledgeDetection:
    """Test that stale knowledge is detected."""
    
    def test_stale_knowledge_identified(self):
        """Test that stale knowledge is identified as a gap."""
        tracker = KnowledgeProgressTracker()
        
        from datetime import datetime, timedelta
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.8,
            execution_score=0.8,
            evidence_score=0.8,
            confidence=0.8,
            readiness=0.8,
            last_verified=(datetime.utcnow() - timedelta(hours=48)).isoformat(),
            freshness="stale",
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        # Should identify stale knowledge
        assert any("stale" in gap.lower() for gap in gaps)
    
    def test_expired_knowledge_identified(self):
        """Test that expired knowledge is identified as a gap."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.8,
            execution_score=0.8,
            evidence_score=0.8,
            confidence=0.8,
            readiness=0.8,
            freshness="expired",
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        # Should identify expired knowledge
        assert any("expired" in gap.lower() for gap in gaps)


class TestPlatformSpecificBlockers:
    """Test that platform-specific blockers are detected."""
    
    def test_platform_blockers_recorded(self):
        """Test that platform blockers are properly recorded."""
        intelligence = PlatformIntelligence()
        
        from datetime import datetime
        from app.marketplace.account_state import (
            MarketplaceAccountState,
            AccountStatus,
            CreditBalance,
            FreshnessStatus,
        )
        
        account_state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=1, currency="Connects"),  # Very low
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        readiness = intelligence.analyze_from_account_state(
            MarketplacePlatform.UPWORK,
            account_state,
        )
        
        # Should have blocker for low credits
        assert any("credits" in blocker.lower() for blocker in readiness.blockers)
    
    def test_different_platforms_separate_blockers(self):
        """Test that different platforms have separate blockers."""
        intelligence = PlatformIntelligence()
        
        from datetime import datetime
        from app.marketplace.account_state import (
            MarketplaceAccountState,
            AccountStatus,
            CreditBalance,
            FreshnessStatus,
        )
        
        # Upwork with low credits
        upwork_state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="upwork_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=1, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        # Freelancer with good credits
        freelancer_state = MarketplaceAccountState(
            platform=MarketplacePlatform.FREELANCER,
            account_id="freelancer_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Credits"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        intelligence.analyze_from_account_state(MarketplacePlatform.UPWORK, upwork_state)
        intelligence.analyze_from_account_state(MarketplacePlatform.FREELANCER, freelancer_state)
        
        upwork_readiness = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        freelancer_readiness = intelligence.get_platform_readiness(MarketplacePlatform.FREELANCER)
        
        # Upwork should have blockers
        assert len(upwork_readiness.blockers) > 0
        
        # Freelancer should have fewer or no blockers
        assert len(freelancer_readiness.blockers) <= len(upwork_readiness.blockers)


class TestTrainingProgressAccuracy:
    """Test that training progress is accurately tracked."""
    
    def test_low_progress_not_complete(self):
        """Test that low progress is not treated as complete."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            progress=0.1,
        )
        
        tracker.register_training(item)
        
        retrieved = tracker.get_training("Technical SEO")
        
        assert retrieved.progress == 0.1
        assert retrieved.level == SkillLevel.LEARNING
        assert retrieved.completed_at is None
    
    def test_progress_cap_at_1(self):
        """Test that progress is capped at 1.0."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            progress=0.5,
        )
        
        tracker.register_training(item)
        
        # Try to set progress above 1.0
        tracker.update_progress("Technical SEO", 1.5)
        
        retrieved = tracker.get_training("Technical SEO")
        
        # Should be capped at 1.0
        assert retrieved.progress == 1.0
