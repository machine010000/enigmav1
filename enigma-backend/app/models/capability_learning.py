"""System-owned capability progress and auditable evidence promotion ledger."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SystemCapabilityProgress(Base):
    __tablename__ = "system_capability_progress"

    capability_id = Column(String(100), primary_key=True)
    knowledge_score = Column(Float, default=0.0, nullable=False)
    execution_score = Column(Float, default=0.0, nullable=False)
    evidence_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    readiness = Column(Float, default=0.0, nullable=False)
    capability_status = Column(String(50), default="unknown", nullable=False)
    evidence_count = Column(Integer, default=0, nullable=False)
    successful_execution_count = Column(Integer, default=0, nullable=False)
    failed_execution_count = Column(Integer, default=0, nullable=False)
    last_success_at = Column(DateTime, nullable=True)
    freelance_readiness_threshold = Column(Float, default=0.65, nullable=False)
    last_verified = Column(DateTime, nullable=True)
    freshness = Column(String(50), default="unknown", nullable=False)
    concepts = Column(JSON, default=dict, nullable=False)
    policy_version = Column(String(50), default="capability-promotion-v1", nullable=False)
    aggregate_source = Column(String(50), default="promotion_ledger", nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CapabilityEvidenceContribution(Base):
    __tablename__ = "capability_evidence_contributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(
        UUID(as_uuid=True), ForeignKey("worker_executions.id", ondelete="RESTRICT"),
        nullable=False, unique=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    capability_id = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)
    training_mode = Column(String(50), nullable=True)
    observation_status = Column(String(30), nullable=False)
    evaluation_score = Column(Float, nullable=True)
    evidence_digest = Column(String(64), nullable=False)
    evidence_reference = Column(JSON, default=dict, nullable=False)
    eligibility_state = Column(String(30), nullable=False)
    decision_state = Column(String(30), nullable=False)
    policy_version = Column(String(50), nullable=False)
    decision_reason = Column(Text, nullable=False)
    promoted_at = Column(DateTime, nullable=True)
    promoted_by = Column(String(100), nullable=True)
    progress_applied = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_capability_contribution_capability_decision", "capability_id", "decision_state"),
        Index("ix_capability_contribution_user_created", "user_id", "created_at"),
    )
