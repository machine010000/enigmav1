import pytest

from app.academy.academy_models import AcademyModule
from app.academy.academy_registry import AcademyRegistry


@pytest.fixture
def sample_module() -> AcademyModule:
    return AcademyModule(
        id="mod-1",
        name="Test Academy",
        version="1.0.0",
        description="Test module",
        topics=["Testing", "Documentation"],
        capabilities=["test"],
        confidence=0.9,
    )


def test_registry_register_and_get(sample_module):
    registry = AcademyRegistry()
    registry.register(sample_module)

    assert registry.get("Test Academy") == sample_module
    assert registry.get("test academy") == sample_module


def test_registry_unregister(sample_module):
    registry = AcademyRegistry()
    registry.register(sample_module)
    registry.unregister("Test Academy")

    assert registry.get("Test Academy") is None


def test_registry_list_modules(sample_module):
    registry = AcademyRegistry()
    registry.register(sample_module)

    assert registry.list_modules() == [sample_module]


def test_registry_search_topics(sample_module):
    registry = AcademyRegistry()
    registry.register(sample_module)

    matches = registry.search_topics("documentation")
    assert sample_module in matches
