"""
Enigma Profile Package

Enigma's internal operator intelligence profile for tracking knowledge, training, performance, and development.
"""

from app.enigma_profile.contracts import (
    SkillLevel,
    IssueSeverity,
    IssueType,
    IssueStatus,
    KnowledgeProgress,
    TrainingItem,
    PlatformReadiness,
    DevelopmentPriority,
    Issue,
    EnigmaProfile,
)
from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.development_engine import DevelopmentEngine
from app.enigma_profile.issue_intelligence import IssueIntelligence
from app.enigma_profile.profile import EnigmaProfileManager

__all__ = [
    # Contracts
    "SkillLevel",
    "IssueSeverity",
    "IssueType",
    "IssueStatus",
    "KnowledgeProgress",
    "TrainingItem",
    "PlatformReadiness",
    "DevelopmentPriority",
    "Issue",
    "EnigmaProfile",
    # Trackers
    "KnowledgeProgressTracker",
    "TrainingTracker",
    # Intelligence
    "PlatformIntelligence",
    "DevelopmentEngine",
    "IssueIntelligence",
    # Manager
    "EnigmaProfileManager",
]
