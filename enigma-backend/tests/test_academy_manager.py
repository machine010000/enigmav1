import pytest

from app.academy.academy_manager import AcademyManager
from app.academy.academy_models import AcademyModule, KnowledgeArticle
from app.academy.academy_registry import AcademyRegistry


class FakeProvider:
    def load(self):
        module = AcademyModule(
            id="fake_module",
            name="Fake Academy",
            version="1.0.0",
            description="Fake provider module.",
            topics=["Fake Topic"],
            capabilities=["fake_capability"],
            confidence=0.7,
        )
        module.add_article(KnowledgeArticle(
            id="fake_article",
            module=module.name,
            title="Fake Article",
            content="Fake content.",
            summary="Fake summary.",
            keywords=["Fake Topic"],
            references=[],
            evidence=[],
            confidence=0.7,
        ))
        return module


def test_academy_manager_loads_providers_and_caches():
    registry = AcademyRegistry()
    manager = AcademyManager(registry)
    manager.load_providers([FakeProvider()])

    module = manager.get_module("Fake Academy")
    assert module is not None
    assert module.name == "Fake Academy"
    assert manager.list_modules() == [module]


def test_academy_manager_get_context_by_topic():
    registry = AcademyRegistry()
    manager = AcademyManager(registry)
    manager.load_providers([FakeProvider()])

    context = manager.get_context("Fake Topic")
    assert context["topic"] == "Fake Topic"
    assert len(context["modules"]) == 1
    assert context["modules"][0]["name"] == "Fake Academy"


def test_academy_manager_refresh_returns_module():
    registry = AcademyRegistry()
    manager = AcademyManager(registry)
    manager.load_providers([FakeProvider()])

    module = manager.refresh("Fake Academy")
    assert module is not None
    assert module.name == "Fake Academy"


def test_academy_manager_search_subtopic_filters():
    registry = AcademyRegistry()
    manager = AcademyManager(registry)
    manager.load_providers([FakeProvider()])

    context = manager.get_context("Fake Topic", subtopic="Fake Topic")
    assert len(context["modules"]) == 1
