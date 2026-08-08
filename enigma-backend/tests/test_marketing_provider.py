from app.academy.providers.marketing import MarketingAcademyProvider


def test_marketing_provider_metadata_and_health():
    provider = MarketingAcademyProvider()
    metadata = provider.metadata()

    assert metadata["name"] == "Marketing Academy"
    assert metadata["version"] == "1.0.0"
    assert "Buyer Psychology" in metadata["topics"]
    assert provider.health() == "healthy"
    assert provider.version() == "1.0.0"


def test_marketing_provider_loads_module():
    provider = MarketingAcademyProvider()
    module = provider.load()

    assert module.name == "Marketing Academy"
    assert module.version == "1.0.0"
    assert module.articles
    assert module.articles[0].module == module.name
    assert module.articles[0].has_content()
