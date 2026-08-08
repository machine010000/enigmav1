import pytest

from app.academy.academy_manager import AcademyManager
from app.academy.providers.marketing import MarketingAcademyProvider


def test_academy_manager_only_returns_context_from_manager():
    manager = AcademyManager()
    manager.load_providers([MarketingAcademyProvider()])

    context = manager.get_context("Marketing", subtopic="Audience Segmentation")
    assert context["topic"] == "Marketing"
    assert context["subtopic"] == "Audience Segmentation"
    assert len(context["modules"]) > 0
    assert all("Marketing Academy" == module["name"] for module in context["modules"])
