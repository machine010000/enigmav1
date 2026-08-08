from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DomainStatus(str, Enum):
    """Status of an expert domain."""
    DRAFT = "draft"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class BusinessModule(str, Enum):
    """Business modules that domains can support."""
    FREELANCING = "freelancing"
    BRAND_MARKETING = "brand_marketing"
    CONTENT_CREATION = "content_creation"
    SERVICE_PROVIDER = "service_provider"
    ANALYTICS = "analytics"
    RESEARCH = "research"


class Platform(str, Enum):
    """Platforms that domains can support."""
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    DESKTOP = "desktop"


@dataclass(frozen=True)
class DomainMetadata:
    """Metadata for an expert domain."""
    domain_id: str
    version: str
    owner: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    dependencies: List[str] = field(default_factory=list)
    supported_business_modules: List[BusinessModule] = field(default_factory=list)
    supported_platforms: List[Platform] = field(default_factory=list)
    status: DomainStatus = DomainStatus.DEVELOPMENT
    framework_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    license: str = "MIT"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DomainDependency:
    """Represents a dependency for a domain."""
    dependency_id: str
    dependency_type: str  # domain, capability, library, service
    version_constraint: Optional[str] = None
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class DomainMetadataRegistry:
    """Registry for domain metadata."""

    def __init__(self) -> None:
        self._metadata: Dict[str, DomainMetadata] = {}

    def register(self, metadata: DomainMetadata) -> bool:
        """Register domain metadata."""
        if metadata.domain_id in self._metadata:
            return False
        self._metadata[metadata.domain_id] = metadata
        return True

    def get(self, domain_id: str) -> Optional[DomainMetadata]:
        """Get metadata by domain ID."""
        return self._metadata.get(domain_id)

    def list_all(self) -> List[DomainMetadata]:
        """List all metadata."""
        return list(self._metadata.values())

    def list_by_status(self, status: DomainStatus) -> List[DomainMetadata]:
        """List metadata by status."""
        return [m for m in self._metadata.values() if m.status == status]

    def list_by_business_module(self, module: BusinessModule) -> List[DomainMetadata]:
        """List metadata by supported business module."""
        return [
            m for m in self._metadata.values()
            if module in m.supported_business_modules
        ]

    def update(self, metadata: DomainMetadata) -> bool:
        """Update existing metadata."""
        if metadata.domain_id not in self._metadata:
            return False
        self._metadata[metadata.domain_id] = metadata
        return True

    def remove(self, domain_id: str) -> bool:
        """Remove metadata."""
        if domain_id in self._metadata:
            del self._metadata[domain_id]
            return True
        return False

    def validate_dependencies(
        self,
        domain_id: str,
        available_domains: List[str],
    ) -> Dict[str, bool]:
        """Validate if dependencies are available."""
        metadata = self.get(domain_id)
        if not metadata:
            return {"valid": False, "metadata_found": False}

        required_deps = set(metadata.dependencies)
        available_deps = set(available_domains)

        validation = {
            "valid": True,
            "metadata_found": True,
            "dependencies_met": required_deps.issubset(available_deps),
            "missing_dependencies": list(required_deps - available_deps),
        }

        if not validation["dependencies_met"]:
            validation["valid"] = False

        return validation

    def get_framework_compatibility(self, domain_id: str, framework_version: str) -> bool:
        """Check if domain is compatible with framework version."""
        metadata = self.get(domain_id)
        if not metadata:
            return False

        # Simple version check - in production, use semantic versioning
        return metadata.framework_version == framework_version
