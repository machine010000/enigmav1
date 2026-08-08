from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeArticle:
    id: str
    module: str
    title: str
    content: str
    summary: str
    keywords: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def is_valid(self) -> bool:
        return bool(self.id and self.title and self.content and self.summary)

    def has_content(self) -> bool:
        return bool(self.content.strip())


@dataclass
class AcademyModule:
    id: str
    name: str
    version: str
    description: str
    topics: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    source_count: int = 0
    confidence: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    articles: List[KnowledgeArticle] = field(default_factory=list)

    def add_article(self, article: KnowledgeArticle) -> None:
        self.articles.append(article)
        self.source_count = len(self.articles)

    def get_topic_articles(self, topic: str) -> List[KnowledgeArticle]:
        return [article for article in self.articles if topic.lower() in [k.lower() for k in article.keywords]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "topics": self.topics,
            "capabilities": self.capabilities,
            "source_count": self.source_count,
            "confidence": self.confidence,
            "last_updated": self.last_updated.isoformat(),
            "articles": [article.__dict__ for article in self.articles],
        }
