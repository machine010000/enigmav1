"""
Test Knowledge Progress

Tests for knowledge domain progress tracking.
"""

import pytest
from datetime import datetime, timedelta

from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.contracts import (
    KnowledgeProgress,
    SkillLevel,
)


class TestKnowledgeProgressTracker:
    """Test KnowledgeProgressTracker."""
    
    def test_initialization(self):
        """Test tracker initialization."""
        tracker = KnowledgeProgressTracker()
        assert tracker is not None
        assert tracker._progress == {}
    
    def test_register_domain(self):
        """Test registering a knowledge domain."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.72,
            execution_score=0.48,
            evidence_score=0.35,
            confidence=0.61,
            readiness=0.52,
            last_verified=datetime.utcnow().isoformat(),
            freshness="fresh",
        )
        
        tracker.register_domain(progress)
        
        retrieved = tracker.get_progress("SEO")
        assert retrieved is not None
        assert retrieved.domain == "SEO"
        assert retrieved.knowledge_score == 0.72
    
    def test_get_progress_not_found(self):
        """Test getting progress for unregistered domain."""
        tracker = KnowledgeProgressTracker()
        
        retrieved = tracker.get_progress("Nonexistent")
        assert retrieved is None
    
    def test_update_progress(self):
        """Test updating knowledge progress."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.5,
            execution_score=0.3,
            evidence_score=0.2,
            confidence=0.4,
            readiness=0.35,
        )
        
        tracker.register_domain(progress)
        
        tracker.update_progress("SEO", knowledge_score=0.8)
        
        updated = tracker.get_progress("SEO")
        assert updated.knowledge_score == 0.8
        assert updated.last_verified is not None
    
    def test_calculate_readiness(self):
        """Test calculating overall readiness."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.8,
            execution_score=0.6,
            evidence_score=0.7,
            confidence=0.9,
            readiness=0.0,  # Will be calculated
        )
        
        tracker.register_domain(progress)
        
        readiness = tracker.calculate_readiness("SEO")
        
        assert 0.0 <= readiness <= 1.0
        assert readiness > 0.5  # Should be reasonably high
    
    def test_get_skill_level(self):
        """Test determining skill level."""
        tracker = KnowledgeProgressTracker()
        
        # High readiness
        progress_high = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.9,
            execution_score=0.9,
            evidence_score=0.9,
            confidence=0.9,
            readiness=0.85,
        )
        
        tracker.register_domain(progress_high)
        
        level = tracker.get_skill_level("SEO")
        assert level == SkillLevel.EXPERT
        
        # Low readiness
        progress_low = KnowledgeProgress(
            domain="Content Writing",
            knowledge_score=0.3,
            execution_score=0.2,
            evidence_score=0.1,
            confidence=0.3,
            readiness=0.25,
        )
        
        tracker.register_domain(progress_low)
        
        level_low = tracker.get_skill_level("Content Writing")
        assert level_low == SkillLevel.LEARNING
    
    def test_identify_gaps(self):
        """Test identifying knowledge gaps."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.3,
            execution_score=0.2,
            evidence_score=0.1,
            confidence=0.4,
            readiness=0.25,
            freshness="fresh",
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        assert len(gaps) > 0
        assert any("knowledge" in gap.lower() for gap in gaps)
        assert any("evidence" in gap.lower() for gap in gaps)
    
    def test_identify_gaps_no_gaps(self):
        """Test identifying gaps when there are none."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.9,
            execution_score=0.9,
            evidence_score=0.9,
            confidence=0.9,
            readiness=0.9,
            freshness="fresh",
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        # Should have no gaps
        assert len(gaps) == 0
    
    def test_identify_gaps_stale(self):
        """Test identifying stale knowledge as a gap."""
        tracker = KnowledgeProgressTracker()
        
        progress = KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.8,
            execution_score=0.8,
            evidence_score=0.8,
            confidence=0.8,
            readiness=0.8,
            freshness="stale",
        )
        
        tracker.register_domain(progress)
        
        gaps = tracker.identify_gaps("SEO")
        
        assert any("stale" in gap.lower() for gap in gaps)
    
    def test_get_all_domains(self):
        """Test getting all tracked domains."""
        tracker = KnowledgeProgressTracker()
        
        tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.5,
            execution_score=0.3,
            evidence_score=0.2,
            confidence=0.4,
            readiness=0.35,
        ))
        
        tracker.register_domain(KnowledgeProgress(
            domain="Content Writing",
            knowledge_score=0.6,
            execution_score=0.4,
            evidence_score=0.3,
            confidence=0.5,
            readiness=0.45,
        ))
        
        domains = tracker.get_all_domains()
        
        assert len(domains) == 2
        assert "SEO" in domains
        assert "Content Writing" in domains
    
    def test_get_stale_domains(self):
        """Test getting stale domains."""
        tracker = KnowledgeProgressTracker()
        
        # Fresh domain
        tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.5,
            execution_score=0.3,
            evidence_score=0.2,
            confidence=0.4,
            readiness=0.35,
            last_verified=datetime.utcnow().isoformat(),
            freshness="fresh",
        ))
        
        # Stale domain
        tracker.register_domain(KnowledgeProgress(
            domain="Old Domain",
            knowledge_score=0.5,
            execution_score=0.3,
            evidence_score=0.2,
            confidence=0.4,
            readiness=0.35,
            last_verified=(datetime.utcnow() - timedelta(hours=48)).isoformat(),
            freshness="stale",
        ))
        
        stale = tracker.get_stale_domains(max_age_hours=24)
        
        assert "Old Domain" in stale
        assert "SEO" not in stale
