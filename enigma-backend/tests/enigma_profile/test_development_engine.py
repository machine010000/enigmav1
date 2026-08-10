"""
Test Development Engine

Tests for development priority generation.
"""

import pytest
from datetime import datetime

from app.enigma_profile.development_engine import DevelopmentEngine
from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.contracts import (
    KnowledgeProgress,
    TrainingItem,
    PlatformReadiness,
    SkillLevel,
)
from app.marketplace.contracts import MarketplacePlatform


class TestDevelopmentEngine:
    """Test DevelopmentEngine."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = DevelopmentEngine()
        assert engine is not None
        assert engine._priorities == []
    
    def test_generate_priorities(self):
        """Test generating development priorities."""
        knowledge_tracker = KnowledgeProgressTracker()
        training_tracker = TrainingTracker()
        platform_intelligence = PlatformIntelligence()
        
        engine = DevelopmentEngine(
            knowledge_tracker=knowledge_tracker,
            training_tracker=training_tracker,
            platform_intelligence=platform_intelligence,
        )
        
        # Add some data
        knowledge_tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.3,
            execution_score=0.2,
            evidence_score=0.1,
            confidence=0.3,
            readiness=0.25,
        ))
        
        priorities = engine.generate_priorities()
        
        assert isinstance(priorities, list)
        assert len(priorities) > 0
    
    def test_analyze_knowledge_gaps(self):
        """Test analyzing knowledge gaps generates priorities."""
        knowledge_tracker = KnowledgeProgressTracker()
        
        knowledge_tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.3,
            execution_score=0.2,
            evidence_score=0.1,
            confidence=0.3,
            readiness=0.25,
        ))
        
        engine = DevelopmentEngine(knowledge_tracker=knowledge_tracker)
        
        engine._analyze_knowledge_gaps()
        
        assert len(engine._priorities) > 0
        assert any(p.category == "knowledge" for p in engine._priorities)
    
    def test_analyze_training_needs(self):
        """Test analyzing training needs generates priorities."""
        training_tracker = TrainingTracker()
        
        training_tracker.register_training(TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            progress=0.1,
        ))
        
        engine = DevelopmentEngine(training_tracker=training_tracker)
        
        engine._analyze_training_needs()
        
        assert len(engine._priorities) > 0
        assert any(p.category == "knowledge" for p in engine._priorities)
    
    def test_analyze_platform_blockers(self):
        """Test analyzing platform blockers generates priorities."""
        platform_intelligence = PlatformIntelligence()
        
        platform_intelligence.register_platform_readiness(PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.2,
            knowledge_score=0.5,
            evidence_score=0.1,
            portfolio_score=0.0,
            execution_score=0.3,
            win_probability=0.2,
            economics_score=0.3,
            blockers=["Account suspended", "No reviews"],
        ))
        
        engine = DevelopmentEngine(platform_intelligence=platform_intelligence)
        
        engine._analyze_platform_blockers()
        
        assert len(engine._priorities) > 0
        assert any(p.category == "platform" for p in engine._priorities)
    
    def test_analyze_evidence_gaps(self):
        """Test analyzing evidence gaps generates priorities."""
        knowledge_tracker = KnowledgeProgressTracker()
        
        knowledge_tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.8,
            execution_score=0.7,
            evidence_score=0.1,  # Low evidence
            confidence=0.8,
            readiness=0.65,
        ))
        
        engine = DevelopmentEngine(knowledge_tracker=knowledge_tracker)
        
        engine._analyze_evidence_gaps()
        
        assert len(engine._priorities) > 0
        assert any(p.category == "evidence" for p in engine._priorities)
    
    def test_add_custom_priority(self):
        """Test adding custom development priority."""
        engine = DevelopmentEngine()
        
        engine.add_priority(
            title="Custom priority",
            description="Custom description",
            category="knowledge",
            impact="high",
            effort="medium",
        )
        
        assert len(engine._priorities) == 1
        assert engine._priorities[0].title == "Custom priority"
    
    def test_complete_priority(self):
        """Test marking priority as completed."""
        engine = DevelopmentEngine()
        
        engine.add_priority(
            title="Test priority",
            description="Test description",
            category="knowledge",
        )
        
        engine.complete_priority("Test priority")
        
        assert engine._priorities[0].status == "completed"
    
    def test_get_top_priorities(self):
        """Test getting top development priorities."""
        engine = DevelopmentEngine()
        
        engine.add_priority(
            title="Priority 1",
            description="First priority",
            category="knowledge",
            impact="high",
        )
        
        engine.add_priority(
            title="Priority 2",
            description="Second priority",
            category="evidence",
            impact="medium",
        )
        
        engine.add_priority(
            title="Priority 3",
            description="Third priority",
            category="platform",
            impact="low",
        )
        
        top = engine.get_top_priorities(limit=2)
        
        assert len(top) == 2
        assert all(p.status == "pending" for p in top)
    
    def test_get_priorities_by_category(self):
        """Test getting priorities by category."""
        engine = DevelopmentEngine()
        
        engine.add_priority(
            title="Knowledge priority",
            description="Knowledge gap",
            category="knowledge",
        )
        
        engine.add_priority(
            title="Evidence priority",
            description="Evidence gap",
            category="evidence",
        )
        
        knowledge_priorities = engine.get_priorities_by_category("knowledge")
        
        assert len(knowledge_priorities) == 1
        assert knowledge_priorities[0].category == "knowledge"
    
    def test_priorities_sorted_by_priority(self):
        """Test that priorities are sorted by priority number."""
        knowledge_tracker = KnowledgeProgressTracker()
        
        # Add multiple domains with gaps
        knowledge_tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.3,
            execution_score=0.2,
            evidence_score=0.1,
            confidence=0.3,
            readiness=0.25,
        ))
        
        knowledge_tracker.register_domain(KnowledgeProgress(
            domain="Content Writing",
            knowledge_score=0.4,
            execution_score=0.3,
            evidence_score=0.2,
            confidence=0.4,
            readiness=0.35,
        ))
        
        engine = DevelopmentEngine(knowledge_tracker=knowledge_tracker)
        
        priorities = engine.generate_priorities()
        
        # Check that priorities are sorted
        priority_numbers = [p.priority for p in priorities]
        assert priority_numbers == sorted(priority_numbers)
