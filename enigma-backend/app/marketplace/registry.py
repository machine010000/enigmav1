"""
Marketplace Adapter Registry.

Manages the registration and retrieval of marketplace adapters.
This module initializes and registers all available adapters.
"""
from app.marketplace.contracts import adapter_registry
from app.marketplace.mock_adapter import MockMarketplaceAdapter
from app.marketplace.upwork_adapter import UpworkAdapter


def register_adapters() -> None:
    """Register all available marketplace adapters."""
    # Register Mock adapter (for testing)
    mock_adapter = MockMarketplaceAdapter()
    adapter_registry.register(mock_adapter)
    
    # Register Upwork adapter (for production use)
    # Note: Upwork adapter requires credentials to function
    # It will be registered but not authenticated until credentials are provided
    upwork_adapter = UpworkAdapter()
    adapter_registry.register(upwork_adapter)


# Auto-register on module import
register_adapters()
