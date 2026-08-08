import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey, JSON, Integer, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ProductAnalytics(Base):
    __tablename__ = "product_analytics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    date = Column(Date, nullable=False)
    views = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    platform_breakdown = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class LearningFingerprint(Base):
    __tablename__ = "learning_fingerprints"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    category = Column(String(100), nullable=False)
    market = Column(String(100), nullable=False)
    what_worked = Column(JSON, default=list)
    what_failed = Column(JSON, default=list)
    audience_patterns = Column(JSON, default=dict)
    content_patterns = Column(JSON, default=dict)
    similar_products = Column(ARRAY(UUID(as_uuid=True)), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
