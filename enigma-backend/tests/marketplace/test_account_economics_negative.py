"""
Test Account Economics - Negative Cases

Tests for ensuring no automatic apply, no fake data, no unknown=free assumptions.
"""

import pytest

from app.marketplace.account_economics import (
    AccountEconomicsEngine,
    EconomicSafetyStatus,
)
from app.marketplace.account_state import (
    MarketplaceAccountState,
    AccountStatus,
    FreshnessStatus,
    CreditBalance,
    WalletBalance,
)
from app.marketplace.contracts import MarketplacePlatform


class TestNoAutomaticApply:
    """Test that account economics never enables automatic apply."""
    
    def test_engine_never_auto_applies(self):
        """Test that engine never performs automatic apply."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Connects"),
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        # Result should never indicate automatic apply
        assert result.status in [
            EconomicSafetyStatus.SAFE,
            EconomicSafetyStatus.BLOCK,
            EconomicSafetyStatus.NEED_RESEARCH,
        ]
        # No apply action in result
        assert not hasattr(result, "auto_apply")
        assert not hasattr(result, "should_apply")


class TestNoFakeData:
    """Test that no fake data is generated."""
    
    def test_unknown_cost_not_treated_as_zero(self):
        """Test that unknown cost is not treated as zero."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=None),  # Unknown
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        # Should not treat unknown as sufficient
        assert result.status != EconomicSafetyStatus.SAFE
        assert result.blocking_reason is not None
    
    def test_unknown_balance_not_treated_as_sufficient(self):
        """Test that unknown balance is not treated as sufficient."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.FREELANCER,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            wallet=WalletBalance(available=None),  # Unknown
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.FREELANCER,
            job_data,
        )
        
        # Should not treat unknown as sufficient
        assert result.status != EconomicSafetyStatus.SAFE
        assert result.blocking_reason is not None
    
    def test_no_hardcoded_balance(self):
        """Test that no hardcoded balance is used."""
        from datetime import datetime
        
        engine = AccountEconomicsEngine()
        
        # Register state with zero balance
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=0, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        # Should block on insufficient balance
        assert result.status == EconomicSafetyStatus.BLOCK
        assert "insufficient" in result.blocking_reason.lower()


class TestUnknownNotFree:
    """Test that unknown cost is not treated as free."""
    
    def test_unknown_cost_not_free(self):
        """Test that unknown cost is not treated as free."""
        from app.marketplace.account_economics import ApplicationCost, ApplicationCostType
        
        cost_unknown = ApplicationCost(
            cost_type=ApplicationCostType.UNKNOWN,
            is_known=False,
        )
        
        assert cost_unknown.is_free() is False
        assert cost_unknown.is_unknown() is True
    
    def test_platform_with_unknown_cost_blocks(self):
        """Test that platform with unknown cost blocks."""
        from app.marketplace.platform_rules import PlatformRules, PlatformApplicationCost, ApplicationCostType
        
        rules = PlatformRules(
            platform=MarketplacePlatform.UPWORK,
            application_cost=PlatformApplicationCost(
                cost_type=ApplicationCostType.UNKNOWN,
            ),
        )
        
        assert rules.application_cost.is_cost_known() is False
        assert rules.application_cost.is_free() is False


class TestStaleDataBlocks:
    """Test that stale data blocks execution."""
    
    def test_expired_status_blocks(self):
        """Test that EXPIRED status blocks."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Connects"),
            freshness=FreshnessStatus.EXPIRED,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH
        assert "stale" in result.blocking_reason.lower() or "expired" in result.blocking_reason.lower()
    
    def test_stale_status_blocks(self):
        """Test that STALE status blocks."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Connects"),
            freshness=FreshnessStatus.STALE,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH


class TestAccountPlatformMismatch:
    """Test account platform mismatch handling."""
    
    def test_wrong_platform_account_state(self):
        """Test using wrong platform account state."""
        engine = AccountEconomicsEngine()
        
        # Register Upwork account state
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
        )
        
        engine.register_account_state(state)
        
        # Try to evaluate for Freelancer
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.FREELANCER,
            job_data,
        )
        
        # Should not have account state for Freelancer
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH
        assert result.blocking_reason == "Account state unknown"


class TestNoLiveApiCalls:
    """Test that no live API calls are made."""
    
    def test_engine_uses_registered_state_only(self):
        """Test that engine only uses registered state, no API calls."""
        engine = AccountEconomicsEngine()
        
        # No account state registered
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        # Should not attempt to fetch data via API
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH
        assert result.blocking_reason == "Account state unknown"
        
        # No network activity should occur
        # (This is a design test - the engine should not make network calls)


class TestNegativeExpectedValue:
    """Test negative expected value handling."""
    
    def test_negative_expected_value_blocks(self):
        """Test that negative expected value blocks."""
        from datetime import datetime
        
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job", "expected_value": -100.0}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.BLOCK
        assert result.blocking_reason == "Negative expected value"
    
    def test_zero_expected_value_allowed(self):
        """Test that zero expected value is allowed."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=100, currency="Connects"),
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job", "expected_value": 0.0}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        # Zero is not negative, should not block on expected value
        assert result.status != EconomicSafetyStatus.BLOCK or result.blocking_reason != "Negative expected value"


class TestInsufficientResources:
    """Test insufficient resource handling."""
    
    def test_insufficient_credits_blocks(self):
        """Test that insufficient credits block."""
        from datetime import datetime
        
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=1, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.BLOCK
        assert "insufficient" in result.blocking_reason.lower()
    
    def test_insufficient_wallet_blocks(self):
        """Test that insufficient wallet blocks."""
        from datetime import datetime
        
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.FREELANCER,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            wallet=WalletBalance(available=0.10, currency="USD"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.FREELANCER,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.BLOCK
        assert "insufficient" in result.blocking_reason.lower()


class TestManualAccountInput:
    """Test manual account input support."""
    
    def test_manual_input_source_accepted(self):
        """Test that manual input source is accepted."""
        from app.marketplace.account_state import DataSource
        from datetime import datetime
        
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
            source=DataSource.MANUAL_INPUT,
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        # Manual input should be accepted if fresh
        assert result.status == EconomicSafetyStatus.SAFE
