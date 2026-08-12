"""
Enigma Profile Database Models

Database models for persistent Enigma Profile state.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class SkillLevelEnum(str, enum.Enum):
    """Skill level enum for database."""
    LEARNING = "learning"
    GROWING = "growing"
    OPERATIONAL = "operational"
    EXPERT = "expert"
    UNKNOWN = "unknown"


class IssueSeverityEnum(str, enum.Enum):
    """Issue severity enum for database."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class IssueTypeEnum(str, enum.Enum):
    """Issue type enum for database."""
    SYSTEM = "system"
    API = "api"
    MARKETPLACE = "marketplace"
    KNOWLEDGE = "knowledge"
    EXECUTION = "execution"
    BUSINESS = "business"
    CLIENT = "client"
    UNKNOWN = "unknown"


class IssueStatusEnum(str, enum.Enum):
    """Issue status enum for database."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class EnigmaProfile(Base):
    """
    Enigma's internal operator intelligence profile.
    
    This is NOT a user profile - it's Enigma's private admin profile
    for tracking knowledge, training, performance, and development.
    """
    __tablename__ = "enigma_profiles"

    # Identity
    profile_id = Column(String, primary_key=True, default="enigma_profile")
    owner = Column(String, default="Enigma")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Goals (stored as JSON arrays)
    active_goals = Column(JSON, default=list)
    target_professions = Column(JSON, default=list)
    target_platforms = Column(JSON, default=list)
    target_markets = Column(JSON, default=list)
    target_languages = Column(JSON, default=list)

    # Metadata
    profile_metadata = Column("metadata", JSON, default=dict)

    # Relationships
    knowledge_progress = relationship("KnowledgeProgress", back_populates="profile", cascade="all, delete-orphan")
    training_items = relationship("TrainingItem", back_populates="profile", cascade="all, delete-orphan")
    platform_readiness = relationship("PlatformReadiness", back_populates="profile", cascade="all, delete-orphan")
    development_priorities = relationship("DevelopmentPriority", back_populates="profile", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="profile", cascade="all, delete-orphan")


class CapabilityStatus(str, enum.Enum):
    """
    TASK-017: Canonical capability status vocabulary.
    
    Progression: UNKNOWN → LEARNING → PRACTICING → QUALIFIED → PROVEN
    Status is derived from evidence counts and confidence — never self-asserted
    by the LLM.
    """
    UNKNOWN = "unknown"
    LEARNING = "learning"      # evidence_count < 3 OR confidence < 0.4
    PRACTICING = "practicing"  # evidence_count >= 3 AND confidence >= 0.4
    QUALIFIED = "qualified"    # evidence_count >= 5 AND confidence >= 0.65
    PROVEN = "proven"          # evidence_count >= 10 AND confidence >= 0.80


class KnowledgeProgress(Base):
    """
    Progress tracking for a knowledge domain / capability.

    TASK-017 extensions:
    - capability_status: evidence-derived status (UNKNOWN→LEARNING→PRACTICING→QUALIFIED→PROVEN)
    - evidence_count: total executions observed
    - successful_execution_count: successful executions only
    - failed_execution_count: failed executions only
    - last_success_at: timestamp of most recent successful execution
    - freelance_readiness_threshold: minimum confidence required for READY_TO_APPLY
    """
    __tablename__ = "knowledge_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("enigma_profiles.profile_id", ondelete="CASCADE"))
    domain = Column(String, nullable=False)
    
    # Scores (0.0 to 1.0)
    knowledge_score = Column(Float, default=0.0)
    execution_score = Column(Float, default=0.0)
    evidence_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    readiness = Column(Float, default=0.0)
    
    # TASK-017: evidence-based capability status
    capability_status = Column(String, default=CapabilityStatus.UNKNOWN.value)
    evidence_count = Column(Integer, default=0)
    successful_execution_count = Column(Integer, default=0)
    failed_execution_count = Column(Integer, default=0)
    last_success_at = Column(DateTime, nullable=True)
    # Minimum confidence threshold before this capability qualifies for READY_TO_APPLY
    freelance_readiness_threshold = Column(Float, default=0.65)
    
    # Metadata
    last_verified = Column(DateTime)
    freshness = Column(String, default="unknown")  # fresh, stale, expired
    concepts = Column(JSON, default=dict)  # concept -> score
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    profile = relationship("EnigmaProfile", back_populates="knowledge_progress")

    # Indexes
    __table_args__ = (
        Index("ix_knowledge_progress_profile_domain", "profile_id", "domain", unique=True),
    )


class TrainingItem(Base):
    """
    Training item for learning tracker.
    """
    __tablename__ = "training_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("enigma_profiles.profile_id", ondelete="CASCADE"))
    skill = Column(String, nullable=False)
    level = Column(ENUM(SkillLevelEnum, name="skill_level_enum"), default=SkillLevelEnum.UNKNOWN)
    
    # Progress
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Additional data
    resources = Column(JSON, default=list)
    notes = Column(Text, default="")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    profile = relationship("EnigmaProfile", back_populates="training_items")

    # Indexes
    __table_args__ = (
        Index("ix_training_items_profile_skill", "profile_id", "skill", unique=True),
    )


class PlatformReadiness(Base):
    """
    Readiness assessment for a marketplace platform.
    """
    __tablename__ = "platform_readiness"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("enigma_profiles.profile_id", ondelete="CASCADE"))
    platform = Column(String, nullable=False)  # Stored as string from MarketplacePlatform enum
    
    # Scores (0.0 to 1.0)
    overall_readiness = Column(Float, default=0.0)
    knowledge_score = Column(Float, default=0.0)
    evidence_score = Column(Float, default=0.0)
    portfolio_score = Column(Float, default=0.0)
    execution_score = Column(Float, default=0.0)
    win_probability = Column(Float, default=0.0)
    economics_score = Column(Float, default=0.0)
    
    # Lists
    blockers = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    # Metadata
    last_updated = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    profile = relationship("EnigmaProfile", back_populates="platform_readiness")

    # Indexes
    __table_args__ = (
        Index("ix_platform_readiness_profile_platform", "profile_id", "platform", unique=True),
    )


class DevelopmentPriority(Base):
    """
    Development priority item.
    """
    __tablename__ = "development_priorities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("enigma_profiles.profile_id", ondelete="CASCADE"))
    
    # Priority data
    priority = Column(Integer, nullable=False)  # 1 = highest
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    category = Column(String, default="knowledge")  # knowledge, evidence, execution, economics, platform
    impact = Column(String, default="medium")  # high, medium, low
    effort = Column(String, default="medium")  # high, medium, low
    status = Column(String, default="pending")  # pending, in_progress, completed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    profile = relationship("EnigmaProfile", back_populates="development_priorities")

    # Indexes
    __table_args__ = (
        Index("ix_development_priorities_profile_priority", "profile_id", "priority"),
    )


class Issue(Base):
    """
    Issue or error tracking.
    """
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("enigma_profiles.profile_id", ondelete="CASCADE"))
    issue_id = Column(String, unique=True, nullable=False)  # ISSUE-XXXXXXXX
    
    # Issue data
    source = Column(String, default="system")  # system, platform, task
    type = Column(ENUM(IssueTypeEnum, name="issue_type_enum"), default=IssueTypeEnum.UNKNOWN)
    severity = Column(ENUM(IssueSeverityEnum, name="issue_severity_enum"), default=IssueSeverityEnum.UNKNOWN)
    status = Column(ENUM(IssueStatusEnum, name="issue_status_enum"), default=IssueStatusEnum.OPEN)
    
    # Details
    timestamp = Column(DateTime, default=datetime.utcnow)
    platform = Column(String)  # Marketplace platform (optional)
    task = Column(String)  # Task identifier (optional)
    detected_reason = Column(Text, default="")
    impact = Column(Text, default="")
    required_action = Column(Text, default="")
    resolved_at = Column(DateTime)
    
    # Additional metadata
    issue_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    profile = relationship("EnigmaProfile", back_populates="issues")

    # Indexes
    __table_args__ = (
        Index("ix_issues_profile_id", "profile_id"),
        Index("ix_issues_issue_id", "issue_id"),
        Index("ix_issues_status_severity", "status", "severity"),
    )
