from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.academy.academy_loader import AcademyLoader
from app.academy.academy_models import AcademyModule, KnowledgeArticle
from app.academy.academy_registry import AcademyRegistry
from app.academy.academy_validator import AcademyValidator, ValidationResult

try:
    from app.knowledge_governance import CandidateKnowledge, Evidence, SourceType
    KNOWLEDGE_GOVERNANCE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GOVERNANCE_AVAILABLE = False


class AcademyManager:
    def __init__(self, registry: Optional[AcademyRegistry] = None) -> None:
        self.registry = registry or AcademyRegistry()
        self.loader = AcademyLoader(self.registry)
        self._cache: Dict[str, AcademyModule] = {}

    def load_providers(self, providers: List[object]) -> None:
        self.loader.load(providers)
        self._refresh_cache()

    def refresh(self, module_name: str) -> Optional[AcademyModule]:
        module = self.registry.get(module_name)
        if module:
            self._cache[module.name.lower()] = module
        return module

    def get_context(self, topic: str, subtopic: Optional[str] = None) -> Dict[str, object]:
        matching = self.registry.search_topics(topic)
        if subtopic:
            subterm = subtopic.lower()
            matching = [m for m in matching if any(subterm in kw.lower() for article in m.articles for kw in article.keywords)]

        return {
            "topic": topic,
            "subtopic": subtopic,
            "modules": [module.to_dict() for module in matching],
        }

    def validate_module(self, module: AcademyModule) -> ValidationResult:
        return AcademyValidator.validate_module(module)

    def list_modules(self) -> List[AcademyModule]:
        return self.registry.list_modules()

    def get_module(self, module_name: str) -> Optional[AcademyModule]:
        return self.registry.get(module_name)

    def _refresh_cache(self) -> None:
        self._cache = {module.name.lower(): module for module in self.registry.list_modules()}

    def module_to_candidate_knowledge(self, module: AcademyModule) -> Optional[Any]:
        """Convert Academy module to CandidateKnowledge for governance."""
        if not KNOWLEDGE_GOVERNANCE_AVAILABLE:
            return None

        # Convert articles to Evidence
        evidence_list = []
        for article in module.articles:
            evidence = Evidence(
                id=f"academy-{module.name}-{article.id}",
                source=module.name,
                source_type=SourceType.ACADEMY,
                claim=article.content,
                retrieved_at=datetime.utcnow(),
                quality_score=0.85,  # Academy sources are generally high quality
                confidence=article.confidence if article.confidence > 0 else 0.8,
            )
            evidence_list.append(evidence)

        # Create CandidateKnowledge from the module
        return CandidateKnowledge(
            id=f"academy-{module.id}",
            name=module.name,
            definition=f"Academy module: {module.description}",
            evidence=evidence_list,
            source="academy",
            submitted_at=datetime.utcnow(),
        )


class AcademyEngine:
    def __init__(self, manager: Optional[AcademyManager] = None) -> None:
        self.manager = manager or AcademyManager()

    def get_module_context(self, topic: str, subtopic: Optional[str] = None) -> Dict[str, object]:
        return self.manager.get_context(topic, subtopic)
