import pytest

from app.academy.academy_models import AcademyModule, KnowledgeArticle
from app.academy.academy_validator import AcademyValidator


def test_validator_rejects_missing_metadata():
    module = AcademyModule(
        id="",
        name="",
        version="",
        description="",
        topics=[],
        capabilities=[],
        confidence=1.1,
    )

    result = AcademyValidator.validate_module(module)

    assert not result.is_valid()
    assert "Module id is required." in result.errors
    assert "Module name is required." in result.errors
    assert "Module version is required." in result.errors
    assert "Module description is required." in result.errors
    assert "Module confidence must be between 0 and 1." in result.errors


def test_validator_detects_duplicate_topics():
    module = AcademyModule(
        id="mod-2",
        name="Test Academy",
        version="1.0.0",
        description="Description",
        topics=["Topic", "topic"],
        capabilities=["capability"],
        confidence=0.5,
    )

    result = AcademyValidator.validate_module(module)

    assert not result.is_valid()
    assert "Duplicate topic found: topic" in result.errors


def test_validator_detects_empty_article():
    module = AcademyModule(
        id="mod-3",
        name="Test Academy",
        version="1.0.0",
        description="Description",
        topics=["Topic"],
        capabilities=["capability"],
        confidence=0.5,
    )
    module.add_article(KnowledgeArticle(
        id="article-1",
        module=module.name,
        title="",
        content="",
        summary="",
        keywords=["Topic"],
        references=[],
        evidence=[],
        confidence=0.5,
    ))

    result = AcademyValidator.validate_module(module)

    assert not result.is_valid()
    assert any("missing required fields" in error for error in result.errors)
