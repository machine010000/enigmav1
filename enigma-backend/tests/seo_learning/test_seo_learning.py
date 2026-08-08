"""
Tests for SEO Learning module.

Tests knowledge governance integration and versioning.
"""

import pytest
from datetime import datetime

from app.expert_domains.domains.seo_learning import (
    KnowledgeUpdateType,
    KnowledgeUpdateResult,
    SEOKnowledgeGovernanceBridge,
    SEOKnowledgeVersionTracker,
    SEOKnowledgeManager,
)
from app.knowledge_governance.models import (
    CandidateKnowledge,
    Evidence,
    SourceType,
    KnowledgeMaturity,
    KnowledgeFreshness,
    ConceptVersion,
)


class TestSEOKnowledgeGovernanceBridge:
    """Test SEO knowledge governance bridge."""

    def test_submit_candidate_without_governance(self):
        """Test submitting candidate without governance service."""
        bridge = SEOKnowledgeGovernanceBridge()
        
        candidate = CandidateKnowledge(
            id="candidate_001",
            name="test_concept",
            definition="Test definition",
            evidence=[],
            proposed_maturity=KnowledgeMaturity.DEFINITION,
            proposed_confidence=0.8,
            source="test",
        )
        
        result = bridge.submit_candidate(candidate)
        
        assert result.success is False
        assert "Governance service not available" in result.reason

    def test_submit_candidate_with_governance(self):
        """Test submitting candidate with governance service."""
        # Mock governance service
        class MockGovernanceService:
            def submit_candidate(self, candidate, actor):
                from app.knowledge_governance.models import GovernedKnowledge, Concept
                governed = GovernedKnowledge(
                    concept=Concept(
                        id=candidate.id,
                        name=candidate.name,
                        definition=candidate.definition,
                        knowledge_maturity=candidate.proposed_maturity,
                        knowledge_confidence=candidate.proposed_confidence,
                    ),
                    versions=[],
                    conflicts=[],
                    relationships=[],
                    governance_events=[],
                )
                return governed
        
        bridge = SEOKnowledgeGovernanceBridge()
        bridge.set_governance_service(MockGovernanceService())
        
        candidate = CandidateKnowledge(
            id="candidate_002",
            name="test_concept",
            definition="Test definition",
            evidence=[],
            proposed_maturity=KnowledgeMaturity.DEFINITION,
            proposed_confidence=0.8,
            source="test",
        )
        
        result = bridge.submit_candidate(candidate)
        
        assert result.success is True
        assert result.concept_id == "candidate_002"
        assert result.new_maturity == KnowledgeMaturity.DEFINITION

    def test_deprecate_concept(self):
        """Test deprecating a concept."""
        bridge = SEOKnowledgeGovernanceBridge()
        
        result = bridge.deprecate_concept(
            concept_id="test_concept",
            reason="Outdated best practice",
        )
        
        assert result.success is False  # No governance service
        assert "Governance service not available" in result.reason

    def test_get_update_history(self):
        """Test getting update history."""
        bridge = SEOKnowledgeGovernanceBridge()
        
        history = bridge.get_update_history()
        
        assert isinstance(history, list)

    def test_get_update_statistics(self):
        """Test getting update statistics."""
        bridge = SEOKnowledgeGovernanceBridge()
        
        stats = bridge.get_update_statistics()
        
        assert "total_updates" in stats
        assert "successful_updates" in stats
        assert "failed_updates" in stats
        assert "by_type" in stats


