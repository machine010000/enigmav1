"""
Test Account Economics
"""

import pytest
from datetime import datetime, timedelta

from app.marketplace.account_economics import (
    AccountEconomicsEngine,
    EconomicSafetyStatus,
    EconomicSafetyResult,
    EconomicMetrics,
    ApplicationCost,
)
from app.marketplace.account_state import (
    MarketplaceAccountState,
    AccountStatus,
    DataSource,
    FreshnessStatus,
    CreditBalance,
    WalletBalance,
)
from app.marketplace.platform_rules import (
    get_platform_rules,
    ApplicationCostType,
)
from app.marketplace.contracts import MarketplacePlatform


class TestApplicationCost:
    """Test application cost."""
    
    def test_application_cost_creation(self):
        """Test application cost creation."""
        cost = ApplicationCost(
            cost_type=ApplicationCostType.CREDITS,
            amount=2,
            currency="Connects",
            is_known=True,
        )
        
        assert cost.cost_type == ApplicationCostType.CREDITS
        assert cost.amount == 2
        assert cost.currency == "Connects"
        assert cost.is_known is True
    
    def test_is_free(self):
        """Test is_free."""
        cost_free = ApplicationCost(cost_type=ApplicationCostType.FREE, is_known=True)
        cost_paid = ApplicationCost(
            cost_type=ApplicationCostType.CREDITS,
            amount=2,
            is_known=True,
        )
        
        assert cost_free.is_free() is True
        assert cost_paid.is_free() is False
    
    def test_is_unknown(self):
        """Test is_unknown."""
        cost_unknown = ApplicationCost(
            cost_type=ApplicationCostType.UNKNOWN,
            is_known=False,
        )
        cost_known = ApplicationCost(
            cost_type=ApplicationCostType.CREDITS,
            amount=2,
            is_known=True,
        )
        
        assert cost_unknown.is_unknown() is True
        assert cost_known.is_unknown() is False


class TestEconomicMetrics:
    """Test economic metrics."""
    
    def test_economic_metrics_creation(self):
        """Test economic metrics creation."""
        metrics = EconomicMetrics(
            application_cost=ApplicationCost(
                cost_type=ApplicationCostType.CREDITS,
                amount=2,
                is_known=True,
            ),
            available_credits=10,
            expected_value=100.0,
            win_probability=0.5,
        )
        
        assert metrics.application_cost.amount == 2
        assert metrics.available_credits == 10
        assert metrics.expected_value == 100.0
        assert metrics.win_probability == 0.5
    
    def test_is_balance_sufficient_credits(self):
        """Test is_balance_sufficient with credits."""
        metrics = EconomicMetrics(
            application_cost=ApplicationCost(
                cost_type=ApplicationCostType.CREDITS,
                amount=2,
                is_known=True,
            ),
            available_credits=10,
        )
        
        assert metrics.is_balance_sufficient() is True
    
    def test_is_balance_sufficient_insufficient_credits(self):
        """Test is_balance_sufficient with insufficient credits."""
        metrics = EconomicMetrics(
            application_cost=ApplicationCost(
                cost_type=ApplicationCostType.CREDITS,
                amount=10,
                is_known=True,
            ),
            available_credits=5,
        )
        
        assert metrics.is_balance_sufficient() is False
    
    def test_is_balance_sufficient_unknown_credits(self):
        """Test is_balance_sufficient with unknown credits."""
        metrics = EconomicMetrics(
            application_cost=ApplicationCost(
                cost_type=ApplicationCostType.CREDITS,
                amount=2,
                is_known=True,
            ),
            available_credits=None,
        )
        
        assert metrics.is_balance_sufficient() is None
    
    def test_is_balance_sufficient_wallet(self):
        """Test is_balance_sufficient with wallet."""
        metrics = EconomicMetrics(
            application_cost=ApplicationCost(
                cost_type=ApplicationCostType.MONETARY,
                amount=5.0,
                is_known=True,
            ),
            available_balance=100.0,
        )
        
        assert metrics.is_balance_sufficient() is True
    
    def test_has_positive_expected_value(self):
        """Test has_positive_expected_value."""
        metrics_positive = EconomicMetrics(
            application_cost=ApplicationCost(cost_type=ApplicationCostType.FREE, is_known=True),
            expected_value=100.0,
        )
        metrics_negative = EconomicMetrics(
            application_cost=ApplicationCost(cost_type=ApplicationCostType.FREE, is_known=True),
            expected_value=-50.0,
        )
        metrics_unknown = EconomicMetrics(
            application_cost=ApplicationCost(cost_type=ApplicationCostType.FREE, is_known=True),
            expected_value=None,
        )
        
        assert metrics_positive.has_positive_expected_value() is True
        assert metrics_negative.has_positive_expected_value() is False
        assert metrics_unknown.has_positive_expected_value() is None


