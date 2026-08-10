"""
Test Training Tracker

Tests for training and learning progress tracking.
"""

import pytest
from datetime import datetime

from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.contracts import (
    TrainingItem,
    SkillLevel,
)


class TestTrainingTracker:
    """Test TrainingTracker."""
    
    def test_initialization(self):
        """Test tracker initialization."""
        tracker = TrainingTracker()
        assert tracker is not None
        assert tracker._training_items == []
    
    def test_register_training(self):
        """Test registering a training item."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            started_at=datetime.utcnow().isoformat(),
            progress=0.2,
        )
        
        tracker.register_training(item)
        
        retrieved = tracker.get_training("Technical SEO")
        assert retrieved is not None
        assert retrieved.skill == "Technical SEO"
        assert retrieved.progress == 0.2
    
    def test_get_training_not_found(self):
        """Test getting training for unregistered skill."""
        tracker = TrainingTracker()
        
        retrieved = tracker.get_training("Nonexistent")
        assert retrieved is None
    
    def test_get_skill_level(self):
        """Test getting skill level."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.OPERATIONAL,
            started_at=datetime.utcnow().isoformat(),
            progress=0.7,
        )
        
        tracker.register_training(item)
        
        level = tracker.get_skill_level("Technical SEO")
        assert level == SkillLevel.OPERATIONAL
    
    def test_get_skill_level_unknown(self):
        """Test getting skill level for unknown skill."""
        tracker = TrainingTracker()
        
        level = tracker.get_skill_level("Nonexistent")
        assert level == SkillLevel.UNKNOWN
    
    def test_update_progress(self):
        """Test updating training progress."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            started_at=datetime.utcnow().isoformat(),
            progress=0.2,
        )
        
        tracker.register_training(item)
        
        tracker.update_progress("Technical SEO", 0.6)
        
        updated = tracker.get_training("Technical SEO")
        assert updated.progress == 0.6
        assert updated.level == SkillLevel.GROWING
    
    def test_update_progress_to_expert(self):
        """Test updating progress to expert level."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            started_at=datetime.utcnow().isoformat(),
            progress=0.2,
        )
        
        tracker.register_training(item)
        
        tracker.update_progress("Technical SEO", 0.95)
        
        updated = tracker.get_training("Technical SEO")
        assert updated.progress == 0.95
        assert updated.level == SkillLevel.EXPERT
    
    def test_complete_training(self):
        """Test completing training."""
        tracker = TrainingTracker()
        
        item = TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            started_at=datetime.utcnow().isoformat(),
            progress=0.5,
        )
        
        tracker.register_training(item)
        
        tracker.complete_training("Technical SEO")
        
        completed = tracker.get_training("Technical SEO")
        assert completed.progress == 1.0
        assert completed.completed_at is not None
        assert completed.level == SkillLevel.OPERATIONAL
    
    def test_identify_training_needs(self):
        """Test identifying training needs."""
        tracker = TrainingTracker()
        
        tracker.register_training(TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            progress=0.2,
        ))
        
        tracker.register_training(TrainingItem(
            skill="Keyword Research",
            level=SkillLevel.OPERATIONAL,
            progress=0.8,
        ))
        
        needs = tracker.identify_training_needs()
        
        assert "Technical SEO" in needs
        assert "Keyword Research" not in needs
    
    def test_get_high_priority_training(self):
        """Test getting high priority training needs."""
        tracker = TrainingTracker()
        
        tracker.register_training(TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            progress=0.1,
        ))
        
        tracker.register_training(TrainingItem(
            skill="Keyword Research",
            level=SkillLevel.OPERATIONAL,
            progress=0.8,
        ))
        
        high_priority = tracker.get_high_priority_training()
        
        assert "Technical SEO" in high_priority
        assert "Keyword Research" not in high_priority
    
    def test_get_all_skills(self):
        """Test getting all tracked skills."""
        tracker = TrainingTracker()
        
        tracker.register_training(TrainingItem(skill="SEO", level=SkillLevel.LEARNING))
        tracker.register_training(TrainingItem(skill="Content Writing", level=SkillLevel.GROWING))
        
        skills = tracker.get_all_skills()
        
        assert len(skills) == 2
        assert "SEO" in skills
        assert "Content Writing" in skills
    
    def test_get_skills_by_level(self):
        """Test getting skills by level."""
        tracker = TrainingTracker()
        
        tracker.register_training(TrainingItem(skill="SEO", level=SkillLevel.LEARNING))
        tracker.register_training(TrainingItem(skill="Content Writing", level=SkillLevel.LEARNING))
        tracker.register_training(TrainingItem(skill="Technical SEO", level=SkillLevel.OPERATIONAL))
        
        learning_skills = tracker.get_skills_by_level(SkillLevel.LEARNING)
        
        assert len(learning_skills) == 2
        assert "SEO" in learning_skills
        assert "Content Writing" in learning_skills
    
    def test_generate_training_recommendations(self):
        """Test generating training recommendations."""
        tracker = TrainingTracker()
        
        tracker.register_training(TrainingItem(
            skill="Technical SEO",
            level=SkillLevel.LEARNING,
            progress=0.1,
        ))
        
        recommendations = tracker.generate_training_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("HIGH PRIORITY" in rec for rec in recommendations)
