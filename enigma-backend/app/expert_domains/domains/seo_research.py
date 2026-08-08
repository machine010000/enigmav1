from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.knowledge_governance.models import (
    CandidateKnowledge,
    Evidence,
    SourceType,
    KnowledgeMaturity,
    KnowledgeFreshness,
)


class ResearchSource(str, Enum):
    """Types of research sources for SEO knowledge."""
    GOOGLE_DOCUMENTATION = "google_documentation"
    SEARCH_CENTRAL = "search_central"
    SEARCH_QUALITY_GUIDELINES = "search_quality_guidelines"
    CORE_WEB_VITALS = "core_web_vitals"
    STRUCTURED_DATA = "structured_data"
    SEARCH_CONSOLE = "search_console"
    MOZ_BLOG = "moz_blog"
    AHREFS_BLOG = "ahrefs_blog"
    SEMRUSH_BLOG = "semrush_blog"
    BACKLINKO = "backlinko"
    INDUSTRY_CASE_STUDY = "industry_case_study"
    EXPERIMENT = "experiment"
    ACADEMIC_RESEARCH = "academic_research"
    USER_REPORT = "user_report"


@dataclass
class ResearchIntake:
    """Structured research intake for SEO knowledge acquisition."""
    research_id: str
    source: ResearchSource
    title: str
    content: str
    source_url: Optional[str] = None
    extracted_concepts: List[str] = field(default_factory=list)
    extracted_claims: List[str] = field(default_factory=list)
    confidence: float = 0.5
    proposed_maturity: KnowledgeMaturity = KnowledgeMaturity.DEFINITION
    metadata: Dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.utcnow)


class ResearchSourceProcessor(ABC):
    """Contract for processing research sources into CandidateKnowledge."""

    @abstractmethod
    def process(self, intake: ResearchIntake) -> List[CandidateKnowledge]:
        """
        Process research intake into CandidateKnowledge objects.

        This method:
        1. Extracts concepts from the research
        2. Creates evidence for each concept
        3. Generates CandidateKnowledge with proper structure
        4. Never directly inserts knowledge - only produces candidates
        """
        pass


class GoogleDocumentationProcessor(ResearchSourceProcessor):
    """Processor for Google official documentation."""

    def process(self, intake: ResearchIntake) -> List[CandidateKnowledge]:
        """Process Google documentation into candidate knowledge."""
        candidates = []

        # Extract concepts from the documentation
        for concept_name in intake.extracted_concepts:
            # Create evidence from the source
            evidence = Evidence(
                id=f"evidence_{intake.research_id}_{concept_name}",
                source=intake.source_url or "google_documentation",
                source_type=SourceType.RESEARCH,
                claim=f"{concept_name}: {intake.content[:200]}...",
                retrieved_at=intake.collected_at,
                quality_score=0.9,  # High trust for official docs
                confidence=intake.confidence,
                freshness=KnowledgeFreshness.FRESH,
                metadata={
                    "research_id": intake.research_id,
                    "source_type": intake.source.value,
                    "title": intake.title,
                },
            )

            # Create candidate knowledge
            candidate = CandidateKnowledge(
                id=f"candidate_{intake.research_id}_{concept_name}",
                name=concept_name,
                definition=self._extract_definition(intake.content, concept_name),
                evidence=[evidence],
                proposed_maturity=intake.proposed_maturity,
                proposed_confidence=intake.confidence,
                source=intake.source.value,
                submitted_at=intake.collected_at,
                metadata={
                    "research_id": intake.research_id,
                    "source_url": intake.source_url,
                    "processor": "GoogleDocumentationProcessor",
                },
            )

            candidates.append(candidate)

        return candidates

    def _extract_definition(self, content: str, concept_name: str) -> str:
        """Extract definition for a concept from content."""
        # Simple extraction - in production would use NLP
        lines = content.split('\n')
        for line in lines:
            if concept_name.lower() in line.lower() and len(line) > 20:
                return line.strip()
        return f"{concept_name} - extracted from documentation"


