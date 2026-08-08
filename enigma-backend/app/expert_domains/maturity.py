from __future__ import annotations

from app.expert_domains.models import DomainMaturity


class MaturityManager:
    """Manages knowledge maturity for expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.maturity = DomainMaturity(domain_id)

    def set_concept_maturity(self, concept_id: str, maturity: int) -> None:
        """Set the maturity level for a concept."""
        self.maturity.set_concept_maturity(concept_id, maturity)

    def get_concept_maturity(self, concept_id: str) -> int:
        """Get the maturity level for a concept."""
        return self.maturity.get_concept_maturity(concept_id)

    def get_average_maturity(self) -> float:
        """Get the average maturity level across all concepts."""
        return self.maturity.get_average_maturity()

    def get_maturity_distribution(self) -> dict:
        """Get the distribution of maturity levels."""
        return self.maturity.get_maturity_distribution()

    def can_increase_maturity(self, concept_id: str, to_level: int) -> bool:
        """Check if concept maturity can be increased to a given level."""
        current_level = self.get_concept_maturity(concept_id)
        return to_level > current_level and to_level <= 5

    def increase_maturity(self, concept_id: str, to_level: int) -> bool:
        """Increase concept maturity to a given level."""
        if self.can_increase_maturity(concept_id, to_level):
            self.set_concept_maturity(concept_id, to_level)
            return True
        return False

    def get_maturity_summary(self) -> dict:
        """Get a summary of maturity status."""
        return {
            "domain_id": self.domain_id,
            "average_maturity": self.get_average_maturity(),
            "distribution": self.get_maturity_distribution(),
            "total_concepts": len(self.maturity._concept_maturity),
        }
