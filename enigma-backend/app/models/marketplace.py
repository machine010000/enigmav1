"""
Marketplace Database Models

Database models for persistent marketplace state.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, ForeignKey, Index, Boolean, Numeric
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base
from app.marketplace.contracts import MarketplacePlatform, AccountStatus, ApplicationStatus
from app.marketplace.account_state import DataSource, FreshnessStatus


class AccountStatusEnum(str, enum.Enum):
    """Account status enum for database."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class DataSourceEnum(str, enum.Enum):
    """Data source enum for database."""
    MANUAL_INPUT = "manual_input"
    API_INTEGRATION = "api_integration"
    MOCK_ADAPTER = "mock_adapter"
    UNKNOWN = "unknown"


class FreshnessStatusEnum(str, enum.Enum):
    """Freshness status enum for database."""
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ApplicationStatusEnum(str, enum.Enum):
    """Application status enum for database."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    WITHDRAWN = "withdrawn"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class MarketplaceAccountState(Base):
    """
    Canonical marketplace account state.
    
    Represents the actual state of an account on a marketplace platform.
    """
    __tablename__ = "marketplace_account_states"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier for data isolation
    platform = Column(String, nullable=False)  # MarketplacePlatform enum value
    account_id = Column(String, nullable=True)
    account_status = Column(ENUM(AccountStatusEnum, name="account_status_enum"), default=AccountStatusEnum.UNKNOWN)
    
    # Credits/Tokens
    credits_available = Column(Integer, nullable=True)
    credits_pending = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    credits_limit = Column(Integer, nullable=True)
    credits_currency = Column(String, nullable=True)  # e.g., "Connects", "Credits"
    
    # Wallet/Balance
    wallet_available = Column(Numeric(10, 2), nullable=True)
    wallet_currency = Column(String, default="USD")
    
    # Subscription/Plan
    subscription_plan_name = Column(String, nullable=True)
    subscription_plan_type = Column(String, nullable=True)  # e.g., "basic", "premium"
    subscription_expires_at = Column(DateTime, nullable=True)
    subscription_features = Column(JSON, default=dict)
    
    # Metadata
    last_verified_at = Column(DateTime)
    source = Column(ENUM(DataSourceEnum, name="data_source_enum"), default=DataSourceEnum.UNKNOWN)
    confidence = Column(Float, default=0.5)  # 0.0 to 1.0
    freshness = Column(ENUM(FreshnessStatusEnum, name="freshness_status_enum"), default=FreshnessStatusEnum.UNKNOWN)
    
    # Additional platform-specific data
    account_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_marketplace_account_state_profile_platform", "profile_id", "platform", unique=True),
    )


class MarketplaceJob(Base):
    """
    Normalized job data from any marketplace.
    """
    __tablename__ = "marketplace_jobs"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier for data isolation
    job_id = Column(String, nullable=False)  # Internal Enigma job ID
    platform = Column(String, nullable=False)  # MarketplacePlatform enum value
    platform_job_id = Column(String, nullable=False)  # Platform-specific job ID
    
    # Job details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    budget_min = Column(Numeric(10, 2), nullable=True)
    budget_max = Column(Numeric(10, 2), nullable=True)
    budget_type = Column(String, nullable=True)  # "hourly", "fixed", "negotiable"
    currency = Column(String, default="USD")
    
    # Client info
    client_info = Column(JSON, default=dict)
    
    # Requirements
    skills_required = Column(JSON, default=list)  # List of skill strings
    job_type = Column(String, nullable=True)  # "one-time", "ongoing", "milestone"
    duration = Column(String, nullable=True)  # "less_than_1_week", "1-3_months", etc.
    
    # Timing
    posted_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    
    # Cost and URL
    url = Column(String, nullable=True)
    platform_cost = Column(JSON, nullable=True)  # PlatformCost as JSON
    
    # Additional data
    job_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)  # Last sync with platform

    # Indexes
    __table_args__ = (
        Index("ix_marketplace_jobs_profile_platform_job_id", "profile_id", "platform", "platform_job_id", unique=True),
        Index("ix_marketplace_jobs_job_id", "job_id"),
    )


class MarketplaceJobAssessment(Base):
    """
    Assessment of a job's suitability for the user.
    """
    __tablename__ = "marketplace_job_assessments"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier for data isolation
    job_id = Column(String, nullable=False)  # References marketplace_jobs.job_id
    
    # Assessment scores
    knowledge_match_score = Column(Float, default=0.0)  # 0.0 to 1.0
    evidence_match_score = Column(Float, default=0.0)  # 0.0 to 1.0
    execution_match_score = Column(Float, default=0.0)  # 0.0 to 1.0
    overall_readiness_score = Column(Float, default=0.0)  # 0.0 to 1.0
    win_probability = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Assessment details
    recommended_action = Column(String, nullable=True)  # "apply", "skip", "review"
    blockers = Column(JSON, default=list)  # List of blocker descriptions
    strengths = Column(JSON, default=list)  # List of strength descriptions
    recommendations = Column(JSON, default=list)  # List of recommendations
    
    # Metadata
    assessed_at = Column(DateTime, default=datetime.utcnow)
    assessment_version = Column(String, default="1.0")
    assessment_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_marketplace_job_assessments_profile_job", "profile_id", "job_id", unique=True),
    )


class MarketplaceApplication(Base):
    """
    Normalized application data for any marketplace.
    """
    __tablename__ = "marketplace_applications"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier for data isolation
    application_id = Column(String, nullable=False, unique=True)  # Internal Enigma application ID
    job_id = Column(String, nullable=False)  # References marketplace_jobs.job_id
    platform = Column(String, nullable=False)  # MarketplacePlatform enum value
    platform_job_id = Column(String, nullable=False)  # Platform-specific job ID
    platform_application_id = Column(String, nullable=True)  # Platform-specific application ID
    
    # Application status (TASK-052C: Must persist all 12 states)
    status = Column(ENUM(ApplicationStatusEnum, name="application_status_enum"), default=ApplicationStatusEnum.DRAFT)
    status_history = Column(JSON, default=list)  # List of status transitions with timestamps
    
    # Application content
    proposal_text = Column(Text, default="")
    cover_letter = Column(Text, default="")
    attachments = Column(JSON, default=list)  # List of attachment URLs/paths
    
    # Bid information
    bid_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String, default="USD")
    
    # Timing
    submitted_at = Column(DateTime, nullable=True)
    
    # Additional data
    application_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_marketplace_applications_profile_job", "profile_id", "job_id"),
        Index("ix_marketplace_applications_platform_application_id", "platform", "platform_application_id"),
    )


class MarketplaceActiveWork(Base):
    """
    Active work/engagement tracking.
    """
    __tablename__ = "marketplace_active_work"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier for data isolation
    work_id = Column(String, nullable=False, unique=True)  # Internal Enigma work ID
    application_id = Column(String, nullable=False)  # References marketplace_applications.application_id
    platform = Column(String, nullable=False)  # MarketplacePlatform enum value
    platform_work_id = Column(String, nullable=True)  # Platform-specific work/contract ID
    
    # Work status
    status = Column(String, default="active")  # "active", "completed", "cancelled", "paused"
    
    # Work details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Compensation
    total_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String, default="USD")
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    
    # Progress
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    milestones_completed = Column(Integer, default=0)
    milestones_total = Column(Integer, nullable=True)
    
    # Additional data
    work_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_marketplace_active_work_profile_application", "profile_id", "application_id"),
        Index("ix_marketplace_active_work_platform_work_id", "platform", "platform_work_id"),
    )
