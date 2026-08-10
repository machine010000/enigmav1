"""
Platform Capability Discovery

TASK-051: Each platform declares its capabilities to Enigma.
Unknown capabilities return "UNKNOWN", not "false" or "free".
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Set


class CapabilityStatus(str, Enum):
    """Capability status."""
    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    UNKNOWN = "UNKNOWN"
    DEPRECATED = "DEPRECATED"
    BETA = "BETA"


@dataclass
class PlatformCapabilityInfo:
    """Information about a platform capability."""
    capability: str
    status: CapabilityStatus
    version: Optional[str] = None
    limitations: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlatformCapabilities:
    """
    Platform capability declarations.
    
    TASK-051: Each platform must declare its capabilities.
    Unknown capabilities return "UNKNOWN", not "false" or "free".
    """
    
    # Standard capabilities that platforms can declare
    JOB_SEARCH = "job_search"
    JOB_DETAILS = "job_details"
    ACCOUNT_BALANCE = "account_balance"
    ACCOUNT_STATUS = "account_status"
    APPLICATION_COST = "application_cost"
    APPLICATION_SUBMISSION = "application_submission"
    APPLICATION_STATUS = "application_status"
    WEBHOOKS = "webhooks"
    OAUTH = "oauth"
    API_KEY_AUTH = "api_key_auth"
    MESSAGING = "messaging"
    CONTRACT_MANAGEMENT = "contract_management"
    PAYMENT_MANAGEMENT = "payment_management"
    PROFILE_MANAGEMENT = "profile_management"
    
    # All standard capabilities
    ALL_CAPABILITIES = [
        JOB_SEARCH,
        JOB_DETAILS,
        ACCOUNT_BALANCE,
        ACCOUNT_STATUS,
        APPLICATION_COST,
        APPLICATION_SUBMISSION,
        APPLICATION_STATUS,
        WEBHOOKS,
        OAUTH,
        API_KEY_AUTH,
        MESSAGING,
        CONTRACT_MANAGEMENT,
        PAYMENT_MANAGEMENT,
        PROFILE_MANAGEMENT,
    ]
    
    def __init__(self, platform: str):
        """
        Initialize platform capabilities.
        
        Args:
            platform: Platform identifier
        """
        self.platform = platform
        self._capabilities: Dict[str, PlatformCapabilityInfo] = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self) -> None:
        """Initialize all capabilities as UNKNOWN."""
        for capability in self.ALL_CAPABILITIES:
            self._capabilities[capability] = PlatformCapabilityInfo(
                capability=capability,
                status=CapabilityStatus.UNKNOWN,
            )
    
    def declare_capability(
        self,
        capability: str,
        status: CapabilityStatus,
        version: Optional[str] = None,
        limitations: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Declare a capability for the platform.
        
        Args:
            capability: Capability identifier
            status: Capability status
            version: Capability version
            limitations: Any limitations
            metadata: Additional metadata
        """
        self._capabilities[capability] = PlatformCapabilityInfo(
            capability=capability,
            status=status,
            version=version,
            limitations=limitations or [],
            metadata=metadata or {},
        )
    
    def supports(self, capability: str) -> bool:
        """
        Check if platform supports a capability.
        
        Args:
            capability: Capability identifier
            
        Returns:
            True if supported, False otherwise
        """
        info = self._capabilities.get(capability)
        if not info:
            return False
        return info.status == CapabilityStatus.SUPPORTED
    
    def get_status(self, capability: str) -> CapabilityStatus:
        """
        Get capability status.
        
        Args:
            capability: Capability identifier
            
        Returns:
            Capability status (UNKNOWN if not declared)
        """
        info = self._capabilities.get(capability)
        if not info:
            return CapabilityStatus.UNKNOWN
        return info.status
    
    def get_info(self, capability: str) -> Optional[PlatformCapabilityInfo]:
        """
        Get capability information.
        
        Args:
            capability: Capability identifier
            
        Returns:
            Capability info or None
        """
        return self._capabilities.get(capability)
    
    def get_supported_capabilities(self) -> Set[str]:
        """
        Get all supported capabilities.
        
        Returns:
            Set of supported capability identifiers
        """
        return {
            cap for cap, info in self._capabilities.items()
            if info.status == CapabilityStatus.SUPPORTED
        }
    
    def get_unsupported_capabilities(self) -> Set[str]:
        """
        Get all unsupported capabilities.
        
        Returns:
            Set of unsupported capability identifiers
        """
        return {
            cap for cap, info in self._capabilities.items()
            if info.status == CapabilityStatus.NOT_SUPPORTED
        }
    
    def get_unknown_capabilities(self) -> Set[str]:
        """
        Get all unknown capabilities.
        
        Returns:
            Set of unknown capability identifiers
        """
        return {
            cap for cap, info in self._capabilities.items()
            if info.status == CapabilityStatus.UNKNOWN
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert capabilities to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "platform": self.platform,
            "capabilities": {
                cap: {
                    "status": info.status.value,
                    "version": info.version,
                    "limitations": info.limitations,
                    "metadata": info.metadata,
                }
                for cap, info in self._capabilities.items()
            },
        }


class CapabilityRegistry:
    """
    Registry for platform capabilities.
    
    TASK-051: Central registry for all platform capabilities.
    """
    
    def __init__(self):
        """Initialize capability registry."""
        self._capabilities: Dict[str, PlatformCapabilities] = {}
    
    def register(self, capabilities: PlatformCapabilities) -> None:
        """
        Register platform capabilities.
        
        Args:
            capabilities: Platform capabilities
        """
        self._capabilities[capabilities.platform] = capabilities
    
    def get(self, platform: str) -> Optional[PlatformCapabilities]:
        """
        Get platform capabilities.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Platform capabilities or None
        """
        return self._capabilities.get(platform)
    
    def supports(self, platform: str, capability: str) -> bool:
        """
        Check if platform supports a capability.
        
        Args:
            platform: Platform identifier
            capability: Capability identifier
            
        Returns:
            False if platform not registered or capability not supported
        """
        capabilities = self.get(platform)
        if not capabilities:
            return False
        return capabilities.supports(capability)
    
    def get_status(self, platform: str, capability: str) -> CapabilityStatus:
        """
        Get capability status for a platform.
        
        Args:
            platform: Platform identifier
            capability: Capability identifier
            
        Returns:
            UNKNOWN if platform not registered or capability unknown
        """
        capabilities = self.get(platform)
        if not capabilities:
            return CapabilityStatus.UNKNOWN
        return capabilities.get_status(capability)
    
    def list_platforms(self) -> list[str]:
        """List all registered platforms."""
        return list(self._capabilities.keys())


# Global capability registry
capability_registry = CapabilityRegistry()
