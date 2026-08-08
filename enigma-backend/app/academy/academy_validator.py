from __future__ import annotations

from typing import Dict, List

from app.academy.academy_models import AcademyModule, KnowledgeArticle


class ValidationResult:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, List[str]]:
        return {"errors": self.errors, "warnings": self.warnings}


class AcademyValidator:
    @staticmethod
    def validate_module(module: AcademyModule) -> ValidationResult:
        result = ValidationResult()

        if not module.id:
            result.add_error("Module id is required.")
        if not module.name:
            result.add_error("Module name is required.")
        if not module.version:
            result.add_error("Module version is required.")
        if not module.description:
            result.add_error("Module description is required.")
        if module.confidence < 0 or module.confidence > 1:
            result.add_error("Module confidence must be between 0 and 1.")
        if not module.topics:
            result.add_warning("Module should expose at least one topic.")

        topic_set = set()
        for topic in module.topics:
            lower = topic.lower()
            if lower in topic_set:
                result.add_error(f"Duplicate topic found: {topic}")
            topic_set.add(lower)

        article_ids = set()
        for article in module.articles:
            if not article.is_valid():
                result.add_error(f"Article '{article.id or article.title}' is missing required fields.")
            if article.confidence < 0 or article.confidence > 1:
                result.add_error(f"Article '{article.id}' has invalid confidence value.")
            if article.id in article_ids:
                result.add_error(f"Duplicate article id found: {article.id}")
            article_ids.add(article.id)
            if not article.has_content():
                result.add_error(f"Article '{article.id}' is empty.")

        return result
