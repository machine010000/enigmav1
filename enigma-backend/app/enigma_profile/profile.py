"""
Enigma Profile

Main Enigma Profile module - Enigma's internal operator intelligence profile.
"""

from datetime import datetime
from typing import Optional, List

from app.enigma_profile.contracts import (
    EnigmaProfile,
    KnowledgeProgress,
    TrainingItem,
    PlatformReadiness,
    DevelopmentPriority,
    Issue,
    IssueSeverity,
    IssueType,
    IssueStatus,
)
from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.development_engine import DevelopmentEngine
from app.enigma_profile.issue_intelligence import IssueIntelligence
from app.enigma_profile.repositories import (
    EnigmaProfileRepository,
    KnowledgeProgressRepository,
    TrainingItemRepository,
    PlatformReadinessRepository,
    DevelopmentPriorityRepository,
    IssueRepository,
)
from app.marketplace.contracts import MarketplacePlatform


class EnigmaProfileManager:
    """
    Manager for Enigma's internal operator intelligence profile.
    
    This is NOT a user profile - it's Enigma's private admin profile
    for tracking knowledge, training, performance, and development.
    """
    
    def __init__(
        self,
        profile_repo: Optional[EnigmaProfileRepository] = None,
        knowledge_repo: Optional[KnowledgeProgressRepository] = None,
        training_repo: Optional[TrainingItemRepository] = None,
        platform_repo: Optional[PlatformReadinessRepository] = None,
        priority_repo: Optional[DevelopmentPriorityRepository] = None,
        issue_repo: Optional[IssueRepository] = None,
    ):
        """Initialize Enigma profile manager.
        
        Args:
            profile_repo: Enigma Profile repository
            knowledge_repo: Knowledge Progress repository
            training_repo: Training Item repository
            platform_repo: Platform Readiness repository
            priority_repo: Development Priority repository
            issue_repo: Issue repository
        """
        self.profile_repo = profile_repo
        self.knowledge_repo = knowledge_repo
        self.training_repo = training_repo
        self.platform_repo = platform_repo
        self.priority_repo = priority_repo
        self.issue_repo = issue_repo
        
        self.profile = EnigmaProfile()
        self.knowledge_tracker = KnowledgeProgressTracker(knowledge_repo=knowledge_repo)
        self.training_tracker = TrainingTracker(training_repo=training_repo)
        self.platform_intelligence = PlatformIntelligence(platform_repo=platform_repo)
        self.development_engine = DevelopmentEngine(
            knowledge_tracker=self.knowledge_tracker,
            training_tracker=self.training_tracker,
            platform_intelligence=self.platform_intelligence,
            priority_repo=priority_repo,
        )
        self.issue_intelligence = IssueIntelligence(issue_repo=issue_repo)
    
    async def initialize_default_profile(self) -> EnigmaProfile:
        """
        Initialize default Enigma profile with common domains.
        
        Returns:
            Initialized EnigmaProfile
        """
        # Set default goals
        self.profile.active_goals = [
            "Build SEO expertise",
            "Establish marketplace presence",
            "Develop portfolio evidence",
        ]
        
        self.profile.target_professions = ["SEO Specialist", "Content Writer"]
        self.profile.target_platforms = [
            MarketplacePlatform.UPWORK,
            MarketplacePlatform.FREELANCER,
            MarketplacePlatform.FIVERR,
        ]
        self.profile.target_markets = ["Canada", "USA", "UK", "Egypt"]
        self.profile.target_languages = ["English", "Arabic"]
        
        # Initialize knowledge domains
        await self._initialize_knowledge_domains()
        
        # Initialize training items
        await self._initialize_training_items()
        
        # Initialize platform readiness
        await self._initialize_platform_readiness()
        
        # Generate development priorities
        await self._generate_development_priorities()
        
        self.profile.updated_at = datetime.utcnow().isoformat()
        
        # Save profile if repository is available
        if self.profile_repo:
            self.profile = await self.profile_repo.save_profile(self.profile)
        
        return self.profile
    
    async def _initialize_knowledge_domains(self) -> None:
        """Initialize common knowledge domains."""
        domains = [
            "SEO",
            "Keyword Research",
            "On-Page SEO",
            "Technical SEO",
            "Content Writing",
            "Proposal Writing",
            "Client Communication",
        ]
        
        for domain in domains:
            progress = KnowledgeProgress(
                domain=domain,
                knowledge_score=0.5,
                execution_score=0.3,
                evidence_score=0.2,
                confidence=0.4,
                readiness=0.35,
                last_verified=datetime.utcnow().isoformat(),
                freshness="fresh",
            )
            
            await self.knowledge_tracker.register_domain(progress)
            self.profile.knowledge_progress[domain] = progress
    
    async def _initialize_training_items(self) -> None:
        """Initialize common training items."""
        skills = [
            "SEO Audit",
            "Keyword Research",
            "On-Page SEO",
            "Technical SEO",
            "Proposal Writing",
            "Client Communication",
        ]
        
        for skill in skills:
            item = TrainingItem(
                skill=skill,
                level="learning",
                started_at=datetime.utcnow().isoformat(),
                progress=0.2,
            )
            
            await self.training_tracker.register_training(item)
            self.profile.training_items.append(item)
    
    async def _initialize_platform_readiness(self) -> None:
        """Initialize platform readiness."""
        platforms = [
            MarketplacePlatform.UPWORK,
            MarketplacePlatform.FREELANCER,
            MarketplacePlatform.FIVERR,
            MarketplacePlatform.MOSTAQL,
            MarketplacePlatform.KHAMSAT,
        ]
        
        for platform in platforms:
            readiness = PlatformReadiness(
                platform=platform,
                overall_readiness=0.3,
                knowledge_score=0.5,
                evidence_score=0.2,
                portfolio_score=0.1,
                execution_score=0.3,
                win_probability=0.4,
                economics_score=0.5,
                blockers=["No reviews", "Weak portfolio", "Low evidence"],
                recommendations=[
                    "Build 3 proof-of-work assets",
                    "Complete 5 simulated SEO tasks",
                    "Improve proposal strategy",
                ],
                last_updated=datetime.utcnow().isoformat(),
            )
            
            await self.platform_intelligence.register_platform_readiness(readiness)
            self.profile.platform_readiness[platform] = readiness
    
    async def _generate_development_priorities(self) -> None:
        """Generate development priorities."""
        priorities = await self.development_engine.generate_priorities()
        self.profile.development_priorities = priorities
    
    async def update_profile(self) -> EnigmaProfile:
        """
        Update profile with latest data from trackers.
        
        Returns:
            Updated EnigmaProfile
        """
        # Update knowledge progress
        knowledge_progress = await self.knowledge_tracker.get_all_progress()
        self.profile.knowledge_progress = knowledge_progress
        
        # Update training items
        training_items = await self.training_tracker.get_all_training()
        self.profile.training_items = training_items
        
        # Update platform readiness
        platform_readiness = await self.platform_intelligence.get_all_readiness()
        self.profile.platform_readiness = platform_readiness
        
        # Update development priorities
        self.profile.development_priorities = await self.development_engine.generate_priorities()
        
        # Update issues
        self.profile.issues = await self.issue_intelligence.get_all_issues()
        
        self.profile.updated_at = datetime.utcnow().isoformat()
        
        # Save profile if repository is available
        if self.profile_repo:
            self.profile = await self.profile_repo.save_profile(self.profile)
        
        return self.profile
    
    def get_profile_summary(self) -> str:
        """
        Generate profile summary.
        
        Returns:
            Summary string
        """
        lines = [
            "ENIGMA PROFILE",
            f"Owner: {self.profile.owner}",
            f"Updated: {self.profile.updated_at}",
            "",
            "Active Goals:",
        ]
        
        for goal in self.profile.active_goals:
            lines.append(f"- {goal}")
        
        lines.append("")
        lines.append("Knowledge Progress:")
        
        for domain, progress in self.profile.knowledge_progress.items():
            lines.append(f"{domain}: {progress.readiness:.0%} readiness")
        
        lines.append("")
        lines.append("Top Development Priorities:")
        
        priorities = self.profile.get_development_priorities(limit=3)
        for priority in priorities:
            lines.append(f"{priority.priority}. {priority.title}")
        
        lines.append("")
        lines.append(self.issue_intelligence.generate_issue_summary())
        
        return "\n".join(lines)
    
    async def report_system_issue(
        self,
        error_message: str,
        platform: Optional[MarketplacePlatform] = None,
    ) -> Issue:
        """
        Report a system issue.
        
        Args:
            error_message: Error message
            platform: Platform (if applicable)
            
        Returns:
            Created issue
        """
        issue = await self.issue_intelligence.auto_classify_system_error(error_message, platform)
        self.profile.issues.append(issue)
        return issue
    
    def get_platform_summary(self, platform: MarketplacePlatform) -> Optional[str]:
        """
        Get platform readiness summary.
        
        Args:
            platform: Marketplace platform
            
        Returns:
            Summary string or None
        """
        return self.platform_intelligence.generate_platform_summary(platform)
