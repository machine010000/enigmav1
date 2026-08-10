"""
Training Tracker

Tracking and analysis of training and learning progress.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

from app.enigma_profile.contracts import (
    TrainingItem,
    SkillLevel,
)
from app.enigma_profile.repositories import TrainingItemRepository


class TrainingTracker:
    """
    Tracker for training and learning progress.
    
    Tracks what Enigma has trained on, current skill levels,
    and what needs training.
    """
    
    def __init__(self, training_repo: Optional[TrainingItemRepository] = None):
        """Initialize training tracker.
        
        Args:
            training_repo: Training item repository
        """
        self._training_items: List[TrainingItem] = []
        self._skill_levels: Dict[str, SkillLevel] = {}
        self._training_repo = training_repo
    
    async def register_training(self, item: TrainingItem) -> None:
        """
        Register a training item.
        
        Args:
            item: Training item
        """
        self._training_items.append(item)
        self._skill_levels[item.skill] = item.level
        if self._training_repo:
            await self._training_repo.save_training("enigma_profile", item)
    
    def get_training(self, skill: str) -> Optional[TrainingItem]:
        """
        Get training item for a skill.
        
        Args:
            skill: Skill name
            
        Returns:
            TrainingItem or None
        """
        for item in self._training_items:
            if item.skill == skill:
                return item
        return None
    
    def get_skill_level(self, skill: str) -> SkillLevel:
        """
        Get skill level for a skill.
        
        Args:
            skill: Skill name
            
        Returns:
            SkillLevel
        """
        return self._skill_levels.get(skill, SkillLevel.UNKNOWN)
    
    async def update_progress(self, skill: str, progress: float) -> None:
        """
        Update training progress for a skill.
        
        Args:
            skill: Skill name
            progress: Progress (0.0 to 1.0)
        """
        item = self.get_training(skill)
        if item:
            item.progress = min(1.0, max(0.0, progress))
            
            # Update skill level based on progress
            if progress >= 0.9:
                item.level = SkillLevel.EXPERT
            elif progress >= 0.7:
                item.level = SkillLevel.OPERATIONAL
            elif progress >= 0.5:
                item.level = SkillLevel.GROWING
            elif progress >= 0.2:
                item.level = SkillLevel.LEARNING
            
            self._skill_levels[skill] = item.level
            
            if self._training_repo:
                await self._training_repo.save_training("enigma_profile", item)
    
    async def complete_training(self, skill: str) -> None:
        """
        Mark training as completed.
        
        Args:
            skill: Skill name
        """
        item = self.get_training(skill)
        if item:
            item.progress = 1.0
            item.completed_at = datetime.utcnow().isoformat()
            item.level = SkillLevel.OPERATIONAL  # Minimum operational level
            self._skill_levels[skill] = item.level
            
            if self._training_repo:
                await self._training_repo.save_training("enigma_profile", item)
    
    def identify_training_needs(self) -> List[str]:
        """
        Identify skills that need training.
        
        Returns:
            List of skill names that need training
        """
        needs = []
        
        for item in self._training_items:
            if item.progress < 0.5:
                needs.append(item.skill)
            elif item.level in [SkillLevel.LEARNING, SkillLevel.UNKNOWN]:
                needs.append(item.skill)
        
        return needs
    
    def get_high_priority_training(self) -> List[str]:
        """
        Get high priority training needs.
        
        Returns:
            List of skill names with low progress (< 0.3)
        """
        return [
            item.skill
            for item in self._training_items
            if item.progress < 0.3
        ]
    
    async def get_all_training(self) -> List[TrainingItem]:
        """Get all training items."""
        if self._training_repo:
            return await self._training_repo.get_all_training("enigma_profile")
        return self._training_items
    
    def get_all_skills(self) -> List[str]:
        """Get all tracked skills."""
        return list(self._skill_levels.keys())
    
    def get_skills_by_level(self, level: SkillLevel) -> List[str]:
        """
        Get skills at a specific level.
        
        Args:
            level: Skill level
            
        Returns:
            List of skill names
        """
        return [
            skill
            for skill, skill_level in self._skill_levels.items()
            if skill_level == level
        ]
    
    def generate_training_recommendations(self) -> List[str]:
        """
        Generate training recommendations based on current state.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        high_priority = self.get_high_priority_training()
        if high_priority:
            recommendations.append(
                f"HIGH PRIORITY: Complete training for {', '.join(high_priority)}"
            )
        
        needs = self.identify_training_needs()
        if needs:
            for skill in needs:
                item = self.get_training(skill)
                if item:
                    recommendations.append(
                        f"Improve {skill}: {item.progress:.0%} complete"
                    )
        
        return recommendations