class SearchCentralProcessor(ResearchSourceProcessor):
    """Processor for Google Search Central content."""

    def process(self, intake: ResearchIntake) -> List[CandidateKnowledge]:
        """Process Search Central content into candidate knowledge."""
        candidates = []

        for concept_name in intake.extracted_concepts:
            evidence = Evidence(
                id=f"evidence_{intake.research_id}_{concept_name}",
                source=intake.source_url or "search_central",
                source_type=SourceType.RESEARCH,
                claim=f"{concept_name}: {intake.content[:200]}...",
                retrieved_at=intake.collected_at,
                quality_score=0.85,  # High trust for Search Central
                confidence=intake.confidence,
                freshness=KnowledgeFreshness.FRESH,
                metadata={
                    "research_id": intake.research_id,
                    "source_type": intake.source.value,
                    "title": intake.title,
                },
            )

            candidate = CandidateKnowledge(
                id=f"candidate_{intake.research_id}_{concept_name}",
                name=concept_name,
                definition=self._extract_definition(intake.content, concept_name),
                evidence=[evidence],
                proposed_maturity=intake.proposed_maturity,
                proposed_confidence=intake.confidence,
                source=intake.source.value,
                submitted_at=intake.collected_at,
                metadata={
                    "research_id": intake.research_id,
                    "source_url": intake.source_url,
                    "processor": "SearchCentralProcessor",
                },
            )

            candidates.append(candidate)

        return candidates

    def _extract_definition(self, content: str, concept_name: str) -> str:
        """Extract definition for a concept from content."""
        lines = content.split('\n')
        for line in lines:
            if concept_name.lower() in line.lower() and len(line) > 20:
                return line.strip()
        return f"{concept_name} - extracted from Search Central"


