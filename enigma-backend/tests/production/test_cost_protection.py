"""
Tests for Connects/Cost Protection.

These tests verify that the cost protection system prevents
applications when insufficient credits are available.
"""
import pytest

from app.marketplace.cost_protection import CostProtection, CostCheckResult
from app.marketplace.contracts import (
    MarketplacePlatform,
    PlatformCost,
    PlatformLimits,
    CreditType,
)


class TestCostProtection:
    """Test cost protection functionality."""
    
    def test_update_limits(self):
        """Test that platform limits can be updated."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=100.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
        )
        
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        assert protection.get_available_credits(MarketplacePlatform.UPWORK) == 100.0
    
    def test_check_cost_sufficient_credits(self):
        """Test cost check when credits are sufficient."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=100.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=5.0,
            currency="USD",
            is_free=False,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is True
        assert result.available_credits == 100.0
        assert result.reason is None
    
    def test_check_cost_insufficient_credits(self):
        """Test cost check when credits are insufficient."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=3.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=5.0,
            currency="USD",
            is_free=False,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is False
        assert result.available_credits == 3.0
        assert "Insufficient" in result.reason
    
    def test_check_cost_free_application(self):
        """Test cost check for free application."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=0.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=0.0,
            currency="USD",
            is_free=True,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is True
        assert result.reason == "Application is free"
    
    def test_check_cost_no_limits_available(self):
        """Test cost check when no limits are available."""
        protection = CostProtection()
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=5.0,
            currency="USD",
            is_free=False,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is False
        assert "No account information" in result.reason
    
    def test_deduct_cost(self):
        """Test that cost is deducted after submission."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=100.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
            daily_application_limit=50,
            monthly_application_limit=200,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=5.0,
            currency="USD",
            is_free=False,
        )
        
        protection.deduct_cost(MarketplacePlatform.UPWORK, cost)
        
        assert protection.get_available_credits(MarketplacePlatform.UPWORK) == 95.0
    
    def test_deduct_cost_free_application(self):
        """Test that free applications don't deduct cost."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=100.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=0.0,
            currency="USD",
            is_free=True,
        )
        
        protection.deduct_cost(MarketplacePlatform.UPWORK, cost)
        
        assert protection.get_available_credits(MarketplacePlatform.UPWORK) == 100.0
    
    def test_check_cost_daily_limit_reached(self):
        """Test cost check when daily limit is reached."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=100.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
            daily_application_limit=0,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=5.0,
            currency="USD",
            is_free=False,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is False
        assert "Daily application limit" in result.reason
    
    def test_check_cost_monthly_limit_reached(self):
        """Test cost check when monthly limit is reached."""
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=100.0,
            credits_total=200.0,
            credit_type=CreditType.CONNECTS,
            monthly_application_limit=0,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=5.0,
            currency="USD",
            is_free=False,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is False
        assert "Monthly application limit" in result.reason
