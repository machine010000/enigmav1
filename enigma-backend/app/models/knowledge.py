import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class MasterKnowledge(Base):
    __tablename__ = "master_knowledge"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(50), nullable=False)
    domain = Column(String(100), nullable=True)
    market = Column(String(100), nullable=True)
    key = Column(String(200), nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)
    source = Column(String(50), default="ai_inferred")
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OnboardingQuestion(Base):
    __tablename__ = "onboarding_questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    market = Column(String(100), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="text")
    options = Column(JSON, nullable=True)
    purpose = Column(String(100), nullable=True)
    asked_count = Column(Integer, default=0)
    helpful_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    depends_on_question_id = Column(UUID(as_uuid=True), nullable=True)
    show_if_answer = Column(JSON, nullable=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