class TestSEOKnowledgeVersionTracker:
    """Test SEO knowledge version tracking."""

    def test_track_concept_version(self):
        """Test tracking concept versions."""
        tracker = SEOKnowledgeVersionTracker()
        
        version = ConceptVersion(
            version=1,
            concept_id="test_concept",
            definition="Initial definition",
            evidence_ids=[],
            reason="Initial version",
            confidence=0.8,
            maturity=KnowledgeMaturity.DEFINITION,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        tracker.track_concept_version("test_concept", version)
        
        history = tracker.get_concept_history("test_concept")
        
        assert len(history) == 1
        assert history[0].version == 1

    def test_track_best_practice_version(self):
        """Test tracking best practice versions."""
        tracker = SEOKnowledgeVersionTracker()
        
        tracker.track_best_practice_version(
            practice_id="title_optimization",
            version=1,
            description="Include target keyword in title",
            reason="Initial best practice",
        )
        
        history = tracker.get_best_practice_history("title_optimization")
        
        assert len(history) == 1
        assert history[0]["version"] == 1
        assert "title" in history[0]["description"].lower()

    def test_track_template_version(self):
        """Test tracking execution template versions."""
        tracker = SEOKnowledgeVersionTracker()
        
        tracker.track_template_version(
            template_id="seo_audit_template",
            version=1,
            changes=["Added mobile optimization check"],
            reason="Updated for mobile-first indexing",
        )
        
        history = tracker.get_template_history("seo_audit_template")
        
        assert len(history) == 1
        assert history[0]["version"] == 1
        assert len(history[0]["changes"]) == 1

    def test_track_kpi_version(self):
        """Test tracking KPI threshold versions."""
        tracker = SEOKnowledgeVersionTracker()
        
        tracker.track_kpi_version(
            kpi_id="organic_traffic",
            version=1,
            old_threshold=None,
            new_threshold=10000.0,
            reason="Initial KPI threshold",
        )
        
        history = tracker.get_kpi_history("organic_traffic")
        
        assert len(history) == 1
        assert history[0]["new_threshold"] == 10000.0

    def test_version_summary(self):
        """Test version summary."""
        tracker = SEOKnowledgeVersionTracker()
        
        # Add some versions
        tracker.track_best_practice_version("practice1", 1, "desc", "reason")
        tracker.track_template_version("template1", 1, ["change"], "reason")
        tracker.track_kpi_version("kpi1", 1, None, 100.0, "reason")
        
        summary = tracker.get_version_summary()
        
        assert summary["best_practices_tracked"] == 1
        assert summary["templates_tracked"] == 1
        assert summary["kpis_tracked"] == 1
        assert summary["total_versions"] == 3


class TestSEOKnowledgeManager:
    """Test SEO knowledge manager."""

    def test_knowledge_manager_initialization(self):
        """Test knowledge manager initialization."""
        manager = SEOKnowledgeManager()
        
        assert manager._governance_bridge is not None
        assert manager._version_tracker is not None

    def test_submit_candidate(self):
        """Test submitting candidate through manager."""
        manager = SEOKnowledgeManager()
        
        candidate = CandidateKnowledge(
            id="candidate_003",
            name="test_concept",
            definition="Test definition",
            evidence=[],
            proposed_maturity=KnowledgeMaturity.DEFINITION,
            proposed_confidence=0.8,
            source="test",
        )
        
        result = manager.submit_candidate(candidate)
        
        # Should fail without governance service
        assert result.success is False

    def test_track_concept_version(self):
        """Test tracking concept version through manager."""
        manager = SEOKnowledgeManager()
        
        version = ConceptVersion(
            version=1,
            concept_id="test_concept",
            definition="Initial definition",
            evidence_ids=[],
            reason="Initial version",
            confidence=0.8,
            maturity=KnowledgeMaturity.DEFINITION,
            freshness=KnowledgeFreshness.FRESH,
        )
        
        manager.track_concept_version("test_concept", version)
        
        history = manager._version_tracker.get_concept_history("test_concept")
        assert len(history) == 1

    def test_track_best_practice_version(self):
        """Test tracking best practice version through manager."""
        manager = SEOKnowledgeManager()
        
        manager.track_best_practice_version(
            practice_id="practice1",
            version=1,
            description="Description",
            reason="Reason",
        )
        
        history = manager._version_tracker.get_best_practice_history("practice1")
        assert len(history) == 1

    def test_get_statistics(self):
        """Test getting comprehensive statistics."""
        manager = SEOKnowledgeManager()
        
        stats = manager.get_statistics()
        
        assert "update_statistics" in stats
        assert "version_summary" in stats


class TestKnowledgeUpdateTypes:
    """Test knowledge update type handling."""

    def test_new_concept_update(self):
        """Test new concept update type."""
        result = KnowledgeUpdateResult(
            success=True,
            update_type=KnowledgeUpdateType.NEW_CONCEPT,
            concept_id="new_concept",
            new_maturity=KnowledgeMaturity.DEFINITION,
            new_version=1,
            reason="New concept added",
        )
        
        assert result.update_type == KnowledgeUpdateType.NEW_CONCEPT
        assert result.new_version == 1

    def test_updated_concept_update(self):
        """Test updated concept update type."""
        result = KnowledgeUpdateResult(
            success=True,
            update_type=KnowledgeUpdateType.UPDATED_CONCEPT,
            concept_id="existing_concept",
            previous_maturity=KnowledgeMaturity.DEFINITION,
            new_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
            previous_version=1,
            new_version=2,
            reason="Concept updated with new evidence",
        )
        
        assert result.update_type == KnowledgeUpdateType.UPDATED_CONCEPT
        assert result.new_version == 2
        assert result.previous_version == 1

    def test_deprecated_concept_update(self):
        """Test deprecated concept update type."""
        result = KnowledgeUpdateResult(
            success=True,
            update_type=KnowledgeUpdateType.DEPRECATED_CONCEPT,
            concept_id="old_concept",
            previous_maturity=KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS,
            reason="Concept deprecated due to algorithm changes",
        )
        
        assert result.update_type == KnowledgeUpdateType.DEPRECATED_CONCEPT
        assert result.previous_maturity is not None
