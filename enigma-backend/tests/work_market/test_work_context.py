from app.work_market.models import WorkContext, WorkType


def test_work_context_distinguishes_types():
    """WorkContext should distinguish between different work types."""
    internal_context = WorkContext(
        work_type=WorkType.INTERNAL,
        goal="Build Enigma brand",
    )

    freelance_context = WorkContext(
        work_type=WorkType.FREELANCE,
        goal="Complete SEO audit for client",
        client="Test Client",
    )

    assert internal_context.work_type == WorkType.INTERNAL
    assert freelance_context.work_type == WorkType.FREELANCE
    assert freelance_context.client == "Test Client"


def test_work_context_serializes():
    """WorkContext should serialize to dict."""
    from datetime import datetime

    context = WorkContext(
        work_type=WorkType.FREELANCE,
        client="Test Client",
        profession="SEO Specialist",
        task="SEO Audit",
        goal="Complete SEO audit",
        budget=500.0,
        deadline=datetime(2024, 2, 1),
    )

    context_dict = context.to_dict()

    assert context_dict["work_type"] == "freelance"
    assert context_dict["client"] == "Test Client"
    assert context_dict["profession"] == "SEO Specialist"
    assert context_dict["budget"] == 500.0
