"""
Tests for SEO Evidence module.

Tests evidence validation, scoring, and aggregation.
"""

import pytest
from datetime import datetime, timedelta

from app.expert_domains.domains.seo_evidence import (
    EvidenceCategory,
    EvidenceQuality,
    SEOEvidenceScorer,
    SEOEvidenceValidator,
    SEOEvidenceAggregator,
    SEOEvidenceValidation,
)
from app.knowledge_governance.models import (
    Evidence,
    SourceType,
    KnowledgeFreshness,
)


class TestSEOEvidenceScorer:
    """Test SEO evidence scoring."""

    def test_score_google_documentation(self):
        """Test scoring Google documentation evidence."""
        scorer = SEOEvidenceScorer()
        
        evidence = Evidence(
            id="evidence_001",
            source="https://developers.google.com/search/docs",
            source_type=SourceType.RESEARCH,
            claim="Google documentation about SEO best practices",
            retrieved_at=datetime.utcnow(),
            quality_score=0.9,
            confidence=0.9,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        score = scorer.score(evidence)
        
        assert score.total_score > 0.6  # Good score for Google docs
        assert score.source_quality > 0.8
        assert score.freshness > 0.8

    def test_score_stale_evidence(self):
        """Test scoring stale evidence."""
        scorer = SEOEvidenceScorer()
        
        old_date = datetime.utcnow() - timedelta(days=400)
        evidence = Evidence(
            id="evidence_002",
            source="old_source",
            source_type=SourceType.RESEARCH,
            claim="Old claim",
            retrieved_at=old_date,
            quality_score=0.5,
            confidence=0.5,
            freshness=KnowledgeFreshness.STALE,
        )
        
        score = scorer.score(evidence)
        
        assert score.freshness < 0.5  # Low freshness score

    def test_score_with_corroboration(self):
        """Test scoring with corroboration context."""
        scorer = SEOEvidenceScorer()
        
        evidence = Evidence(
            id="evidence_003",
            source="source",
            source_type=SourceType.RESEARCH,
            claim="Claim with corroboration",
            retrieved_at=datetime.utcnow(),
            quality_score=0.7,
            confidence=0.7,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        context = {"corroborating_sources": 3}
        score = scorer.score(evidence, context)
        
        assert score.corroboration > 0.8  # High corroboration

    def test_score_breakdown(self):
        """Test score breakdown components."""
        scorer = SEOEvidenceScorer()
        
        evidence = Evidence(
            id="evidence_004",
            source="source",
            source_type=SourceType.RESEARCH,
            claim="A" * 600,  # Long claim for specificity
            retrieved_at=datetime.utcnow(),
            quality_score=0.8,
            confidence=0.8,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        score = scorer.score(evidence)
        
        assert "source_quality" in score.breakdown
        assert "freshness" in score.breakdown
        assert "corroboration" in score.breakdown
        assert "specificity" in score.breakdown
        assert "validation" in score.breakdown
        assert "weights" in score.breakdown


class TestSEOEvidenceValidator:
    """Test SEO evidence validation."""

    def test_validate_high_quality_evidence(self):
        """Test validating high-quality evidence."""
        validator = SEOEvidenceValidator()
        
        evidence = Evidence(
            id="evidence_005",
            source="https://developers.google.com/search/docs",
            source_type=SourceType.RESEARCH,
            claim="Comprehensive claim about SEO with detailed explanation",
            retrieved_at=datetime.utcnow(),
            quality_score=0.9,
            confidence=0.9,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        validation = validator.validate(evidence)
        
        assert validation.is_valid is True
        assert validation.quality in [EvidenceQuality.CRITICAL, EvidenceQuality.HIGH, EvidenceQuality.MEDIUM]
        assert validation.confidence > 0.5
        assert len(validation.validation_reasons) > 0

    def test_validate_low_quality_evidence(self):
        """Test validating low-quality evidence."""
        validator = SEOEvidenceValidator()
        
        evidence = Evidence(
            id="evidence_006",
            source="unreliable_source",
            source_type=SourceType.USER_INPUT,
            claim="Short claim",
            retrieved_at=datetime.utcnow() - timedelta(days=400),
            quality_score=0.3,
            confidence=0.3,
            freshness=KnowledgeFreshness.STALE,
        )
        
        validation = validator.validate(evidence)
        
        assert validation.quality in [EvidenceQuality.LOW, EvidenceQuality.UNRELIABLE]
        assert validation.confidence < 0.5

    def test_maturity_impact_calculation(self):
        """Test maturity impact calculation."""
        validator = SEOEvidenceValidator()
        
        evidence = Evidence(
            id="evidence_007",
            source="source",
            source_type=SourceType.RESEARCH,
            claim="Claim",
            retrieved_at=datetime.utcnow(),
            quality_score=0.8,
            confidence=0.8,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        validation = validator.validate(evidence)
        
        # Maturity impact should be between -1.0 and 1.0
        assert -1.0 <= validation.maturity_impact <= 1.0

    def test_validation_reasons_generation(self):
        """Test validation reasons generation."""
        validator = SEOEvidenceValidator()
        
        evidence = Evidence(
            id="evidence_008",
            source="https://developers.google.com/search/docs",
            source_type=SourceType.RESEARCH,
            claim="Claim",
            retrieved_at=datetime.utcnow(),
            quality_score=0.9,
            confidence=0.9,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        validation = validator.validate(evidence)
        
        assert len(validation.validation_reasons) > 0
        assert any("source" in reason.lower() for reason in validation.validation_reasons)


class TestSEOEvidenceAggregator:
    """Test SEO evidence aggregation."""

    def test_aggregate_single_evidence(self):
        """Test aggregating single evidence."""
        aggregator = SEOEvidenceAggregator()
        
        evidence = Evidence(
            id="evidence_009",
            source="source",
            source_type=SourceType.RESEARCH,
            claim="Claim",
            retrieved_at=datetime.utcnow(),
            quality_score=0.8,
            confidence=0.8,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        result = aggregator.aggregate_evidence([evidence])
        
        assert result["evidence_count"] == 1
        assert result["combined_score"] > 0
        assert result["best_evidence"] is not None

    def test_aggregate_multiple_evidence(self):
        """Test aggregating multiple evidence."""
        aggregator = SEOEvidenceAggregator()
        
        evidence_list = [
            Evidence(
                id=f"evidence_{i}",
                source=f"source_{i}",
                source_type=SourceType.RESEARCH,
                claim=f"Claim {i}",
                retrieved_at=datetime.utcnow(),
                quality_score=0.7 + (i * 0.05),
                confidence=0.7 + (i * 0.05),
                freshness=KnowledgeFreshness.FRESH,
            )
            for i in range(5)
        ]
        
        result = aggregator.aggregate_evidence(evidence_list)
        
        assert result["evidence_count"] == 5
        assert result["combined_score"] > 0
        assert len(result["individual_validations"]) == 5

    def test_aggregate_empty_evidence(self):
        """Test aggregating empty evidence list."""
        aggregator = SEOEvidenceAggregator()
        
        result = aggregator.aggregate_evidence([])
        
        assert result["evidence_count"] == 0
        assert result["combined_score"] == 0.0
        assert result["best_evidence"] is None
        assert result["validation_summary"] == "No evidence"

    def test_aggregation_corroboration_effect(self):
        """Test that corroboration improves aggregation."""
        aggregator = SEOEvidenceAggregator()
        
        evidence_list = [
            Evidence(
                id=f"evidence_{i}",
                source=f"source_{i}",
                source_type=SourceType.RESEARCH,
                claim="Similar claim",
                retrieved_at=datetime.utcnow(),
                quality_score=0.7,
                confidence=0.7,
                freshness=KnowledgeFreshness.FRESH,
            )
            for i in range(3)
        ]
        
        result = aggregator.aggregate_evidence(evidence_list)
        
        # With corroboration, individual validations should have higher scores
        for validation in result["individual_validations"]:
            # Corroboration context should be applied
            assert validation.confidence > 0


class TestEvidencePipeline:
    """Test complete evidence pipeline."""

    def test_evidence_to_readiness_impact(self):
        """Test pipeline from evidence to readiness impact."""
        validator = SEOEvidenceValidator()
        
        # Create high-quality evidence
        evidence = Evidence(
            id="evidence_010",
            source="https://developers.google.com/search/docs",
            source_type=SourceType.RESEARCH,
            claim="Important SEO insight",
            retrieved_at=datetime.utcnow(),
            quality_score=0.9,
            confidence=0.9,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        # Validate
        validation = validator.validate(evidence)
        
        # Check that high-quality evidence has positive impact
        assert validation.maturity_impact > 0
        assert validation.source_quality > 0.8

    def test_multiple_sources_aggregation(self):
        """Test aggregating evidence from multiple sources."""
        aggregator = SEOEvidenceAggregator()
        
        evidence_list = [
            Evidence(
                id="evidence_011",
                source="google_docs",
                source_type=SourceType.RESEARCH,
                claim="SEO best practice",
                retrieved_at=datetime.utcnow(),
                quality_score=0.9,
                confidence=0.9,
                freshness=KnowledgeFreshness.FRESH,
            ),
            Evidence(
                id="evidence_012",
                source="moz_blog",
                source_type=SourceType.RESEARCH,
                claim="SEO best practice",
                retrieved_at=datetime.utcnow(),
                quality_score=0.85,
                confidence=0.85,
                freshness=KnowledgeFreshness.FRESH,
            ),
            Evidence(
                id="evidence_013",
                source="ahrefs_blog",
                source_type=SourceType.RESEARCH,
                claim="SEO best practice",
                retrieved_at=datetime.utcnow(),
                quality_score=0.8,
                confidence=0.8,
                freshness=KnowledgeFreshness.FRESH,
            ),
        ]
        
        result = aggregator.aggregate_evidence(evidence_list)
        
        # Multiple sources should improve overall score
        assert result["combined_score"] > 0.7
        assert result["validation_summary"].startswith("3/3")
