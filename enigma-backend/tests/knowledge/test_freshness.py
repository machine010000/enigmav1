from app.knowledge_governance import (
    Evidence,
    KnowledgeFreshness,
    SourceType,
    DefaultEvidenceScorer,
)
from datetime import datetime, timedelta


def test_freshness_categories_are_defined():
    """Freshness should have all required categories."""
    categories = [
        KnowledgeFreshness.FRESH,
        KnowledgeFreshness.AGING,
        KnowledgeFreshness.STALE,
        KnowledgeFreshness.EXPIRED,
        KnowledgeFreshness.UNKNOWN,
    ]

    for category in categories:
        assert category.value in ["fresh", "aging", "stale", "expired", "unknown"]


def test_freshness_scorer_calculates_based_on_age():
    """Freshness scorer should calculate based on evidence age."""
    scorer = DefaultEvidenceScorer()

    # Fresh evidence (recent)
    fresh_evidence = Evidence(
        id="ev-1",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test claim",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=15),
    )

    score = scorer.score(fresh_evidence)
    assert score.freshness >= 0.8  # Should be fresh

    # Stale evidence (old)
    stale_evidence = Evidence(
        id="ev-2",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test claim",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=400),
    )

    score = scorer.score(stale_evidence)
    assert score.freshness <= 0.4  # Should be stale


def test_freshness_without_published_date():
    """Evidence without published date should get neutral freshness."""
    scorer = DefaultEvidenceScorer()

    evidence = Evidence(
        id="ev-1",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test claim",
        retrieved_at=datetime.utcnow(),
        published_at=None,  # No published date
    )

    score = scorer.score(evidence)
    assert score.freshness == 0.5  # Neutral score


def test_freshness_affects_total_score():
    """Freshness should contribute to total evidence score."""
    scorer = DefaultEvidenceScorer()

    # Fresh evidence
    fresh_evidence = Evidence(
        id="ev-1",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test claim",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=10),
    )

    fresh_score = scorer.score(fresh_evidence)

    # Stale evidence
    stale_evidence = Evidence(
        id="ev-2",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test claim",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=500),
    )

    stale_score = scorer.score(stale_evidence)

    # Fresh evidence should have higher total score
    assert fresh_score.total_score > stale_score.total_score


def test_freshness_thresholds():
    """Test freshness thresholds are appropriate."""
    scorer = DefaultEvidenceScorer()

    # Very fresh (≤ 30 days)
    very_fresh = Evidence(
        id="ev-1",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=20),
    )
    assert scorer.score(very_fresh).freshness == 1.0

    # Fresh (≤ 90 days)
    fresh = Evidence(
        id="ev-2",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=60),
    )
    assert scorer.score(fresh).freshness == 0.8

    # Acceptable (≤ 180 days)
    acceptable = Evidence(
        id="ev-3",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=120),
    )
    assert scorer.score(acceptable).freshness == 0.6

    # Aging (≤ 365 days)
    aging = Evidence(
        id="ev-4",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=300),
    )
    assert scorer.score(aging).freshness == 0.4

    # Stale (≤ 730 days)
    stale = Evidence(
        id="ev-5",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=500),
    )
    assert scorer.score(stale).freshness == 0.2

    # Expired (> 730 days)
    expired = Evidence(
        id="ev-6",
        source="Test",
        source_type=SourceType.RESEARCH,
        claim="Test",
        retrieved_at=datetime.utcnow(),
        published_at=datetime.utcnow() - timedelta(days=800),
    )
    assert scorer.score(expired).freshness == 0.1
