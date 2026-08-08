import pytest

from app.expert_domains.models import DomainMaturity
from app.expert_domains.maturity import MaturityManager


class TestDomainMaturity:
    """Tests for DomainMaturity model."""

    def test_maturity_initialization(self):
        """Test maturity initialization."""
        maturity = DomainMaturity("test_domain")
        assert maturity.domain_id == "test_domain"
        assert maturity.get_average_maturity() == 0.0

    def test_set_concept_maturity(self):
        """Test setting concept maturity."""
        maturity = DomainMaturity("test_domain")
        maturity.set_concept_maturity("concept1", 3)
        assert maturity.get_concept_maturity("concept1") == 3

    def test_set_concept_maturity_clamps_low(self):
        """Test that maturity is clamped to minimum."""
        maturity = DomainMaturity("test_domain")
        maturity.set_concept_maturity("concept1", -1)
        assert maturity.get_concept_maturity("concept1") == 0

    def test_set_concept_maturity_clamps_high(self):
        """Test that maturity is clamped to maximum."""
        maturity = DomainMaturity("test_domain")
        maturity.set_concept_maturity("concept1", 10)
        assert maturity.get_concept_maturity("concept1") == 5

    def test_get_concept_maturity_default(self):
        """Test getting maturity for nonexistent concept."""
        maturity = DomainMaturity("test_domain")
        assert maturity.get_concept_maturity("nonexistent") == 0

    def test_get_average_maturity(self):
        """Test calculating average maturity."""
        maturity = DomainMaturity("test_domain")
        maturity.set_concept_maturity("concept1", 2)
        maturity.set_concept_maturity("concept2", 4)
        assert maturity.get_average_maturity() == 3.0

    def test_get_average_maturity_empty(self):
        """Test average maturity with no concepts."""
        maturity = DomainMaturity("test_domain")
        assert maturity.get_average_maturity() == 0.0

    def test_get_maturity_distribution(self):
        """Test getting maturity distribution."""
        maturity = DomainMaturity("test_domain")
        maturity.set_concept_maturity("concept1", 2)
        maturity.set_concept_maturity("concept2", 2)
        maturity.set_concept_maturity("concept3", 4)
        distribution = maturity.get_maturity_distribution()
        assert distribution[2] == 2
        assert distribution[4] == 1
        assert distribution[0] == 0


class TestMaturityManager:
    """Tests for MaturityManager."""

    def test_maturity_manager_initialization(self):
        """Test maturity manager initialization."""
        manager = MaturityManager("test_domain")
        assert manager.domain_id == "test_domain"

    def test_set_concept_maturity(self):
        """Test setting concept maturity."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 3)
        assert manager.get_concept_maturity("concept1") == 3

    def test_get_concept_maturity(self):
        """Test getting concept maturity."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 3)
        assert manager.get_concept_maturity("concept1") == 3

    def test_get_average_maturity(self):
        """Test getting average maturity."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 2)
        manager.set_concept_maturity("concept2", 4)
        assert manager.get_average_maturity() == 3.0

    def test_get_maturity_distribution(self):
        """Test getting maturity distribution."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 2)
        manager.set_concept_maturity("concept2", 2)
        distribution = manager.get_maturity_distribution()
        assert distribution[2] == 2

    def test_can_increase_maturity(self):
        """Test checking if maturity can be increased."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 2)
        assert manager.can_increase_maturity("concept1", 3) is True
        assert manager.can_increase_maturity("concept1", 2) is False
        assert manager.can_increase_maturity("concept1", 6) is False

    def test_increase_maturity(self):
        """Test increasing maturity."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 2)
        result = manager.increase_maturity("concept1", 4)
        assert result is True
        assert manager.get_concept_maturity("concept1") == 4

    def test_increase_maturity_invalid(self):
        """Test increasing maturity to invalid level."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 2)
        result = manager.increase_maturity("concept1", 2)
        assert result is False
        assert manager.get_concept_maturity("concept1") == 2

    def test_get_maturity_summary(self):
        """Test getting maturity summary."""
        manager = MaturityManager("test_domain")
        manager.set_concept_maturity("concept1", 2)
        manager.set_concept_maturity("concept2", 4)
        summary = manager.get_maturity_summary()
        assert summary["domain_id"] == "test_domain"
        assert summary["average_maturity"] == 3.0
        assert summary["total_concepts"] == 2
        assert "distribution" in summary
