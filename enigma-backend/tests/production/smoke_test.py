"""
Production Smoke Test Script.

This script runs a comprehensive smoke test to verify that
the production deployment is functioning correctly.
"""
import asyncio
import sys
from typing import Dict, Any
from datetime import datetime

# Add the backend to the path
sys.path.insert(0, "e:/app/enigma/enigma-backend")

from app.core.config import settings, is_production
from app.core.logging_config import get_logger, setup_logging
from app.core.database import check_database_health
from app.marketplace.cost_protection import CostProtection
from app.marketplace.contracts import MarketplacePlatform, PlatformCost, PlatformLimits, CreditType
from app.work_market.approval_gate import ApprovalGate
from app.work_market.application_package import (
    ApplicationPackage,
    ApplicationStatus,
    Proposal,
)
from app.work_market.proposal_strategy import ProposalStrategy, ProposalTone

logger = get_logger(__name__)


class SmokeTestResult:
    """Result of a smoke test."""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.duration_ms = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "duration_ms": self.duration_ms,
        }


class ProductionSmokeTest:
    """Production smoke test suite."""
    
    def __init__(self):
        self.results: list[SmokeTestResult] = []
        self.start_time = datetime.utcnow()
    
    def record_result(self, result: SmokeTestResult) -> None:
        """Record a test result."""
        self.results.append(result)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        logger.info(f"{status}: {result.test_name} - {result.message}")
    
    def test_environment_config(self) -> SmokeTestResult:
        """Test that environment is properly configured."""
        result = SmokeTestResult("Environment Configuration")
        start = datetime.utcnow()
        
        try:
            # In development mode, we allow missing DATABASE_URL
            if is_production():
                if not settings.DATABASE_URL:
                    result.message = "DATABASE_URL not configured in production"
                    return result
                if not settings.NVIDIA_API_KEY:
                    result.message = "NVIDIA_API_KEY not configured in production"
                    return result
                if not settings.SECRET_KEY:
                    result.message = "SECRET_KEY not configured in production"
                    return result
                result.passed = True
                result.message = "All required production environment variables configured"
            else:
                # In development, just check that config loads
                result.passed = True
                result.message = "Configuration loaded (development mode)"
            
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def test_production_mode(self) -> SmokeTestResult:
        """Test that production mode is correctly set."""
        result = SmokeTestResult("Production Mode")
        start = datetime.utcnow()
        
        try:
            if is_production():
                if settings.DEBUG:
                    result.message = "DEBUG is true in production"
                    return result
                result.passed = True
                result.message = "Running in production mode with DEBUG=false"
            else:
                result.passed = True
                result.message = "Running in development mode (acceptable for testing)"
            
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def test_logging_configured(self) -> SmokeTestResult:
        """Test that logging is properly configured."""
        result = SmokeTestResult("Logging Configuration")
        start = datetime.utcnow()
        
        try:
            setup_logging()
            result.passed = True
            result.message = "Logging configured successfully"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def test_approval_gate(self) -> SmokeTestResult:
        """Test that approval gate is working."""
        result = SmokeTestResult("Approval Gate")
        start = datetime.utcnow()
        
        try:
            gate = ApprovalGate()
            
            package = ApplicationPackage(
                application_id="smoke_test_app",
                job_id="smoke_test_job",
                proposal=Proposal(
                    proposal_id="smoke_test_prop",
                    job_id="smoke_test_job",
                    job_understanding="Test",
                    proposed_approach="Test",
                ),
                strategy=ProposalStrategy(
                    strategy_id="smoke_test_strat",
                    job_id="smoke_test_job",
                    strategy_type="value_focused",
                    tone=ProposalTone.PROFESSIONAL,
                ),
            )
            
            # Request approval
            request = gate.request_approval(package, requested_by="smoke_test_user")
            
            if package.status != ApplicationStatus.WAITING_FOR_APPROVAL:
                result.message = "Approval request did not update status"
                return result
            
            # Approve
            approved = gate.approve_application("smoke_test_app", approved_by="smoke_test_admin")
            
            if approved.status != ApplicationStatus.APPROVED:
                result.message = "Approval did not update status"
                return result
            
            # Check can_submit
            if not gate.can_submit(approved):
                result.message = "Approved application cannot be submitted"
                return result
            
            result.passed = True
            result.message = "Approval gate working correctly"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def test_cost_protection(self) -> SmokeTestResult:
        """Test that cost protection is working."""
        result = SmokeTestResult("Cost Protection")
        start = datetime.utcnow()
        
        try:
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
            
            check_result = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
            
            if not check_result.can_submit:
                result.message = f"Cost check failed unexpectedly: {check_result.reason}"
                return result
            
            # Test insufficient credits
            limits_low = PlatformLimits(
                credits_available=2.0,
                credits_total=200.0,
                credit_type=CreditType.CONNECTS,
            )
            protection.update_limits(MarketplacePlatform.UPWORK, limits_low)
            
            check_result_low = protection.check_submission_cost(MarketplacePlatform.UPWORK, cost)
            
            if check_result_low.can_submit:
                result.message = "Cost check should have failed with insufficient credits"
                return result
            
            result.passed = True
            result.message = "Cost protection working correctly"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def test_upwork_adapter_instantiable(self) -> SmokeTestResult:
        """Test that Upwork adapter can be instantiated."""
        result = SmokeTestResult("Upwork Adapter Instantiation")
        start = datetime.utcnow()
        
        try:
            from app.marketplace.upwork_adapter import UpworkAdapter
            
            adapter = UpworkAdapter()
            
            if adapter is None:
                result.message = "Upwork adapter is None"
                return result
            
            result.passed = True
            result.message = "Upwork adapter instantiated successfully"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def test_adapter_registry(self) -> SmokeTestResult:
        """Test that adapter registry is working."""
        result = SmokeTestResult("Adapter Registry")
        start = datetime.utcnow()
        
        try:
            # Import registry to trigger auto-registration
            from app.marketplace import registry
            from app.marketplace.contracts import adapter_registry, MarketplacePlatform
            
            # Check that Upwork adapter is registered
            upwork_adapter = adapter_registry.get(MarketplacePlatform.UPWORK)
            
            if upwork_adapter is None:
                result.message = "Upwork adapter not registered"
                return result
            
            result.passed = True
            result.message = "Adapter registry working correctly"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            result.message = f"Error: {str(e)}"
            result.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests."""
        logger.info("=" * 60)
        logger.info("Starting Production Smoke Test")
        logger.info("=" * 60)
        
        # Run tests
        self.record_result(self.test_environment_config())
        self.record_result(self.test_production_mode())
        self.record_result(self.test_logging_configured())
        self.record_result(self.test_approval_gate())
        self.record_result(self.test_cost_protection())
        self.record_result(self.test_upwork_adapter_instantiable())
        self.record_result(self.test_adapter_registry())
        
        # Calculate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        total_duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": f"{(passed_tests / total_tests * 100):.1f}%",
            "total_duration_ms": total_duration,
            "results": [r.to_dict() for r in self.results],
        }
        
        logger.info("=" * 60)
        logger.info(f"Smoke Test Complete: {passed_tests}/{total_tests} passed")
        logger.info(f"Success Rate: {summary['success_rate']}")
        logger.info(f"Duration: {total_duration:.2f}ms")
        logger.info("=" * 60)
        
        return summary


def main():
    """Main entry point."""
    setup_logging()
    
    smoke_test = ProductionSmokeTest()
    summary = smoke_test.run_all_tests()
    
    # Exit with error code if any tests failed
    if summary["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
