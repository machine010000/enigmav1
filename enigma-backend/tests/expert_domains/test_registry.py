import pytest

from app.expert_domains.contracts import ExpertDomainContract
from app.expert_domains.registry import ExpertDomainRegistry, expert_domain_registry
from tests.expert_domains.test_contracts import MockExpertDomain


class TestExpertDomainRegistry:
    """Tests for ExpertDomainRegistry."""

    def test_registry_initialization(self):
        """Test that registry initializes correctly."""
        registry = ExpertDomainRegistry()
        assert registry.list_ids() == []
        assert registry.list_all() == []

    def test_register_domain(self):
        """Test registering a domain."""
        registry = ExpertDomainRegistry()
        domain = MockExpertDomain("domain1")
        result = registry.register(domain)
        assert result is True
        assert "domain1" in registry.list_ids()

    def test_register_duplicate_domain(self):
        """Test that registering a duplicate domain fails."""
        registry = ExpertDomainRegistry()
        domain1 = MockExpertDomain("domain1")
        domain2 = MockExpertDomain("domain1")
        registry.register(domain1)
        result = registry.register(domain2)
        assert result is False

    def test_get_domain(self):
        """Test retrieving a domain."""
        registry = ExpertDomainRegistry()
        domain = MockExpertDomain("domain1")
        registry.register(domain)
        retrieved = registry.get("domain1")
        assert retrieved is not None
        assert retrieved.get_identity().domain_id == "domain1"

    def test_get_nonexistent_domain(self):
        """Test retrieving a nonexistent domain."""
        registry = ExpertDomainRegistry()
        retrieved = registry.get("nonexistent")
        assert retrieved is None

    def test_list_all_domains(self):
        """Test listing all domains."""
        registry = ExpertDomainRegistry()
        domain1 = MockExpertDomain("domain1")
        domain2 = MockExpertDomain("domain2")
        registry.register(domain1)
        registry.register(domain2)
        domains = registry.list_all()
        assert len(domains) == 2

    def test_list_domain_ids(self):
        """Test listing domain IDs."""
        registry = ExpertDomainRegistry()
        domain1 = MockExpertDomain("domain1")
        domain2 = MockExpertDomain("domain2")
        registry.register(domain1)
        registry.register(domain2)
        ids = registry.list_ids()
        assert "domain1" in ids
        assert "domain2" in ids

    def test_unregister_domain(self):
        """Test unregistering a domain."""
        registry = ExpertDomainRegistry()
        domain = MockExpertDomain("domain1")
        registry.register(domain)
        result = registry.unregister("domain1")
        assert result is True
        assert "domain1" not in registry.list_ids()

    def test_unregister_nonexistent_domain(self):
        """Test unregistering a nonexistent domain."""
        registry = ExpertDomainRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_validate_contract_valid(self):
        """Test validating a valid contract."""
        registry = ExpertDomainRegistry()
        domain = MockExpertDomain()
        result = registry.validate_contract(domain)
        assert result is True

    def test_validate_contract_invalid(self):
        """Test validating an invalid contract."""
        registry = ExpertDomainRegistry()
        class InvalidDomain:
            """Invalid domain missing required methods."""
            pass
        domain = InvalidDomain()
        result = registry.validate_contract(domain)
        assert result is False

    def test_report_maturity(self):
        """Test reporting maturity for a domain."""
        registry = ExpertDomainRegistry()
        domain = MockExpertDomain()
        registry.register(domain)
        maturity = registry.report_maturity("test_domain")
        assert maturity is not None
        assert "average_maturity" in maturity
        assert "distribution" in maturity

    def test_report_maturity_nonexistent(self):
        """Test reporting maturity for a nonexistent domain."""
        registry = ExpertDomainRegistry()
        maturity = registry.report_maturity("nonexistent")
        assert maturity is None

    def test_report_readiness(self):
        """Test reporting readiness for a domain."""
        registry = ExpertDomainRegistry()
        domain = MockExpertDomain()
        registry.register(domain)
        readiness = registry.report_readiness("test_domain")
        assert readiness is not None
        assert "knowledge_readiness" in readiness
        assert "execution_readiness" in readiness
        assert "evidence_readiness" in readiness
        assert "learning_readiness" in readiness
        assert "overall_readiness" in readiness

    def test_report_readiness_nonexistent(self):
        """Test reporting readiness for a nonexistent domain."""
        registry = ExpertDomainRegistry()
        readiness = registry.report_readiness("nonexistent")
        assert readiness is None

    def test_global_registry_exists(self):
        """Test that the global registry exists."""
        assert expert_domain_registry is not None
        assert isinstance(expert_domain_registry, ExpertDomainRegistry)