class SEOResearchEngine:
    """
    Main research engine for SEO knowledge acquisition.

    Coordinates research intake and processing to produce CandidateKnowledge
    that can be submitted to Knowledge Governance.
    """

    def __init__(self) -> None:
        self._processors: Dict[ResearchSource, ResearchSourceProcessor] = {
            ResearchSource.GOOGLE_DOCUMENTATION: GoogleDocumentationProcessor(),
            ResearchSource.SEARCH_CENTRAL: SearchCentralProcessor(),
            ResearchSource.SEARCH_QUALITY_GUIDELINES: SearchCentralProcessor(),
            ResearchSource.CORE_WEB_VITALS: GoogleDocumentationProcessor(),
            ResearchSource.STRUCTURED_DATA: GoogleDocumentationProcessor(),
            ResearchSource.SEARCH_CONSOLE: GoogleDocumentationProcessor(),
            ResearchSource.INDUSTRY_CASE_STUDY: GoogleDocumentationProcessor(),
            ResearchSource.EXPERIMENT: GoogleDocumentationProcessor(),
        }
        self._research_history: List[ResearchIntake] = []

    def register_processor(self, source: ResearchSource, processor: ResearchSourceProcessor) -> None:
        """Register a custom processor for a research source."""
        self._processors[source] = processor

    def ingest_research(self, intake: ResearchIntake) -> List[CandidateKnowledge]:
        """
        Ingest research and produce CandidateKnowledge.

        This is the entry point for research intake. It:
        1. Validates the intake
        2. Selects appropriate processor
        3. Processes into candidates
        4. Records history
        5. Returns candidates for Governance submission

        Never directly inserts knowledge - only produces candidates.
        """
        # Validate intake
        if not self._validate_intake(intake):
            return []

        # Select processor
        processor = self._processors.get(intake.source)
        if not processor:
            # Default processor for unknown sources
            processor = GoogleDocumentationProcessor()

        # Process into candidates
        candidates = processor.process(intake)

        # Record history
        self._research_history.append(intake)

        return candidates

    def _validate_intake(self, intake: ResearchIntake) -> bool:
        """Validate research intake before processing."""
        if not intake.content or len(intake.content) < 50:
            return False
        if not intake.extracted_concepts:
            return False
        if intake.confidence < 0.0 or intake.confidence > 1.0:
            return False
        return True

    def get_research_history(self) -> List[ResearchIntake]:
        """Get history of research intakes."""
        return self._research_history.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about research activity."""
        if not self._research_history:
            return {
                "total_intakes": 0,
                "by_source": {},
                "avg_confidence": 0.0,
            }

        source_counts: Dict[str, int] = {}
        total_confidence = 0.0

        for intake in self._research_history:
            source_counts[intake.source.value] = source_counts.get(intake.source.value, 0) + 1
            total_confidence += intake.confidence

        return {
            "total_intakes": len(self._research_history),
            "by_source": source_counts,
            "avg_confidence": total_confidence / len(self._research_history),
        }


class SEOResearchOrchestrator:
    """
    Orchestrates the complete research pipeline.

    Provides high-level interface for SEO research operations.
    """

    def __init__(self) -> None:
        self._engine = SEOResearchEngine()

    def research_from_google_docs(
        self,
        url: str,
        title: str,
        content: str,
        concepts: List[str],
        confidence: float = 0.9,
    ) -> List[CandidateKnowledge]:
        """
        Research from Google documentation.

        High-trust source with automatic high confidence.
        """
        intake = ResearchIntake(
            research_id=f"google_{datetime.utcnow().timestamp()}",
            source=ResearchSource.GOOGLE_DOCUMENTATION,
            source_url=url,
            title=title,
            content=content,
            extracted_concepts=concepts,
            confidence=confidence,
            proposed_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        )
        return self._engine.ingest_research(intake)

    def research_from_search_central(
        self,
        url: str,
        title: str,
        content: str,
        concepts: List[str],
        confidence: float = 0.85,
    ) -> List[CandidateKnowledge]:
        """
        Research from Search Central.

        High-trust source for SEO best practices.
        """
        intake = ResearchIntake(
            research_id=f"search_central_{datetime.utcnow().timestamp()}",
            source=ResearchSource.SEARCH_CENTRAL,
            source_url=url,
            title=title,
            content=content,
            extracted_concepts=concepts,
            confidence=confidence,
            proposed_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        )
        return self._engine.ingest_research(intake)

    def research_from_case_study(
        self,
        url: str,
        title: str,
        content: str,
        concepts: List[str],
        confidence: float = 0.7,
    ) -> List[CandidateKnowledge]:
        """
        Research from industry case study.

        Medium-trust source requiring validation.
        """
        intake = ResearchIntake(
            research_id=f"case_study_{datetime.utcnow().timestamp()}",
            source=ResearchSource.INDUSTRY_CASE_STUDY,
            source_url=url,
            title=title,
            content=content,
            extracted_concepts=concepts,
            confidence=confidence,
            proposed_maturity=KnowledgeMaturity.DEFINITION,
        )
        return self._engine.ingest_research(intake)

    def research_from_experiment(
        self,
        title: str,
        content: str,
        concepts: List[str],
        confidence: float = 0.6,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[CandidateKnowledge]:
        """
        Research from controlled experiment.

        Variable-trust source depending on experiment quality.
        """
        intake = ResearchIntake(
            research_id=f"experiment_{datetime.utcnow().timestamp()}",
            source=ResearchSource.EXPERIMENT,
            title=title,
            content=content,
            extracted_concepts=concepts,
            confidence=confidence,
            proposed_maturity=KnowledgeMaturity.DEFINITION,
            metadata=metadata or {},
        )
        return self._engine.ingest_research(intake)

    def get_research_statistics(self) -> Dict[str, Any]:
        """Get research statistics."""
        return self._engine.get_statistics()
