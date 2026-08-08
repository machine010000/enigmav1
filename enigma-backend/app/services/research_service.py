"""
Research Service — the sole responsibility for all research operations.

Web Search, Trend Search, Knowledge Search, and Source Ranking are
handled exclusively by this service.  No Worker may perform its own
searches — it must request the ResearchService instead.

Research produces CandidateKnowledge that must pass through Knowledge Governance
before becoming trusted knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from app.knowledge_governance import CandidateKnowledge, Evidence, SourceType
    KNOWLEDGE_GOVERNANCE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GOVERNANCE_AVAILABLE = False
    # Fallback types if governance not available
    SourceType = str


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    confidence: float = 0.0
    published_at: Optional[str] = None
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "confidence": self.confidence,
            "published_at": self.published_at,
            "rank": self.rank,
        }


@dataclass
class ResearchQuery:
    query: str
    search_type: str = "web"
    max_results: int = 10
    min_confidence: float = 0.3
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchReport:
    query: str
    search_type: str
    results: List[SearchResult] = field(default_factory=list)
    total_found: int = 0
    rank_method: str = "relevance"
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "search_type": self.search_type,
            "results": [r.to_dict() for r in self.results],
            "total_found": self.total_found,
            "rank_method": self.rank_method,
            "generated_at": self.generated_at,
        }

    def to_candidate_knowledge(self) -> Optional[Any]:
        """Convert research results to CandidateKnowledge for governance."""
        if not KNOWLEDGE_GOVERNANCE_AVAILABLE:
            return None

        # Convert search results to Evidence
        evidence_list = []
        for result in self.results:
            published_dt = None
            if result.published_at:
                try:
                    published_dt = datetime.fromisoformat(result.published_at)
                except ValueError:
                    pass

            evidence = Evidence(
                id=f"research-{hash(result.url)}",
                source=result.url,
                source_type=SourceType.EXTERNAL_SOURCE,
                claim=result.snippet,
                retrieved_at=datetime.utcnow(),
                published_at=published_dt,
                quality_score=result.confidence,
                confidence=result.confidence,
            )
            evidence_list.append(evidence)

        # Create CandidateKnowledge
        return CandidateKnowledge(
            id=f"research-{hash(self.query)}",
            name=self.query,
            definition=f"Research findings for: {self.query}",
            evidence=evidence_list,
            source="research_service",
            submitted_at=datetime.utcnow(),
        )


class ResearchService:
    async def web_search(self, query: str, max_results: int = 10, min_confidence: float = 0.3) -> ResearchReport:
        return ResearchReport(query=query, search_type="web", results=[], total_found=0, rank_method="relevance", generated_at=datetime.utcnow().isoformat())

    async def trend_search(self, query: str, market: str = "global", max_results: int = 10) -> ResearchReport:
        return ResearchReport(query=query, search_type="trend", results=[], total_found=0, rank_method="trend_score", generated_at=datetime.utcnow().isoformat())

    async def knowledge_search(self, query: str, category: Optional[str] = None, max_results: int = 10) -> ResearchReport:
        return ResearchReport(query=query, search_type="knowledge", results=[], total_found=0, rank_method="relevance", generated_at=datetime.utcnow().isoformat())

    async def rank_sources(self, results: List[SearchResult], method: str = "relevance") -> List[SearchResult]:
        sorted_results = sorted(results, key=lambda r: r.confidence, reverse=True)
        seen_urls = set()
        ranked: List[SearchResult] = []
        for r in sorted_results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                r.rank = len(ranked) + 1
                ranked.append(r)
        return ranked


research_service = ResearchService()
