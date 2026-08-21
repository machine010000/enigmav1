"""Durable, project-scoped Freelancer Chat persistence models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text

from app.database import Base


class FreelancerConversation(Base):
    __tablename__ = "freelancer_conversations"

    id = Column(String(64), primary_key=True)
    profile_id = Column(String(64), nullable=False, default="enigma_profile")
    user_id = Column(String(64), nullable=False)
    title = Column(String(300), nullable=False, default="Freelancer Chat")
    active_project_id = Column(String(64), nullable=True)
    conversation_metadata = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_freelancer_conversations_user_updated", "user_id", "updated_at"),
        Index("ix_freelancer_conversations_profile", "profile_id"),
    )


class FreelancerChatMessage(Base):
    __tablename__ = "freelancer_chat_messages"

    id = Column(String(64), primary_key=True)
    conversation_id = Column(String(64), ForeignKey("freelancer_conversations.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(String(64), nullable=False, default="enigma_profile")
    user_id = Column(String(64), nullable=False)
    project_id = Column(String(64), nullable=True)
    role = Column(String(20), nullable=False)
    sequence = Column(Integer, nullable=False)
    intent = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_freelancer_messages_conversation_created", "conversation_id", "created_at"),
        Index("uq_freelancer_messages_conversation_sequence", "conversation_id", "sequence", unique=True),
        Index("ix_freelancer_messages_user_project", "user_id", "project_id"),
    )


class FreelancerProjectArtifact(Base):
    __tablename__ = "freelancer_project_artifacts"

    id = Column(String(64), primary_key=True)
    profile_id = Column(String(64), nullable=False, default="enigma_profile")
    user_id = Column(String(64), nullable=False)
    project_id = Column(String(64), nullable=True)
    artifact_type = Column(String(50), nullable=False)
    visibility = Column(String(30), nullable=False, default="project_private")
    version = Column(Integer, nullable=False, default=1)
    content = Column(Text, nullable=False)
    artifact_data = Column("data", JSON, nullable=False, default=dict)
    source_message_id = Column(String(64), ForeignKey("freelancer_chat_messages.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_freelancer_artifacts_user_project_type", "user_id", "project_id", "artifact_type"),
        Index("ix_freelancer_artifacts_visibility_type", "user_id", "visibility", "artifact_type"),
        Index(
            "uq_freelancer_artifact_version",
            "user_id", "project_id", "artifact_type", "version",
            unique=True,
        ),
    )
