"""
Enigma Profile Contracts

Core contracts for Enigma's internal operator intelligence profile.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.marketplace.contracts import MarketplacePlatform


class SkillLevel(str, Enum):
    """Skill level for training and knowledge."""
    LEARNING = "learning"
    GROWING = "growing"
    OPERATIONAL = "operational"
    EXPERT = "expert"
    UNKNOWN = "unknown"


class IssueSeverity(str, Enum):
    """Severity level for issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class IssueType(str, Enum):
    """Type of issue."""
    SYSTEM = "system"
    API = "api"
    MARKETPLACE = "marketplace"
    KNOWLEDGE = "knowledge"
    EXECUTION = "execution"
    BUSINESS = "business"
    CLIENT = "client"
    UNKNOWN = "unknown"


class IssueStatus(str, Enum):
    """Status of issue."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class KnowledgeProgress:
    """
    Progress tracking for a knowledge domain.
    """
    domain: str
    knowledge_score: float  # 0.0 to 1.0
    execution_score: float  # 0.0 to 1.0
    evidence_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    readiness: float  # 0.0 to 1.0
    last_verified: Optional[str] = None
    freshness: str = "unknown"  # fresh, stale, expired
    concepts: Dict[str, float] = field(default_factory=dict)  # concept -> score


@dataclass
class TrainingItem:
    """
    Training item for learning tracker.
    """
    skill: str
    level: SkillLevel
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    resources: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PlatformReadiness:
    """
    Readiness assessment for a marketplace platform.
    """
    platform: MarketplacePlatform
    overall_readiness: float  # 0.0 to 1.0
    knowledge_score: float  # 0.0 to 1.0
    evidence_score: float  # 0.0 to 1.0
    portfolio_score: float  # 0.0 to 1.0
    execution_score: float  # 0.0 to 1.0
    win_probability: float  # 0.0 to 1.0
    economics_score: float  # 0.0 to 1.0
    blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None


@dataclass
class DevelopmentPriority:
    """
    Development priority item.
    """
    priority: int  # 1 = highest
    title: str
    description: str
    category: str  # knowledge, evidence, execution, economics, platform
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    created_at: str
    status: str = "pending"  # pending, in_progress, completed


@dataclass
class Issue:
    """
    Issue or error tracking.
    """
    issue_id: str
    source: str  # system, platform, task
    type: IssueType
    severity: IssueSeverity
    timestamp: str
    platform: Optional[MarketplacePlatform] = None
    task: Optional[str] = None
    detected_reason: str = ""
    impact: str = ""
    required_action: str = ""
    status: IssueStatus = IssueStatus.OPEN
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnigmaProfile:
    """
    Enigma's internal operator intelligence profile.
    
    This is NOT a user profile - it's Enigma's private admin profile
    for tracking knowledge, training, performance, and development.
    """
    # Identity
    profile_id: str = "enigma_profile"
    owner: str = "Enigma"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Goals
    active_goals: List[str] = field(default_factory=list)
    target_professions: List[str] = field(default_factory=list)
    target_platforms: List[MarketplacePlatform] = field(default_factory=list)
    target_markets: List[str] = field(default_factory=list)
    target_languages: List[str] = field(default_factory=list)
    
    # Knowledge Progress
    knowledge_progress: Dict[str, KnowledgeProgress] = field(default_factory=dict)
    
    # Training Tracker
    training_items: List[TrainingItem] = field(default_factory=list)
    
    # Platform Intelligence
    platform_readiness: Dict[MarketplacePlatform, PlatformReadiness] = field(default_factory=dict)
    
    # Development Priorities
    development_priorities: List[DevelopmentPriority] = field(default_factory=list)
    
    # Issues
    issues: List[Issue] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_knowledge_progress(self, domain: str) -> Optional[KnowledgeProgress]:
        """Get knowledge progress for a domain."""
        return self.knowledge_progress.get(domain)
    
    def get_platform_readiness(self, platform: MarketplacePlatform) -> Optional[PlatformReadiness]:
        """Get platform readiness."""
        return self.platform_readiness.get(platform)
    
    def get_open_issues(self, severity: Optional[IssueSeverity] = None) -> List[Issue]:
        """Get open issues, optionally filtered by severity."""
        issues = [i for i in self.issues if i.status == IssueStatus.OPEN]
        if severity:
            issues = [i for i in issues if i.severity == severity]
        return issues
    
    def get_development_priorities(self, limit: int = 5) -> List[DevelopmentPriority]:
        """Get top development priorities."""
        sorted_priorities = sorted(
            self.development_priorities,
            key=lambda p: p.priority,
        )
        return [p for p in sorted_priorities if p.status == "pending"][:limit]
