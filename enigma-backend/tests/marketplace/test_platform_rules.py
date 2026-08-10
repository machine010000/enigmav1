"""
Test Platform Rules
"""

import pytest

from app.marketplace.platform_rules import (
    PlatformRules,
    PlatformApplicationCost,
    ApplicationCostType,
    get_platform_rules,
    UPWORK_RULES,
    FREELANCER_RULES,
    FIVERR_RULES,
)
from app.marketplace.contracts import MarketplacePlatform


class TestPlatformApplicationCost:
    """Test platform application cost."""
    
    def test_application_cost_creation(self):
        """Test application cost creation."""
        cost = PlatformApplicationCost(
            cost_type=ApplicationCostType.CREDITS,
            cost_amount=2,
            currency="Connects",
        )
        
        assert cost.cost_type == ApplicationCostType.CREDITS
        assert cost.cost_amount == 2
        assert cost.currency == "Connects"
    
    def test_is_cost_known(self):
        """Test is_cost_known."""
        cost_known = PlatformApplicationCost(
            cost_type=ApplicationCostType.CREDITS,
            cost_amount=2,
        )
        cost_unknown = PlatformApplicationCost(
            cost_type=ApplicationCostType.UNKNOWN,
        )
        
        assert cost_known.is_cost_known() is True
        assert cost_unknown.is_cost_known() is False
    
    def test_is_free(self):
        """Test is_free."""
        cost_free = PlatformApplicationCost(cost_type=ApplicationCostType.FREE)
        cost_paid = PlatformApplicationCost(
            cost_type=ApplicationCostType.CREDITS,
            cost_amount=2,
        )
        
        assert cost_free.is_free() is True
        assert cost_paid.is_free() is False


class TestPlatformRules:
    """Test platform rules."""
    
    def test_platform_rules_creation(self):
        """Test platform rules creation."""
        rules = PlatformRules(
            platform=MarketplacePlatform.UPWORK,
            application_cost=PlatformApplicationCost(
                cost_type=ApplicationCostType.CREDITS,
                cost_amount=2,
            ),
            requires_credits=True,
            credit_currency="Connects",
        )
        
        assert rules.platform == MarketplacePlatform.UPWORK
        assert rules.requires_credits is True
        assert rules.credit_currency == "Connects"
    
    def test_get_application_cost_for_job(self):
        """Test get_application_cost_for_job."""
        rules = PlatformRules(
            platform=MarketplacePlatform.UPWORK,
            application_cost=PlatformApplicationCost(
                cost_type=ApplicationCostType.CREDITS,
                cost_amount=2,
            ),
        )
        
        job_data = {"title": "Test Job"}
        cost = rules.get_application_cost_for_job(job_data)
        
        assert cost.cost_type == ApplicationCostType.CREDITS
        assert cost.cost_amount == 2
    
    def test_is_data_stale_with_fresh_data(self):
        """Test is_data_stale with fresh data."""
        from datetime import datetime, timedelta
        
        rules = PlatformRules(platform=MarketplacePlatform.UPWORK)
        fresh_timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        assert rules.is_data_stale(fresh_timestamp) is False
    
    def test_is_data_stale_with_stale_data(self):
        """Test is_data_stale with stale data."""
        from datetime import datetime, timedelta
        
        rules = PlatformRules(platform=MarketplacePlatform.UPWORK)
        stale_timestamp = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        
        assert rules.is_data_stale(stale_timestamp) is True
    
    def test_is_data_stale_with_none_timestamp(self):
        """Test is_data_stale with None timestamp."""
        rules = PlatformRules(platform=MarketplacePlatform.UPWORK)
        
        assert rules.is_data_stale(None) is True


class TestGetPlatformRules:
    """Test get_platform_rules function."""
    
    def test_get_upwork_rules(self):
        """Test get Upwork rules."""
        rules = get_platform_rules(MarketplacePlatform.UPWORK)
        
        assert rules.platform == MarketplacePlatform.UPWORK
        assert rules.requires_credits is True
        assert rules.credit_currency == "Connects"
        assert rules.application_cost.cost_type == ApplicationCostType.CREDITS
    
    def test_get_freelancer_rules(self):
        """Test get Freelancer rules."""
        rules = get_platform_rules(MarketplacePlatform.FREELANCER)
        
        assert rules.platform == MarketplacePlatform.FREELANCER
        assert rules.requires_wallet is True
        assert rules.wallet_currency == "USD"
        assert rules.application_cost.cost_type == ApplicationCostType.MONETARY
    
    def test_get_fiverr_rules(self):
        """Test get Fiverr rules."""
        rules = get_platform_rules(MarketplacePlatform.FIVERR)
        
        assert rules.platform == MarketplacePlatform.FIVERR
        assert rules.application_cost.cost_type == ApplicationCostType.FREE
    
    def test_get_mostaql_rules(self):
        """Test get Mostaql rules."""
        rules = get_platform_rules(MarketplacePlatform.MOSTAQL)
        
        assert rules.platform == MarketplacePlatform.MOSTAQL
        assert rules.application_cost.cost_type == ApplicationCostType.FREE
    
    def test_get_khamsat_rules(self):
        """Test get Khamsat rules."""
        rules = get_platform_rules(MarketplacePlatform.KHAMSAT)
        
        assert rules.platform == MarketplacePlatform.KHAMSAT
        assert rules.application_cost.cost_type == ApplicationCostType.FREE


class TestPredefinedRules:
    """Test predefined platform rules."""
    
    def test_upwork_rules_predefined(self):
        """Test Upwork rules are predefined correctly."""
        assert UPWORK_RULES.platform == MarketplacePlatform.UPWORK
        assert UPWORK_RULES.requires_credits is True
        assert UPWORK_RULES.credit_currency == "Connects"
        assert UPWORK_RULES.application_cost.cost_amount == 2
    
    def test_freelancer_rules_predefined(self):
        """Test Freelancer rules are predefined correctly."""
        assert FREELANCER_RULES.platform == MarketplacePlatform.FREELANCER
        assert FREELANCER_RULES.requires_wallet is True
        assert FREELANCER_RULES.wallet_currency == "USD"
        assert FREELANCER_RULES.application_cost.cost_amount == 0.50
    
    def test_fiverr_rules_predefined(self):
        """Test Fiverr rules are predefined correctly."""
        assert FIVERR_RULES.platform == MarketplacePlatform.FIVERR
        assert FIVERR_RULES.application_cost.is_free() is True
