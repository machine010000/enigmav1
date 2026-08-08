from __future__ import annotations

from typing import Dict, List, Optional

from app.work_market.models import (
    Platform,
    PlatformType,
    PlatformConnectionStatus,
    JobSource,
)


class PlatformRegistry:
    """Registry for freelance platforms with capability contracts."""

    def __init__(self) -> None:
        self._platforms: Dict[str, Platform] = {}
        self._initialize_default_platforms()

    def _initialize_default_platforms(self) -> None:
        """Initialize default platform contracts."""
        # Upwork - Proposal-based platform
        self._platforms["upwork"] = Platform(
            platform_id="upwork",
            name="Upwork",
            type=PlatformType.PROPOSAL_BASED,
            connection_status=PlatformConnectionStatus.NOT_CONNECTED,
            auth_status="not_authenticated",
            profile_status="not_set_up",
            application_model="Proposal-based with connects",
            capabilities=[
                "job_discovery",
                "job_retrieval",
                "application_submission",
                "messaging",
                "contract_management",
            ],
            application_requirements={
                "requires_connects": True,
                "requires_profile_verification": True,
                "requires_portfolio": False,
                "requires_payment_method": True,
            },
            credits_available=None,
            availability="available",
            proposal_rules={
                "max_proposals_per_day": 20,
                "max_proposals_per_month": 300,
                "proposal_length_min": 50,
                "proposal_length_max": 5000,
                "requires_connects": True,
                "connects_per_proposal": 1,
            },
            pricing_rules={
                "platform_fee_percentage": 20.0,
                "service_fee_percentage": 5.0,
                "minimum_hourly_rate": 3.0,
                "minimum_fixed_price": 5.0,
            },
            connection_requirements={
                "requires_email_verification": True,
                "requires_phone_verification": True,
                "requires_identity_verification": True,
                "requires_payment_method": True,
            },
            limits={
                "max_active_proposals": 50,
                "max_concurrent_contracts": 20,
                "max_hourly_rate": 1000.0,
                "max_fixed_price": 10000.0,
            },
        )

        # Freelancer - Bid-based platform
        self._platforms["freelancer"] = Platform(
            platform_id="freelancer",
            name="Freelancer",
            type=PlatformType.BID_BASED,
            connection_status=PlatformConnectionStatus.NOT_CONNECTED,
            auth_status="not_authenticated",
            profile_status="not_set_up",
            application_model="Bid-based with membership tiers",
            capabilities=[
                "job_discovery",
                "job_retrieval",
                "application_submission",
                "messaging",
                "contest_participation",
            ],
            application_requirements={
                "requires_bids": True,
                "requires_profile_verification": True,
                "requires_portfolio": False,
                "requires_payment_method": True,
            },
            credits_available=None,
            availability="available",
            proposal_rules={
                "max_bids_per_day": 30,
                "max_bids_per_month": 500,
                "bid_length_min": 30,
                "bid_length_max": 3000,
                "requires_bids": True,
                "bids_per_project": 1,
            },
            pricing_rules={
                "platform_fee_percentage": 10.0,
                "project_fee_percentage": 3.0,
                "minimum_hourly_rate": 5.0,
                "minimum_fixed_price": 10.0,
            },
            connection_requirements={
                "requires_email_verification": True,
                "requires_phone_verification": False,
                "requires_identity_verification": True,
                "requires_payment_method": True,
            },
            limits={
                "max_active_bids": 100,
                "max_concurrent_contracts": 30,
                "max_hourly_rate": 500.0,
                "max_fixed_price": 5000.0,
            },
        )

        # Fiverr - Gig-based platform
        self._platforms["fiverr"] = Platform(
            platform_id="fiverr",
            name="Fiverr",
            type=PlatformType.GIG_BASED,
            connection_status=PlatformConnectionStatus.NOT_CONNECTED,
            auth_status="not_authenticated",
            profile_status="not_set_up",
            application_model="Gig-based with buyer requests",
            capabilities=[
                "gig_creation",
                "buyer_request_response",
                "messaging",
                "order_management",
            ],
            application_requirements={
                "requires_gig_setup": True,
                "requires_profile_verification": True,
                "requires_portfolio": True,
                "requires_payment_method": True,
            },
            credits_available=None,
            availability="available",
            proposal_rules={
                "max_gigs": 7,
                "max_buyer_requests_per_day": 10,
                "gig_description_min": 100,
                "gig_description_max": 1200,
                "requires_gig": True,
            },
            pricing_rules={
                "platform_fee_percentage": 20.0,
                "service_fee_percentage": 0.0,
                "minimum_gig_price": 5.0,
                "maximum_gig_price": 10000.0,
            },
            connection_requirements={
                "requires_email_verification": True,
                "requires_phone_verification": True,
                "requires_identity_verification": True,
                "requires_payment_method": True,
            },
            limits={
                "max_active_gigs": 7,
                "max_concurrent_orders": 10,
                "max_gig_price": 10000.0,
                "max_gig_packages": 3,
            },
        )

        # Khamsat - Arabic marketplace
        self._platforms["khamsat"] = Platform(
            platform_id="khamsat",
            name="Khamsat",
            type=PlatformType.GIG_BASED,
            connection_status=PlatformConnectionStatus.NOT_CONNECTED,
            auth_status="not_authenticated",
            profile_status="not_set_up",
            application_model="Gig-based Arabic marketplace",
            capabilities=[
                "gig_creation",
                "service_request_response",
                "messaging",
                "order_management",
            ],
            application_requirements={
                "requires_gig_setup": True,
                "requires_profile_verification": True,
                "requires_portfolio": True,
                "requires_payment_method": True,
            },
            credits_available=None,
            availability="available",
            proposal_rules={
                "max_gigs": 10,
                "max_service_requests_per_day": 15,
                "gig_description_min": 150,
                "gig_description_max": 1500,
                "requires_gig": True,
            },
            pricing_rules={
                "platform_fee_percentage": 15.0,
                "service_fee_percentage": 0.0,
                "minimum_gig_price": 5.0,
                "maximum_gig_price": 5000.0,
            },
            connection_requirements={
                "requires_email_verification": True,
                "requires_phone_verification": False,
                "requires_identity_verification": True,
                "requires_payment_method": True,
            },
            limits={
                "max_active_gigs": 10,
                "max_concurrent_orders": 15,
                "max_gig_price": 5000.0,
                "max_gig_packages": 3,
            },
        )

        # Mostaql - Arabic marketplace
        self._platforms["mostaql"] = Platform(
            platform_id="mostaql",
            name="Mostaql",
            type=PlatformType.PROPOSAL_BASED,
            connection_status=PlatformConnectionStatus.NOT_CONNECTED,
            auth_status="not_authenticated",
            profile_status="not_set_up",
            application_model="Proposal-based Arabic marketplace",
            capabilities=[
                "job_discovery",
                "job_retrieval",
                "application_submission",
                "messaging",
                "contract_management",
            ],
            application_requirements={
                "requires_proposals": True,
                "requires_profile_verification": True,
                "requires_portfolio": False,
                "requires_payment_method": True,
            },
            credits_available=None,
            availability="available",
            proposal_rules={
                "max_proposals_per_day": 25,
                "max_proposals_per_month": 400,
                "proposal_length_min": 100,
                "proposal_length_max": 4000,
                "requires_proposals": True,
                "proposals_per_project": 1,
            },
            pricing_rules={
                "platform_fee_percentage": 15.0,
                "project_fee_percentage": 5.0,
                "minimum_hourly_rate": 5.0,
                "minimum_fixed_price": 50.0,
            },
            connection_requirements={
                "requires_email_verification": True,
                "requires_phone_verification": True,
                "requires_identity_verification": True,
                "requires_payment_method": True,
            },
            limits={
                "max_active_proposals": 75,
                "max_concurrent_contracts": 25,
                "max_hourly_rate": 1000.0,
                "max_fixed_price": 20000.0,
            },
        )

    def get_platform(self, platform_id: str) -> Optional[Platform]:
        """Get a platform by ID."""
        return self._platforms.get(platform_id)

    def get_all_platforms(self) -> List[Platform]:
        """Get all registered platforms."""
        return list(self._platforms.values())

    def register_platform(self, platform: Platform) -> None:
        """Register a new platform."""
        self._platforms[platform.platform_id] = platform

    def update_platform_status(
        self,
        platform_id: str,
        connection_status: PlatformConnectionStatus,
        auth_status: str = "not_authenticated",
        profile_status: str = "not_set_up",
        credits_available: Optional[int] = None,
    ) -> Optional[Platform]:
        """Update platform connection status."""
        platform = self._platforms.get(platform_id)
        if not platform:
            return None

        # Create updated platform (immutable dataclass pattern)
        updated = Platform(
            platform_id=platform.platform_id,
            name=platform.name,
            type=platform.type,
            connection_status=connection_status,
            auth_status=auth_status,
            profile_status=profile_status,
            application_model=platform.application_model,
            capabilities=platform.capabilities,
            application_requirements=platform.application_requirements,
            credits_available=credits_available,
            availability=platform.availability,
            metadata=platform.metadata,
            registered_at=platform.registered_at,
            proposal_rules=platform.proposal_rules,
            pricing_rules=platform.pricing_rules,
            connection_requirements=platform.connection_requirements,
            limits=platform.limits,
        )

        self._platforms[platform_id] = updated
        return updated

    def get_platform_by_source(self, source: JobSource) -> Optional[Platform]:
        """Get platform by job source."""
        return self._platforms.get(source.value)

    def has_capability(self, platform_id: str, capability: str) -> bool:
        """Check if platform has a specific capability."""
        platform = self._platforms.get(platform_id)
        if not platform:
            return False
        return capability in platform.capabilities

    def get_application_cost(self, platform_id: str) -> Optional[Dict[str, any]]:
        """Get application cost information for a platform."""
        platform = self._platforms.get(platform_id)
        if not platform:
            return None

        return {
            "platform_id": platform_id,
            "credits_available": platform.credits_available,
            "requirements": platform.application_requirements,
        }
