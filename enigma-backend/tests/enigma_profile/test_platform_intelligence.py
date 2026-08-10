"""
Test Platform Intelligence

Tests for platform readiness and intelligence.
"""

import pytest
from datetime import datetime, timedelta

from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.contracts import PlatformReadiness
from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.account_state import (
    MarketplaceAccountState,
    AccountStatus,
    CreditBalance,
    WalletBalance,
    FreshnessStatus,
)


class TestPlatformIntelligence:
    """Test PlatformIntelligence."""
    
    def test_initialization(self):
        """Test intelligence initialization."""
        intelligence = PlatformIntelligence()
        assert intelligence is not None
        assert intelligence._platform_readiness == {}
    
    def test_register_platform_readiness(self):
        """Test registering platform readiness."""
        intelligence = PlatformIntelligence()
        
        readiness = PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.43,
            knowledge_score=0.80,
            evidence_score=0.30,
            portfolio_score=0.10,
            execution_score=0.50,
            win_probability=0.40,
            economics_score=0.50,
            blockers=["No reviews", "Weak portfolio"],
            recommendations=["Build 3 proof-of-work assets"],
            last_updated=datetime.utcnow().isoformat(),
        )
        
        intelligence.register_platform_readiness(readiness)
        
        retrieved = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        assert retrieved is not None
        assert retrieved.overall_readiness == 0.43
    
    def test_get_platform_readiness_not_found(self):
        """Test getting readiness for unregistered platform."""
        intelligence = PlatformIntelligence()
        
        retrieved = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        assert retrieved is None
    
    def test_update_readiness(self):
        """Test updating platform readiness."""
        intelligence = PlatformIntelligence()
        
        readiness = PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.3,
            knowledge_score=0.5,
            evidence_score=0.2,
            portfolio_score=0.1,
            execution_score=0.3,
            win_probability=0.4,
            economics_score=0.5,
        )
        
        intelligence.register_platform_readiness(readiness)
        
        intelligence.update_readiness(
            MarketplacePlatform.UPWORK,
            knowledge_score=0.8,
        )
        
        updated = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        assert updated.knowledge_score == 0.8
        assert updated.last_updated is not None
    
    def test_add_blocker(self):
        """Test adding a blocker."""
        intelligence = PlatformIntelligence()
        
        readiness = PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.5,
            knowledge_score=0.5,
            evidence_score=0.5,
            portfolio_score=0.5,
            execution_score=0.5,
            win_probability=0.5,
            economics_score=0.5,
        )
        
        intelligence.register_platform_readiness(readiness)
        
        intelligence.add_blocker(MarketplacePlatform.UPWORK, "Low credits")
        
        updated = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        assert "Low credits" in updated.blockers
    
    def test_remove_blocker(self):
        """Test removing a blocker."""
        intelligence = PlatformIntelligence()
        
        readiness = PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.5,
            knowledge_score=0.5,
            evidence_score=0.5,
            portfolio_score=0.5,
            execution_score=0.5,
            win_probability=0.5,
            economics_score=0.5,
            blockers=["Low credits"],
        )
        
        intelligence.register_platform_readiness(readiness)
        
        intelligence.remove_blocker(MarketplacePlatform.UPWORK, "Low credits")
        
        updated = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        assert "Low credits" not in updated.blockers
    
    def test_add_recommendation(self):
        """Test adding a recommendation."""
        intelligence = PlatformIntelligence()
        
        readiness = PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.5,
            knowledge_score=0.5,
            evidence_score=0.5,
            portfolio_score=0.5,
            execution_score=0.5,
            win_probability=0.5,
            economics_score=0.5,
        )
        
        intelligence.register_platform_readiness(readiness)
        
        intelligence.add_recommendation(MarketplacePlatform.UPWORK, "Build portfolio")
        
        updated = intelligence.get_platform_readiness(MarketplacePlatform.UPWORK)
        assert "Build portfolio" in updated.recommendations
    
    def test_analyze_from_account_state_suspended(self):
        """Test analyzing from suspended account state."""
        intelligence = PlatformIntelligence()
        
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
        
        assert "suspended" in " ".join(readiness.blockers).lower()
        assert readiness.economics_score == 0.0
    
    def test_analyze_from_account_state_low_credits(self):
        """Test analyzing from account state with low credits."""
        intelligence = PlatformIntelligence()
        
        account_state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=1, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        readiness = intelligence.analyze_from_account_state(
            MarketplacePlatform.UPWORK,
            account_state,
        )
        
        assert any("credits" in blocker.lower() for blocker in readiness.blockers)
    
    def test_analyze_from_account_state_stale(self):
        """Test analyzing from stale account state."""
        intelligence = PlatformIntelligence()
        
        account_state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Connects"),
            last_verified_at=(datetime.utcnow() - timedelta(hours=48)).isoformat(),
            freshness=FreshnessStatus.STALE,
        )
        
        readiness = intelligence.analyze_from_account_state(
            MarketplacePlatform.UPWORK,
            account_state,
        )
        
        assert any("stale" in blocker.lower() for blocker in readiness.blockers)
    
    def test_get_all_platforms(self):
        """Test getting all tracked platforms."""
        intelligence = PlatformIntelligence()
        
        intelligence.register_platform_readiness(PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.5,
            knowledge_score=0.5,
            evidence_score=0.5,
            portfolio_score=0.5,
            execution_score=0.5,
            win_probability=0.5,
            economics_score=0.5,
        ))
        
        platforms = intelligence.get_all_platforms()
        
        assert len(platforms) == 1
        assert MarketplacePlatform.UPWORK in platforms
    
    def test_get_platforms_by_readiness(self):
        """Test getting platforms by readiness threshold."""
        intelligence = PlatformIntelligence()
        
        intelligence.register_platform_readiness(PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.7,
            knowledge_score=0.8,
            evidence_score=0.7,
            portfolio_score=0.6,
            execution_score=0.7,
            win_probability=0.7,
            economics_score=0.7,
        ))
        
        intelligence.register_platform_readiness(PlatformReadiness(
            platform=MarketplacePlatform.FREELANCER,
            overall_readiness=0.3,
            knowledge_score=0.4,
            evidence_score=0.2,
            portfolio_score=0.1,
            execution_score=0.3,
            win_probability=0.3,
            economics_score=0.4,
        ))
        
        high_readiness = intelligence.get_platforms_by_readiness(min_readiness=0.5)
        
        assert MarketplacePlatform.UPWORK in high_readiness
        assert MarketplacePlatform.FREELANCER not in high_readiness
    
    def test_generate_platform_summary(self):
        """Test generating platform summary."""
        intelligence = PlatformIntelligence()
        
        readiness = PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.43,
            knowledge_score=0.80,
            evidence_score=0.30,
            portfolio_score=0.10,
            execution_score=0.50,
            win_probability=0.40,
            economics_score=0.50,
            blockers=["No reviews", "Weak portfolio"],
            recommendations=["Build 3 proof-of-work assets"],
        )
        
        intelligence.register_platform_readiness(readiness)
        
        summary = intelligence.generate_platform_summary(MarketplacePlatform.UPWORK)
        
        assert summary is not None
        assert "UPWORK" in summary
        assert "43%" in summary
        assert "No reviews" in summary
