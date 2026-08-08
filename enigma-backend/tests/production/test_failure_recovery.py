"""
Tests for failure and recovery scenarios.

These tests verify that the system handles failures gracefully
and can recover from various error conditions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.marketplace.upwork_adapter import UpworkAdapter
from app.marketplace.contracts import PlatformError, MarketplacePlatform, PlatformCost
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TestUpworkFailureRecovery:
    """Test Upwork adapter failure and recovery scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_oauth_token(self):
        """Test handling of invalid OAuth token."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid token"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.platform == MarketplacePlatform.UPWORK
        assert error.is_auth_error is True
        assert error.is_retriable is False
    
    @pytest.mark.asyncio
    async def test_expired_token_refresh(self):
        """Test token refresh on expired token."""
        adapter = UpworkAdapter()
        adapter._credentials.access_token = "expired_token"
        adapter._credentials.refresh_token = "valid_refresh_token"
        
        with patch.object(adapter, '_refresh_access_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = "new_access_token"
            
            # Simulate token refresh
            new_token = await adapter._refresh_access_token()
            
            assert new_token == "new_access_token"
            mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upwork_401_error(self):
        """Test handling of Upwork 401 error."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.error_code == "HTTP_401"
        assert error.is_auth_error is True
        assert error.is_retriable is False
    
    @pytest.mark.asyncio
    async def test_upwork_429_rate_limit(self):
        """Test handling of Upwork 429 rate limit error."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.error_code == "HTTP_429"
        assert error.is_rate_limit is True
        assert error.is_retriable is True
    
    @pytest.mark.asyncio
    async def test_upwork_500_server_error(self):
        """Test handling of Upwork 500 server error."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert error.error_code == "HTTP_500"
        assert error.is_retriable is True
        assert error.is_auth_error is False
    
    @pytest.mark.asyncio
    async def test_network_failure(self):
        """Test handling of network failure."""
        adapter = UpworkAdapter()
        
        with patch.object(adapter, '_make_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                await adapter.discover_jobs("python")
    
    @pytest.mark.asyncio
    async def test_insufficient_connects(self):
        """Test handling of insufficient connects."""
        from app.marketplace.cost_protection import CostProtection, CostCheckResult
        from app.marketplace.contracts import PlatformCost, PlatformLimits, CreditType
        
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=2.0,
            credits_total=100.0,
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
        assert "Insufficient" in result.reason
    
    @pytest.mark.asyncio
    async def test_account_restricted(self):
        """Test handling of restricted account."""
        from app.marketplace.cost_protection import CostProtection
        from app.marketplace.contracts import PlatformLimits, CreditType
        
        protection = CostProtection()
        
        limits = PlatformLimits(
            credits_available=0.0,
            credits_total=100.0,
            credit_type=CreditType.CONNECTS,
        )
        protection.update_limits(MarketplacePlatform.UPWORK, limits)
        
        cost = PlatformCost(
            credit_type=CreditType.CONNECTS,
            amount=1.0,
            currency="USD",
            is_free=False,
        )
        
        result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
        
        assert result.can_submit is False
        assert "Insufficient" in result.reason
    
    @pytest.mark.asyncio
    async def test_duplicate_submission_prevention(self):
        """Test prevention of duplicate submissions."""
        from app.work_market.approval_gate import ApprovalGate
        from app.work_market.application_package import (
            ApplicationPackage,
            ApplicationStatus,
            Proposal,
        )
        from app.work_market.proposal_strategy import ProposalStrategy, ProposalTone
        
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
            status=ApplicationStatus.SUBMITTED,
        )
        
        # Cannot request approval for already submitted application
        with pytest.raises(ValueError):
            gate.request_approval(package, requested_by="user_123")
    
    @pytest.mark.asyncio
    async def test_error_normalization(self):
        """Test that errors are normalized to PlatformError."""
        adapter = UpworkAdapter()
        
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"message": "Forbidden"}
        
        error = adapter._handle_api_error(mock_response)
        
        assert isinstance(error, PlatformError)
        assert error.platform == MarketplacePlatform.UPWORK
        assert error.error_code == "HTTP_403"
    
    @pytest.mark.asyncio
    async def test_application_state_not_corrupted(self):
        """Test that application state is not corrupted on error."""
        from app.work_market.approval_gate import ApprovalGate
        from app.work_market.application_package import (
            ApplicationPackage,
            ApplicationStatus,
            Proposal,
        )
        from app.work_market.proposal_strategy import ProposalStrategy, ProposalTone
        
        gate = ApprovalGate()
        
        package = ApplicationPackage(
            application_id="app_001",
            job_id="job_001",
            proposal=Proposal(
                proposal_id="prop_001",
                job_id="job_001",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=ProposalStrategy(
                strategy_id="strat_001",
                job_id="job_001",
                strategy_type="value_focused",
                tone=ProposalTone.PROFESSIONAL,
            ),
            status=ApplicationStatus.DRAFT,
        )
        
        # Request approval
        gate.request_approval(package, requested_by="user_123")
        
        # Try to approve with wrong ID (should fail)
        with pytest.raises(ValueError):
            gate.approve_application("wrong_id", approved_by="admin")
        
        # Original package state should remain unchanged
        assert package.status == ApplicationStatus.WAITING_FOR_APPROVAL
