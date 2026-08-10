"""
Development Engine

Generates development priorities and recommendations for Enigma.
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.enigma_profile.contracts import (
    DevelopmentPriority,
    Issue,
    IssueSeverity,
    IssueType,
)
from app.enigma_profile.repositories import DevelopmentPriorityRepository
from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.platform_intelligence import PlatformIntelligence


class DevelopmentEngine:
    """
    Engine for generating development priorities.
    
    Analyzes knowledge, evidence, execution, economics, and platform
    performance to generate actionable development priorities.
    """
    
    def __init__(
        self,
        knowledge_tracker: Optional[KnowledgeProgressTracker] = None,
        training_tracker: Optional[TrainingTracker] = None,
        platform_intelligence: Optional[PlatformIntelligence] = None,
        priority_repo: Optional[DevelopmentPriorityRepository] = None,
    ):
        """
        Initialize development engine.
        
        Args:
            knowledge_tracker: Knowledge progress tracker
            training_tracker: Training tracker
            platform_intelligence: Platform intelligence
            priority_repo: Development priority repository
        """
        self.knowledge_tracker = knowledge_tracker or KnowledgeProgressTracker()
        self.training_tracker = training_tracker or TrainingTracker()
        self.platform_intelligence = platform_intelligence or PlatformIntelligence()
        self._priority_repo = priority_repo
        self._priorities: List[DevelopmentPriority] = []
    
    async def generate_priorities(self) -> List[DevelopmentPriority]:
        """
        Generate development priorities.
        
        Returns:
            List of development priorities
        """
        self._priorities = []
        
        # Delete old priorities if repository is available
        if self._priority_repo:
            await self._priority_repo.delete_all_priorities("enigma_profile")
        
        # Analyze knowledge gaps
        self._analyze_knowledge_gaps()
        
        # Analyze training needs
        self._analyze_training_needs()
        
        # Analyze platform blockers
        self._analyze_platform_blockers()
        
        # Analyze evidence gaps
        self._analyze_evidence_gaps()
        
        # Sort by priority
        self._priorities.sort(key=lambda p: p.priority)
        
        # Save priorities to repository
        if self._priority_repo:
            for priority in self._priorities:
                await self._priority_repo.save_priority("enigma_profile", priority)
        
        return self._priorities
    
    def _analyze_knowledge_gaps(self) -> None:
        """Analyze knowledge gaps and generate priorities."""
        domains = self.knowledge_tracker.get_all_domains()
        
        for domain in domains:
            gaps = self.knowledge_tracker.identify_gaps(domain)
            
            if gaps:
                priority = len(self._priorities) + 1
                
                # Determine impact based on number of gaps
                if len(gaps) >= 3:
                    impact = "high"
                elif len(gaps) >= 2:
                    impact = "medium"
                else:
                    impact = "low"
                
                self._priorities.append(
                    DevelopmentPriority(
                        priority=priority,
                        title=f"Improve {domain} knowledge",
                        description=f"; ".join(gaps),
                        category="knowledge",
                        impact=impact,
                        effort="medium",
                        created_at=datetime.utcnow().isoformat(),
                    )
                )
    
    def _analyze_training_needs(self) -> None:
        """Analyze training needs and generate priorities."""
        high_priority = self.training_tracker.get_high_priority_training()
        
        for skill in high_priority:
            priority = len(self._priorities) + 1
            
            self._priorities.append(
                DevelopmentPriority(
                    priority=priority,
                    title=f"Complete training: {skill}",
                    description=f"Training progress below 30%",
                    category="knowledge",
                    impact="high",
                    effort="medium",
                    created_at=datetime.utcnow().isoformat(),
                )
                )
    
    def _analyze_platform_blockers(self) -> None:
        """Analyze platform blockers and generate priorities."""
        platforms = self.platform_intelligence.get_all_platforms()
        
        for platform in platforms:
            readiness = self.platform_intelligence.get_platform_readiness(platform)
            
            if readiness and readiness.blockers:
                priority = len(self._priorities) + 1
                
                # Determine impact based on readiness
                if readiness.overall_readiness < 0.3:
                    impact = "high"
                elif readiness.overall_readiness < 0.5:
                    impact = "medium"
                else:
                    impact = "low"
                
                self._priorities.append(
                    DevelopmentPriority(
                        priority=priority,
                        title=f"Resolve {platform.value} blockers",
                        description=f"; ".join(readiness.blockers[:3]),
                        category="platform",
                        impact=impact,
                        effort="high",
                        created_at=datetime.utcnow().isoformat(),
                    )
                )
    
    def _analyze_evidence_gaps(self) -> None:
        """Analyze evidence gaps and generate priorities."""
        domains = self.knowledge_tracker.get_all_domains()
        
        for domain in domains:
            progress = self.knowledge_tracker.get_progress(domain)
            
            if progress and progress.evidence_score < 0.5:
                priority = len(self._priorities) + 1
                
                # Determine impact based on evidence score
                if progress.evidence_score < 0.3:
                    impact = "high"
                else:
                    impact = "medium"
                
                self._priorities.append(
                    DevelopmentPriority(
                        priority=priority,
                        title=f"Build {domain} portfolio evidence",
                        description=f"Evidence score at {progress.evidence_score:.0%}",
                        category="evidence",
                        impact=impact,
                        effort="high",
                        created_at=datetime.utcnow().isoformat(),
                    )
                )
    
    async def add_priority(
        self,
        title: str,
        description: str,
        category: str,
        impact: str = "medium",
        effort: str = "medium",
    ) -> None:
        """
        Add a custom development priority.
        
        Args:
            title: Priority title
            description: Priority description
            category: Category (knowledge, evidence, execution, economics, platform)
            impact: Impact level (high, medium, low)
            effort: Effort level (high, medium, low)
        """
        priority = len(self._priorities) + 1
        
        new_priority = DevelopmentPriority(
            priority=priority,
            title=title,
            description=description,
            category=category,
            impact=impact,
            effort=effort,
            created_at=datetime.utcnow().isoformat(),
        )
        
        self._priorities.append(new_priority)
        
        if self._priority_repo:
            await self._priority_repo.save_priority("enigma_profile", new_priority)
    
    def complete_priority(self, title: str) -> None:
        """
        Mark a priority as completed.
        
        Args:
            title: Priority title
        """
        for priority in self._priorities:
            if priority.title == title:
                priority.status = "completed"
                break
    
    def get_top_priorities(self, limit: int = 5) -> List[DevelopmentPriority]:
        """
        Get top development priorities.
        
        Args:
            limit: Number of priorities to return
            
        Returns:
            List of development priorities
        """
        return [p for p in self._priorities if p.status == "pending"][:limit]
    
    def get_priorities_by_category(self, category: str) -> List[DevelopmentPriority]:
        """
        Get priorities by category.
        
        Args:
            category: Category name
            
        Returns:
            List of development priorities
        """
        return [p for p in self._priorities if p.category == category and p.status == "pending"]
