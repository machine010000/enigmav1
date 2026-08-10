"""
Test Marketplace Account State
"""

import pytest
from datetime import datetime, timedelta

from app.marketplace.account_state import (
    MarketplaceAccountState,
    AccountStatus,
    DataSource,
    FreshnessStatus,
    CreditBalance,
    WalletBalance,
    SubscriptionPlan,
)
from app.marketplace.contracts import MarketplacePlatform


class TestCreditBalance:
    """Test credit balance."""
    
    def test_credit_balance_creation(self):
        """Test credit balance creation."""
        balance = CreditBalance(
            available=10,
            pending=2,
            used=5,
            limit=20,
            currency="Connects",
        )
        
        assert balance.available == 10
        assert balance.pending == 2
        assert balance.used == 5
        assert balance.limit == 20
        assert balance.currency == "Connects"
    
    def test_is_available_known(self):
        """Test is_available_known."""
        balance_known = CreditBalance(available=10)
        balance_unknown = CreditBalance(available=None)
        
        assert balance_known.is_available_known() is True
        assert balance_unknown.is_available_known() is False
    
    def test_is_sufficient(self):
        """Test is_sufficient."""
        balance = CreditBalance(available=10)
        
        assert balance.is_sufficient(5) is True
        assert balance.is_sufficient(10) is True
        assert balance.is_sufficient(15) is False
    
    def test_is_sufficient_unknown(self):
        """Test is_sufficient when available is unknown."""
        balance = CreditBalance(available=None)
        
        assert balance.is_sufficient(5) is None


class TestWalletBalance:
    """Test wallet balance."""
    
    def test_wallet_balance_creation(self):
        """Test wallet balance creation."""
        wallet = WalletBalance(
            available=100.50,
            currency="USD",
        )
        
        assert wallet.available == 100.50
        assert wallet.currency == "USD"
    
    def test_is_available_known(self):
        """Test is_available_known."""
        wallet_known = WalletBalance(available=100.0)
        wallet_unknown = WalletBalance(available=None)
        
        assert wallet_known.is_available_known() is True
        assert wallet_unknown.is_available_known() is False
    
    def test_is_sufficient(self):
        """Test is_sufficient."""
        wallet = WalletBalance(available=100.0)
        
        assert wallet.is_sufficient(50.0) is True
        assert wallet.is_sufficient(100.0) is True
        assert wallet.is_sufficient(150.0) is False


class TestMarketplaceAccountState:
    """Test marketplace account state."""
    
    def test_account_state_creation(self):
        """Test account state creation."""
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
        )
        
        assert state.platform == MarketplacePlatform.UPWORK
        assert state.account_id == "test_account"
        assert state.account_status == AccountStatus.ACTIVE
        assert state.source == DataSource.UNKNOWN
        assert state.freshness == FreshnessStatus.UNKNOWN
    
    def test_is_data_fresh_with_fresh_status(self):
        """Test is_data_fresh with FRESH status."""
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            freshness=FreshnessStatus.FRESH,
        )
        
        assert state.is_data_fresh() is True
    
    def test_is_data_fresh_with_expired_status(self):
        """Test is_data_fresh with EXPIRED status."""
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            freshness=FreshnessStatus.EXPIRED,
        )
        
        assert state.is_data_fresh() is False
    
    def test_is_data_fresh_with_timestamp(self):
        """Test is_data_fresh with timestamp."""
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            last_verified_at=datetime.utcnow().isoformat(),
        )
        
        assert state.is_data_fresh(max_age_hours=24) is True
    
    def test_is_data_fresh_stale_timestamp(self):
        """Test is_data_fresh with stale timestamp."""
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            last_verified_at=(datetime.utcnow() - timedelta(hours=48)).isoformat(),
        )
        
        assert state.is_data_fresh(max_age_hours=24) is False
    
    def test_has_known_credits(self):
        """Test has_known_credits."""
        state_known = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            credits=CreditBalance(available=10),
        )
        state_unknown = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            credits=CreditBalance(available=None),
        )
        
        assert state_known.has_known_credits() is True
        assert state_unknown.has_known_credits() is False
    
    def test_has_known_wallet(self):
        """Test has_known_wallet."""
        state_known = MarketplaceAccountState(
            platform=MarketplacePlatform.FREELANCER,
            wallet=WalletBalance(available=100.0),
        )
        state_unknown = MarketplaceAccountState(
            platform=MarketplacePlatform.FREELANCER,
            wallet=WalletBalance(available=None),
        )
        
        assert state_known.has_known_wallet() is True
        assert state_unknown.has_known_wallet() is False
    
    def test_is_account_active(self):
        """Test is_account_active."""
        state_active = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_status=AccountStatus.ACTIVE,
        )
        state_verified = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_status=AccountStatus.VERIFIED,
        )
        state_suspended = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_status=AccountStatus.SUSPENDED,
        )
        
        assert state_active.is_account_active() is True
        assert state_verified.is_account_active() is True
        assert state_suspended.is_account_active() is False
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        state = MarketplaceAccountState(
            platform=MarketplacePlatform.UPWORK,
            account_id="test_account",
            account_status=AccountStatus.ACTIVE,
            credits=CreditBalance(available=10, currency="Connects"),
            wallet=WalletBalance(available=100.0, currency="USD"),
        )
        
        result = state.to_dict()
        
        assert result["platform"] == "upwork"
        assert result["account_id"] == "test_account"
        assert result["account_status"] == "active"
        assert result["credits"]["available"] == 10
        assert result["credits"]["currency"] == "Connects"
        assert result["wallet"]["available"] == 100.0
        assert result["wallet"]["currency"] == "USD"