class TestAccountEconomicsEngine:
    """Test account economics engine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = AccountEconomicsEngine()
        
        assert engine is not None
        assert engine._account_states == {}
    
    def test_register_account_state(self):
        """Test register account state."""
        engine = AccountEconomicsEngine()
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
        )
        
        engine.register_account_state(state)
        
        assert engine.get_account_state(MarketplacePlatform.UPWORK) == state
    
    def test_get_account_state(self):
        """Test get account state."""
        engine = AccountEconomicsEngine()
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
        )
        
        engine.register_account_state(state)
        
        retrieved = engine.get_account_state(MarketplacePlatform.UPWORK)
        
        assert retrieved == state
    
    def test_get_account_state_not_registered(self):
        """Test get account state when not registered."""
        engine = AccountEconomicsEngine()
        
        retrieved = engine.get_account_state(MarketplacePlatform.UPWORK)
        
        assert retrieved is None
    
    def test_evaluate_application_economics_safe(self):
        """Test evaluate application economics with safe result."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.SAFE
        assert result.metrics is not None
        assert result.blocking_reason is None
    
    def test_evaluate_application_economics_insufficient_credits(self):
        """Test evaluate with insufficient credits."""
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
        assert result.blocking_reason == "Insufficient balance/credits for application"
    
    def test_evaluate_application_economics_stale_data(self):
        """Test evaluate with stale data."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
            last_verified_at=(datetime.utcnow() - timedelta(hours=48)).isoformat(),
            freshness=FreshnessStatus.STALE,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH
        assert result.blocking_reason == "Account data is stale"
    
    def test_evaluate_application_economics_no_account_state(self):
        """Test evaluate with no account state."""
        engine = AccountEconomicsEngine()
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH
        assert result.blocking_reason == "Account state unknown"
    
    def test_evaluate_application_economics_suspended_account(self):
        """Test evaluate with suspended account."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.SUSPENDED,
            credits=CreditBalance(available=10, currency="Connects"),
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
        assert "suspended" in result.blocking_reason.lower()
    
    def test_evaluate_application_economics_negative_expected_value(self):
        """Test evaluate with negative expected value."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
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
    
    def test_evaluate_application_economics_unknown_credits(self):
        """Test evaluate with unknown credits."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=None, currency="Connects"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
        )
        
        engine.register_account_state(state)
        
        job_data = {"title": "Test Job"}
        result = engine.evaluate_application_economics(
            MarketplacePlatform.UPWORK,
            job_data,
        )
        
        assert result.status == EconomicSafetyStatus.NEED_RESEARCH
        assert result.blocking_reason == "Balance/credits unknown"
    
    def test_get_account_summary(self):
        """Test get account summary."""
        engine = AccountEconomicsEngine()
        
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
            wallet=WalletBalance(available=100.0, currency="USD"),
            last_verified_at=datetime.utcnow().isoformat(),
            freshness=FreshnessStatus.FRESH,
            confidence=0.9,
            source=DataSource.MANUAL_INPUT,
        )
        
        engine.register_account_state(state)
        
        summary = engine.get_account_summary(MarketplacePlatform.UPWORK)
        
        assert summary is not None
        assert summary["platform"] == "upwork"
        assert summary["account_status"] == "active"
        assert summary["credits_available"] == 10
        assert summary["wallet_available"] == 100.0
        assert summary["confidence"] == 0.9
        assert summary["source"] == "manual_input"
        assert summary["is_fresh"] is True
    
    def test_get_account_summary_not_registered(self):
        """Test get account summary when not registered."""
        engine = AccountEconomicsEngine()
        
        summary = engine.get_account_summary(MarketplacePlatform.UPWORK)
        
        assert summary is None


class TestEconomicSafetyResult:
    """Test economic safety result."""
    
    def test_safety_result_creation(self):
        """Test safety result creation."""
        result = EconomicSafetyResult(
            status=EconomicSafetyStatus.SAFE,
            metrics=EconomicMetrics(
                application_cost=ApplicationCost(
                    cost_type=ApplicationCostType.FREE,
                    is_known=True,
                ),
            ),
        )
        
        assert result.status == EconomicSafetyStatus.SAFE
        assert result.metrics is not None
        assert result.blocking_reason is None
    
    def test_safety_result_with_blocking_reason(self):
        """Test safety result with blocking reason."""
        result = EconomicSafetyResult(
            status=EconomicSafetyStatus.BLOCK,
            blocking_reason="Insufficient credits",
            recommendations=["Add more credits"],
        )
        
        assert result.status == EconomicSafetyStatus.BLOCK
        assert result.blocking_reason == "Insufficient credits"
        assert "Add more credits" in result.recommendations
