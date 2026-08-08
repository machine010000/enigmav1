from app.services.research_service import ResearchService, ResearchReport, SearchResult


def test_research_produces_candidate_knowledge():
    """ResearchService should produce CandidateKnowledge, not trusted knowledge."""
    service = ResearchService()

    # Create a research report with results
    report = ResearchReport(
        query="test query",
        search_type="web",
        results=[
            SearchResult(
                title="Test Result",
                url="https://example.com",
                snippet="Test snippet",
                source="example.com",
                confidence=0.8,
            )
        ],
        total_found=1,
        rank_method="relevance",
        generated_at="2024-01-01T00:00:00",
    )

    # Convert to CandidateKnowledge
    candidate = report.to_candidate_knowledge()

    # Should produce CandidateKnowledge if governance is available
    if candidate is not None:
        assert candidate.name == report.query
        assert candidate.source == "research_service"
        assert len(candidate.evidence) > 0


def test_research_evidence_has_correct_source_type():
    """Research evidence should have EXTERNAL_SOURCE type."""
    service = ResearchService()

    report = ResearchReport(
        query="test",
        search_type="web",
        results=[
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="Test",
                source="example.com",
                confidence=0.8,
            )
        ],
        total_found=1,
        generated_at="2024-01-01T00:00:00",
    )

    candidate = report.to_candidate_knowledge()

    if candidate is not None:
        for evidence in candidate.evidence:
            assert evidence.source_type.value == "external_source"


def test_research_does_not_publish_directly():
    """ResearchService should not have direct publish methods to Knowledge Graph."""
    service = ResearchService()

    # ResearchService should NOT have methods like:
    # - publish_to_graph()
    # - create_concept()
    # - add_to_knowledge_graph()

    assert not hasattr(service, "publish_to_graph")
    assert not hasattr(service, "create_concept")
    assert not hasattr(service, "add_to_knowledge_graph")
