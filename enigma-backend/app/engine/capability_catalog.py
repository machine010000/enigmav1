"""
Capability Catalog — TASK-017

A canonical catalog of capabilities ENIGMA can execute or aspire to execute.

The catalog is NOT the same as the ExecutionEngine's CapabilityRegistry.
- CapabilityRegistry: maps capability_id → registered worker (executable now)
- CapabilityCatalog:  maps capability_id → metadata including freelance threshold,
                      category, module, execution_available flag

The catalog is the single source of truth for:
  - What capabilities exist (including those without a live worker yet)
  - Which module they belong to
  - The minimum confidence required for READY_TO_APPLY
  - Whether execution is currently available

Architecture rule: the LLM receives capability names from the catalog.
Unknown names returned by the LLM must be rejected as UNMAPPED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CatalogEntry:
    """
    A single entry in the capability catalog.

    Fields
    ------
    capability_id : str
        Canonical snake_case identifier.
    name : str
        Human-readable name.
    description : str
        Short description of what this capability does.
    category : str
        High-level grouping (seo, content, research, data, product).
    module : str
        ENIGMA module this belongs to (seller, content_creator, service_provider).
    execution_available : bool
        True if a registered worker currently implements this capability.
        False if capability exists in catalog but no worker yet.
    freelance_readiness_threshold : float
        Minimum confidence (0–1) required before READY_TO_APPLY can be returned
        for an opportunity that requires this capability.
    risk_level : str
        Subjective risk level: low, medium, high.
    """
    capability_id: str
    name: str
    description: str
    category: str
    module: str
    execution_available: bool = False
    freelance_readiness_threshold: float = 0.65
    risk_level: str = "medium"
    # Optional synonyms used during requirement extraction / mapping
    aliases: List[str] = field(default_factory=list)
    # Optional evidence-trust policy. None means no scheduled revalidation policy.
    revalidation_interval_days: Optional[int] = None
    minimum_revalidation_diversity: int = 1
    routing_terms: List[str] = field(default_factory=list)
    execution_input_fields: List[str] = field(default_factory=list)
    routing_reason: str = ""


# ---------------------------------------------------------------------------
# Canonical capability catalog
# Add new capabilities here — never add workers without adding a catalog entry
# ---------------------------------------------------------------------------

_ENTRIES: List[CatalogEntry] = [
    # --- Currently executable (workers exist) ---
    CatalogEntry(
        capability_id="academy_learning",
        name="Academy Learning",
        description="Generate governed learning material for a task or capability gap.",
        category="learning",
        module="service_provider",
        execution_available=True,
        freelance_readiness_threshold=0.65,
        risk_level="low",
        aliases=["learn capability", "training material", "academy research"],
    ),
    CatalogEntry(
        capability_id="product_verification",
        name="Product Verification",
        description="Verify and normalise product metadata including name, category, and quality signals.",
        category="product",
        module="seller",
        execution_available=True,
        freelance_readiness_threshold=0.65,
        risk_level="low",
        aliases=["verify product", "product check", "product audit"],
    ),
    CatalogEntry(
        capability_id="market_analysis",
        name="Market Analysis",
        description="Analyse market segments, competitors, and demand signals for a product or niche.",
        category="research",
        module="seller",
        execution_available=True,
        freelance_readiness_threshold=0.65,
        risk_level="medium",
        aliases=["market research", "competitive analysis", "competitor analysis"],
    ),

    # --- Catalog-only capabilities (no worker yet — return capability gap) ---
    CatalogEntry(
        capability_id="seo_analysis",
        name="SEO Analysis",
        description="Comprehensive analysis of on-page, off-page, and technical SEO factors.",
        category="seo",
        module="service_provider",
        execution_available=False,
        freelance_readiness_threshold=0.70,
        risk_level="medium",
        aliases=["seo audit", "seo review", "seo check", "site audit"],
    ),
    CatalogEntry(
        capability_id="seo_optimization",
        name="SEO Optimization",
        description="Apply SEO improvements based on analysis findings.",
        category="seo",
        module="service_provider",
        execution_available=False,
        freelance_readiness_threshold=0.72,
        risk_level="medium",
        aliases=["on-page seo", "on page optimization", "seo improvements"],
    ),
    CatalogEntry(
        capability_id="keyword_research",
        name="Keyword Research",
        description="Discover and prioritise target keywords using search volume and competition data.",
        category="seo",
        module="service_provider",
        execution_available=True,   # TASK-018: worker now registered
        freelance_readiness_threshold=0.65,
        risk_level="low",
        aliases=["keyword analysis", "keyword discovery", "search terms research"],
        revalidation_interval_days=90,
        minimum_revalidation_diversity=3,
        routing_terms=["keyword", "keywords", "keyword research", "search terms"],
        execution_input_fields=["topic", "seed_keywords", "market", "goal", "audience", "business_model"],
        routing_reason="Keyword research will identify target search terms for the business or product.",
    ),
    CatalogEntry(
        capability_id="competitor_research",
        name="Competitor Research",
        description="Research and profile direct competitors in a given niche.",
        category="research",
        module="service_provider",
        execution_available=True,
        freelance_readiness_threshold=0.65,
        risk_level="low",
        aliases=["competitive research", "competitor analysis"],
        revalidation_interval_days=90,
        minimum_revalidation_diversity=3,
        routing_terms=["competitor research", "competitive research", "competitor analysis", "competitors"],
        execution_input_fields=["business", "product", "industry", "market", "audience", "goal", "competitors"],
        routing_reason="Competitor research will compare supplied market actors and identify strategic differentiation.",
    ),
    CatalogEntry(
        capability_id="social_media_strategy",
        name="Social Media Strategy",
        description="Develop platform-specific social media strategies aligned with business goals.",
        category="content",
        module="content_creator",
        execution_available=False,
        freelance_readiness_threshold=0.70,
        risk_level="medium",
        aliases=["social strategy", "social media plan"],
    ),
    CatalogEntry(
        capability_id="social_media_content",
        name="Social Media Content",
        description="Create posts, captions, and assets for social media platforms.",
        category="content",
        module="content_creator",
        execution_available=False,
        freelance_readiness_threshold=0.68,
        risk_level="low",
        aliases=["social posts", "social content creation"],
    ),
    CatalogEntry(
        capability_id="ad_campaign_analysis",
        name="Ad Campaign Analysis",
        description="Analyse performance of paid advertising campaigns and recommend optimisations.",
        category="research",
        module="service_provider",
        execution_available=False,
        freelance_readiness_threshold=0.72,
        risk_level="high",
        aliases=["ad analysis", "paid ads review", "ppc analysis"],
    ),
    CatalogEntry(
        capability_id="copywriting",
        name="Copywriting",
        description="Write persuasive copy for web pages, ads, emails, and marketing materials.",
        category="content",
        module="content_creator",
        execution_available=False,
        freelance_readiness_threshold=0.68,
        risk_level="low",
        aliases=["copy", "writing", "web copy", "marketing copy"],
    ),
    CatalogEntry(
        capability_id="product_research",
        name="Product Research",
        description="Research product market fit, pricing, and demand for e-commerce contexts.",
        category="product",
        module="seller",
        execution_available=False,
        freelance_readiness_threshold=0.65,
        risk_level="low",
        aliases=["product discovery", "niche research"],
    ),
    CatalogEntry(
        capability_id="product_listing",
        name="Product Listing",
        description="Create optimised product listings for marketplace platforms.",
        category="product",
        module="seller",
        execution_available=False,
        freelance_readiness_threshold=0.68,
        risk_level="low",
        aliases=["listing creation", "product page writing", "marketplace listing"],
    ),
    CatalogEntry(
        capability_id="data_analysis",
        name="Data Analysis",
        description="Analyse datasets to extract insights, trends, and actionable recommendations.",
        category="data",
        module="service_provider",
        execution_available=False,
        freelance_readiness_threshold=0.72,
        risk_level="medium",
        aliases=["data analytics", "analytics", "data insights"],
    ),
]


class CapabilityCatalog:
    """
    Singleton-style catalog providing lookup by capability_id and alias matching.

    Architecture note:
      This extends (not replaces) CapabilityRegistry.
      CapabilityRegistry manages worker resolution.
      CapabilityCatalog manages metadata, thresholds, and requirement mapping.
    """

    def __init__(self, entries: Optional[List[CatalogEntry]] = None) -> None:
        self._by_id: Dict[str, CatalogEntry] = {}
        self._by_alias: Dict[str, str] = {}  # alias_lower → capability_id

        for entry in (entries or _ENTRIES):
            self._by_id[entry.capability_id] = entry
            for alias in entry.aliases:
                self._by_alias[alias.lower()] = entry.capability_id
            # Also register the canonical name and id as aliases
            self._by_alias[entry.name.lower()] = entry.capability_id
            self._by_alias[entry.capability_id.lower()] = entry.capability_id

    def get(self, capability_id: str) -> Optional[CatalogEntry]:
        """Look up a catalog entry by canonical id."""
        return self._by_id.get(capability_id)

    def resolve(self, name_or_id: str) -> Optional[CatalogEntry]:
        """
        Resolve a capability by id, name, or alias.

        Returns None for unknown names — callers must treat None as UNMAPPED.
        Unknown capabilities from LLM output must not be silently executed.
        """
        key = name_or_id.strip().lower()
        # Direct id lookup first
        if key in self._by_id:
            return self._by_id[key]
        # Alias lookup
        resolved_id = self._by_alias.get(key)
        if resolved_id:
            return self._by_id.get(resolved_id)
        return None

    def list_all(self) -> List[CatalogEntry]:
        return list(self._by_id.values())

    def list_by_module(self, module: str) -> List[CatalogEntry]:
        return [e for e in self._by_id.values() if e.module == module]

    def list_by_category(self, category: str) -> List[CatalogEntry]:
        return [e for e in self._by_id.values() if e.category == category]

    def list_executable(self) -> List[CatalogEntry]:
        """Return only capabilities with a registered worker."""
        return [e for e in self._by_id.values() if e.execution_available]

    def ids(self) -> List[str]:
        return list(self._by_id.keys())

    def is_known(self, name_or_id: str) -> bool:
        """Return True if the name/id maps to a known catalog entry."""
        return self.resolve(name_or_id) is not None


# Global singleton
capability_catalog = CapabilityCatalog()
