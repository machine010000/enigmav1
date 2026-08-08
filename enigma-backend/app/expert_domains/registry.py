from __future__ import annotations

from typing import Dict, List, Optional

from app.expert_domains.contracts import ExpertDomainContract, DomainIdentity


class ExpertDomainRegistry:
    """Registry for expert domains."""

    def __init__(self) -> None:
        self._domains: Dict[str, ExpertDomainContract] = {}

    def register(self, domain: ExpertDomainContract) -> bool:
        """Register an expert domain."""
        domain_id = domain.get_identity().domain_id

        if domain_id in self._domains:
            return False

        self._domains[domain_id] = domain
        return True

    def get(self, domain_id: str) -> Optional[ExpertDomainContract]:
        """Get a registered domain by ID."""
        return self._domains.get(domain_id)

    def list_all(self) -> List[ExpertDomainContract]:
        """List all registered domains."""
        return list(self._domains.values())

    def list_ids(self) -> List[str]:
        """List all registered domain IDs."""
        return list(self._domains.keys())

    def unregister(self, domain_id: str) -> bool:
        """Unregister a domain."""
        if domain_id in self._domains:
            del self._domains[domain_id]
            return True
        return False

    def validate_contract(self, domain: ExpertDomainContract) -> bool:
        """Validate that a domain implements the contract correctly."""
        # Check that all required methods are implemented
        required_methods = [
            "get_identity",
            "get_knowledge_areas",
            "get_concepts",
            "get_evidence_types",
            "get_reasoning_patterns",
            "get_decision_rules",
            "get_kpis",
            "get_execution_standards",
            "evaluate",
            "get_readiness",
            "get_lifecycle_stage",
            "can_advance_to_stage",
        ]

        for method in required_methods:
            if not hasattr(domain, method):
                return False

        return True

    def report_maturity(self, domain_id: str) -> Optional[Dict[str, int]]:
        """Report maturity information for a domain."""
        domain = self.get(domain_id)
        if not domain:
            return None

        # Placeholder: return maturity information
        return {"average_maturity": 0, "distribution": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}

    def report_readiness(self, domain_id: str) -> Optional[Dict[str, float]]:
        """Report readiness information for a domain."""
        domain = self.get(domain_id)
        if not domain:
            return None

        readiness = domain.get_readiness()
        return {
            "knowledge_readiness": readiness.knowledge_readiness,
            "execution_readiness": readiness.execution_readiness,
            "evidence_readiness": readiness.evidence_readiness,
            "learning_readiness": readiness.learning_readiness,
            "overall_readiness": readiness.overall_readiness,
        }


# Global registry instance
expert_domain_registry = ExpertDomainRegistry()
