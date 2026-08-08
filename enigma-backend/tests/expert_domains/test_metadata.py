import pytest

from app.expert_domains.metadata import (
    DomainMetadata,
    DomainStatus,
    BusinessModule,
    Platform,
    DomainDependency,
    DomainMetadataRegistry,
)


class TestDomainMetadata:
    """Tests for DomainMetadata."""

    def test_domain_metadata_creation(self):
        """Test creating domain metadata."""
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
        )
        assert metadata.domain_id == "seo"
        assert metadata.version == "1.0.0"
        assert metadata.owner == "Enigma"
        assert metadata.status == DomainStatus.DEVELOPMENT

    def test_domain_metadata_with_dependencies(self):
        """Test domain metadata with dependencies."""
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
            dependencies=["analytics", "content"],
            supported_business_modules=[BusinessModule.FREELANCING],
            supported_platforms=[Platform.WEB],
        )
        assert len(metadata.dependencies) == 2
        assert BusinessModule.FREELANCING in metadata.supported_business_modules
        assert Platform.WEB in metadata.supported_platforms


class TestDomainDependency:
    """Tests for DomainDependency."""

    def test_domain_dependency_creation(self):
        """Test creating a domain dependency."""
        dependency = DomainDependency(
            dependency_id="dep1",
            dependency_type="domain",
            version_constraint=">=1.0.0",
        )
        assert dependency.dependency_id == "dep1"
        assert dependency.dependency_type == "domain"
        assert dependency.required is True


class TestDomainMetadataRegistry:
    """Tests for DomainMetadataRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = DomainMetadataRegistry()
        assert registry.list_all() == []

    def test_register_metadata(self):
        """Test registering metadata."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
        )
        result = registry.register(metadata)
        assert result is True
        assert "seo" in [m.domain_id for m in registry.list_all()]

    def test_register_duplicate_metadata(self):
        """Test that registering duplicate metadata fails."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
        )
        registry.register(metadata)
        result = registry.register(metadata)
        assert result is False

    def test_get_metadata(self):
        """Test retrieving metadata."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
        )
        registry.register(metadata)
        retrieved = registry.get("seo")
        assert retrieved is not None
        assert retrieved.domain_id == "seo"

    def test_list_by_status(self):
        """Test listing metadata by status."""
        registry = DomainMetadataRegistry()
        metadata1 = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
            status=DomainStatus.STABLE,
        )
        metadata2 = DomainMetadata(
            domain_id="ads",
            version="1.0.0",
            owner="Enigma",
            description="Ads Expert Domain",
            status=DomainStatus.DEVELOPMENT,
        )
        registry.register(metadata1)
        registry.register(metadata2)
        stable_metadata = registry.list_by_status(DomainStatus.STABLE)
        assert len(stable_metadata) == 1
        assert stable_metadata[0].domain_id == "seo"

    def test_list_by_business_module(self):
        """Test listing metadata by business module."""
        registry = DomainMetadataRegistry()
        metadata1 = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
            supported_business_modules=[BusinessModule.FREELANCING],
        )
        metadata2 = DomainMetadata(
            domain_id="ads",
            version="1.0.0",
            owner="Enigma",
            description="Ads Expert Domain",
            supported_business_modules=[BusinessModule.BRAND_MARKETING],
        )
        registry.register(metadata1)
        registry.register(metadata2)
        freelancing_metadata = registry.list_by_business_module(BusinessModule.FREELANCING)
        assert len(freelancing_metadata) == 1
        assert freelancing_metadata[0].domain_id == "seo"

    def test_update_metadata(self):
        """Test updating metadata."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
        )
        registry.register(metadata)
        updated_metadata = DomainMetadata(
            domain_id="seo",
            version="1.1.0",
            owner="Enigma",
            description="SEO Expert Domain Updated",
        )
        result = registry.update(updated_metadata)
        assert result is True
        retrieved = registry.get("seo")
        assert retrieved.version == "1.1.0"

    def test_validate_dependencies_success(self):
        """Test dependency validation with all dependencies available."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
            dependencies=["analytics", "content"],
        )
        registry.register(metadata)
        validation = registry.validate_dependencies("seo", ["analytics", "content"])
        assert validation["valid"] is True
        assert validation["dependencies_met"] is True

    def test_validate_dependencies_failure(self):
        """Test dependency validation with missing dependencies."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
            dependencies=["analytics", "content"],
        )
        registry.register(metadata)
        validation = registry.validate_dependencies("seo", ["analytics"])
        assert validation["valid"] is False
        assert validation["dependencies_met"] is False
        assert "content" in validation["missing_dependencies"]

    def test_get_framework_compatibility(self):
        """Test framework compatibility check."""
        registry = DomainMetadataRegistry()
        metadata = DomainMetadata(
            domain_id="seo",
            version="1.0.0",
            owner="Enigma",
            description="SEO Expert Domain",
            framework_version="1.0.0",
        )
        registry.register(metadata)
        is_compatible = registry.get_framework_compatibility("seo", "1.0.0")
        assert is_compatible is True
        is_compatible = registry.get_framework_compatibility("seo", "2.0.0")
        assert is_compatible is False
