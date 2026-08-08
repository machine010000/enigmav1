import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    domain = Column(String(100), nullable=True)
    target_market = Column(String(100), nullable=True)
    status = Column(String(50), default="onboarding")
    onboarding_data = Column(JSON, default=dict)
    ai_understanding = Column(JSON, default=dict)
    master_knowledge_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    learned_patterns = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
