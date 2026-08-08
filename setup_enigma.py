#!/usr/bin/env python3
"""
ENIGMA Setup Script - Creates all project files automatically
Run this in PowerShell: python setup_enigma.py
"""
import os

BASE = r"E:\app\enigma\enigma-backend"

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {path}")

# 1. requirements.txt
write_file(os.path.join(BASE, "requirements.txt"), 
"""fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
alembic==1.13.2
python-dotenv==1.0.1
pydantic==2.8.2
pydantic-settings==2.3.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
httpx==0.27.0
aiohttp==3.9.5
playwright==1.45.0
beautifulsoup4==4.12.3
redis==5.0.7
celery==5.4.0
""")

# 2. .env
write_file(os.path.join(BASE, ".env"),
"""DATABASE_URL=postgresql://neondb_owner:npg_nIA3hujTsPD1@ep-wandering-forest-asc6s39h-pooler.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
NVIDIA_API_KEY=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
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
AI_MODEL=meta/llama-3.3-70b-instruct
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_URL=redis://localhost:6379/0
""")

# 3. Dockerfile
write_file(os.path.join(BASE, "Dockerfile"),
"""FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""")

# 4. render.yaml
write_file(os.path.join(BASE, "render.yaml"),
"""services:
  - type: web
    name: enigma-api
    runtime: docker
    plan: free
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: NVIDIA_API_KEY
        sync: false
      - key: NVIDIA_BASE_URL
        value: https://integrate.api.nvidia.com/v1
      - key: AI_MODEL
        value: meta/llama-3.3-70b-instruct
      - key: SECRET_KEY
        generateValue: true
""")

# 5. app/__init__.py
write_file(os.path.join(BASE, "app", "__init__.py"), "")

# 6. app/config.py
write_file(os.path.join(BASE, "app", "config.py"),
"""import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "meta/llama-3.3-70b-instruct")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "enigma-dev-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
""")

# 7. app/database.py
write_file(os.path.join(BASE, "app", "database.py"),
"""from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
""")

print("Part 1/4 done!")

# 8. app/models/__init__.py
write_file(os.path.join(BASE, "app", "models", "__init__.py"), "")

# 9. app/models/user.py
write_file(os.path.join(BASE, "app", "models", "user.py"),
"""import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar = Column(String(500), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
""")

# 10. app/models/product.py
write_file(os.path.join(BASE, "app", "models", "product.py"),
"""import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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
    user = relationship("User", back_populates="products")
""")

# 11. app/models/research.py
write_file(os.path.join(BASE, "app", "models", "research.py"),
"""import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ResearchSession(Base):
    __tablename__ = "research_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    status = Column(String(50), default="pending")
    customer_questions = Column(JSON, default=list)
    pain_points = Column(JSON, default=list)
    opportunities = Column(JSON, default=list)
    competitor_analysis = Column(JSON, default=dict)
    audience_insights = Column(JSON, default=dict)
    sources = Column(JSON, default=list)
    patterns_detected = Column(JSON, default=dict)
    applied_knowledge = Column(ARRAY(UUID(as_uuid=True)), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ResearchSource(Base):
    __tablename__ = "research_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    source_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    results_count = Column(Integer, default=0)
    data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
""")

# 12. app/models/decision.py
write_file(os.path.join(BASE, "app", "models", "decision.py"),
"""import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Decision(Base):
    __tablename__ = "decisions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    evidence = Column(JSON, default=dict)
    source_research_id = Column(UUID(as_uuid=True), nullable=True)
    validated = Column(Boolean, default=False)
    validation_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
""")

# 13. app/models/strategy.py
write_file(os.path.join(BASE, "app", "models", "strategy.py"),
"""import uuid
from datetime import datetime, time
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Float, Boolean, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    positioning = Column(Text, nullable=True)
    messaging = Column(Text, nullable=True)
    content_strategy = Column(JSON, default=dict)
    growth_strategy = Column(JSON, default=dict)
    phases = Column(JSON, default=list)
    success_rate = Column(Float, nullable=True)
    adjusted_from = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

class ExecutionPlan(Base):
    __tablename__ = "execution_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(50), default="pending")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("execution_plans.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(Time, nullable=True)
    impact = Column(String(20), default="medium")
    status = Column(String(50), default="pending")
    platform = Column(String(50), nullable=True)
    auto_execute = Column(Boolean, default=False)
    content_template = Column(Text, nullable=True)
    media_urls = Column(ARRAY(String), default=list)
    result_data = Column(JSON, default=dict)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
""")

print("Part 2/4 done!")

# 14. app/models/analytics.py
write_file(os.path.join(BASE, "app", "models", "analytics.py"),
"""import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer, Float, ARRAY
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
""")

# 15. app/models/knowledge.py
write_file(os.path.join(BASE, "app", "models", "knowledge.py"),
"""import uuid
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
""")

# 16. app/ai/__init__.py
write_file(os.path.join(BASE, "app", "ai", "__init__.py"), "")

# 17. app/ai/client.py
write_file(os.path.join(BASE, "app", "ai", "client.py"),
"""import httpx
import json
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()

class NVIDIAClient:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat(self, messages, temperature=0.7, max_tokens=1000, response_format=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def generate_json(self, system_prompt, user_prompt, temperature=0.5):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = await self.chat(messages, temperature, 2000, {"type": "json_object"})
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)

nvidia_client = NVIDIAClient()
""")

print("Part 3/4 done!")

# 18. app/ai/master_brain.py
write_file(os.path.join(BASE, "app", "ai", "master_brain.py"),
"""import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.ai.client import nvidia_client
from app.models.knowledge import MasterKnowledge

class MasterBrain:
    SYSTEM_PROMPT = \"\"\"You are ENIGMA's Master Brain - the central intelligence hub.
You have deep knowledge of business, marketing, and consumer psychology.
You learn from every interaction and improve your guidance over time.
When the user teaches you something, store it precisely.
When asked for guidance, use your accumulated knowledge.
Always think step-by-step and provide actionable insights.\"\"\"

    async def chat(self, db, user_id, message):
        intent = await self._detect_intent(message)
        knowledge = await self._get_relevant_knowledge(db, message)
        context = self._build_context(knowledge)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT + "\n\n" + context},
            {"role": "user", "content": message}
        ]

        response = await nvidia_client.chat(messages, temperature=0.7)
        reply = response["choices"][0]["message"]["content"]

        if intent == "teach":
            extracted = await self._extract_knowledge(message, reply)
            if extracted:
                await self._store_knowledge(db, user_id, extracted)
                reply += f"\n\n[✓] Learned: {extracted['key']}"

        return {"reply": reply, "intent": intent, "knowledge_used": len(knowledge)}

    async def _detect_intent(self, message):
        prompt = f\"\"\"Analyze this message and classify intent:
Message: \"{message}\"
Choose one: teach, ask, command, feedback, chat
Respond with just the intent word.\"\"\"
        response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=20)
        intent = response["choices"][0]["message"]["content"].strip().lower()
        return intent if intent in ["teach", "ask", "command", "feedback"] else "chat"

    async def _get_relevant_knowledge(self, db, query, limit=5):
        result = await db.execute(select(MasterKnowledge).limit(limit))
        return result.scalars().all()

    def _build_context(self, knowledge):
        if not knowledge:
            return ""
        context = "Relevant knowledge:\n"
        for k in knowledge:
            context += f"- [{k.category}] {k.key}: {k.value}\n"
        return context

    async def _extract_knowledge(self, message, reply):
        prompt = f\"\"\"Extract structured knowledge from this teaching message.
Message: \"{message}\"
Respond in JSON format:
{{"category": "marketing|market|product|audience|other", "domain": "fashion|tech|food|general", "market": "egypt|saudi|global|unknown", "key": "short_key_name", "value": "detailed knowledge", "confidence": 0.8}}\"\"\"
        try:
            response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=500)
            content = response["choices"][0]["message"]["content"]
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return None

    async def _store_knowledge(self, db, user_id, knowledge):
        mk = MasterKnowledge(
            category=knowledge.get("category", "general"),
            domain=knowledge.get("domain", "general"),
            market=knowledge.get("market", "global"),
            key=knowledge["key"],
            value=knowledge["value"],
            confidence=knowledge.get("confidence", 0.5),
            source="user_taught"
        )
        db.add(mk)
        await db.commit()

    async def guide_product_brain(self, db, product_category, product_market, task):
        result = await db.execute(select(MasterKnowledge).limit(10))
        knowledge = result.scalars().all()
        guidance = f\"\"\"Guide product brain for:
Category: {product_category}
Market: {product_market}
Task: {task}
Accumulated wisdom:
\"\"\"
        for k in knowledge:
            guidance += f"- {k.key}: {k.value} (confidence: {k.confidence})\n"
        response = await nvidia_client.chat([
            {"role": "system", "content": "You are guiding a product AI. Provide specific, actionable guidance."},
            {"role": "user", "content": guidance}
        ])
        return {"guidance": response["choices"][0]["message"]["content"], "knowledge_applied": len(knowledge)}

master_brain = MasterBrain()
""")

# 19. app/ai/product_brain.py
write_file(os.path.join(BASE, "app", "ai", "product_brain.py"),
"""import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.client import nvidia_client
from app.ai.master_brain import master_brain
from app.models.product import Product

class ProductBrain:
    async def onboard(self, db, product_id):
        product = await db.get(Product, product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        basic_questions = [
            {"id": "product_exact", "question": "ما هو المنتج بالضبط؟ صفه بإيجاز.", "type": "text", "purpose": "understand_product"},
            {"id": "target_audience", "question": "من هو جمهورك المستهدف الرئيسي؟", "type": "text", "purpose": "identify_audience"},
            {"id": "price_range", "question": "ما هو السعر المتوقع أو الحالي؟", "type": "text", "purpose": "pricing"},
            {"id": "market_location", "question": "في أي سوق/بلد تبيع أو تخطط للبيع؟", "type": "text", "purpose": "market_location"}
        ]

        smart_questions = await self._generate_smart_questions(product)
        guidance = await master_brain.guide_product_brain(db, product.category, product.target_market or "global", "onboarding")

        return {"basic_questions": basic_questions, "smart_questions": smart_questions, "master_tips": guidance["guidance"], "total_questions": len(basic_questions) + len(smart_questions)}

    async def _generate_smart_questions(self, product):
        prompt = f\"\"\"Generate 5 specific onboarding questions for this product:
Product: {product.name}
Category: {product.category}
Subcategory: {product.subcategory or 'unknown'}
Market: {product.target_market or 'global'}
Respond in JSON array format.\"\"\"
        try:
            response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
            content = response["choices"][0]["message"]["content"]
            json_match = __import__('re').search(r'\[.*\]', content, __import__('re').DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error: {e}")
        return [{"id": "usp", "question": "ما الذي يميز منتجك عن المنافسين؟", "type": "text", "purpose": "unique_selling_point"}]

    async def process_onboarding_answers(self, db, product_id, answers):
        product = await db.get(Product, product_id)
        product.onboarding_data = answers

        prompt = f\"\"\"Analyze this product based on onboarding answers:
Product: {product.name}
Category: {product.category}
Answers: {json.dumps(answers, ensure_ascii=False)}
Provide structured understanding in JSON.\"\"\"

        try:
            response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            json_match = __import__('re').search(r'\{.*\}', content, __import__('re').DOTALL)
            if json_match:
                understanding = json.loads(json_match.group())
                product.ai_understanding = understanding
                product.status = "researching"
                await db.commit()
                return {"status": "success", "understanding": understanding, "next_step": "research"}
        except Exception as e:
            print(f"Error: {e}")
        return {"status": "error", "message": "Could not process answers"}

product_brain = ProductBrain()
""")

print("Part 4/4 done!")

# 20. app/routers/__init__.py
write_file(os.path.join(BASE, "app", "routers", "__init__.py"), "")

# 21. app/routers/auth.py
write_file(os.path.join(BASE, "app", "routers", "auth.py"),
"""from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    plan: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_data.email, name=user_data.name, hashed_password=get_password_hash(user_data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
""")

# 22. app/routers/products.py
write_file(os.path.join(BASE, "app", "routers", "products.py"),
"""from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.routers.auth import get_current_user
from app.ai.product_brain import product_brain

router = APIRouter(prefix="/products", tags=["products"])

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    domain: Optional[str] = None
    target_market: Optional[str] = "global"

class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    status: str
    created_at: Optional[str] = None
    class Config:
        from_attributes = True

class OnboardingAnswers(BaseModel):
    answers: dict

@router.post("", response_model=ProductResponse)
async def create_product(data: ProductCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    product = Product(user_id=current_user.id, name=data.name, description=data.description, category=data.category, subcategory=data.subcategory, domain=data.domain, target_market=data.target_market, status="onboarding")
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.get("", response_model=List[ProductResponse])
async def list_products(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.user_id == current_user.id).order_by(desc(Product.created_at)))
    return result.scalars().all()

@router.get("/{product_id}")
async def get_product(product_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/{product_id}/onboarding")
async def get_onboarding_questions(product_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    questions = await product_brain.onboard(db, product_id)
    return questions

@router.post("/{product_id}/onboarding")
async def submit_onboarding_answers(product_id: str, data: OnboardingAnswers, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    result = await product_brain.process_onboarding_answers(db, product_id, data.answers)
    return result
""")

# 23. app/routers/master_brain.py
write_file(os.path.join(BASE, "app", "routers", "master_brain.py"),
"""from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.ai.master_brain import master_brain
from app.models.knowledge import MasterKnowledge
from sqlalchemy import select

router = APIRouter(prefix="/brain", tags=["master_brain"])

class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_master_brain(data: ChatMessage, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await master_brain.chat(db, str(current_user.id), data.message)
    return {"reply": result["reply"], "intent": result["intent"], "knowledge_used": result["knowledge_used"]}

@router.get("/knowledge")
async def get_master_knowledge(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MasterKnowledge).order_by(MasterKnowledge.created_at.desc()).limit(50))
    knowledge = result.scalars().all()
    return {"knowledge": [{"id": str(k.id), "category": k.category, "domain": k.domain, "market": k.market, "key": k.key, "value": k.value, "confidence": k.confidence, "source": k.source} for k in knowledge]}
""")

# 24. app/main.py
write_file(os.path.join(BASE, "app", "main.py"),
"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import auth, products, master_brain

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ENIGMA is initializing...")
    await init_db()
    print("Database connected and tables created")
    yield
    print("ENIGMA shutting down...")

app = FastAPI(title="ENIGMA - AI Business Brain", description="Your intelligent partner for business growth", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(master_brain.router)

@app.get("/")
async def root():
    return {"name": "ENIGMA - AI Business Brain", "version": "1.0.0", "status": "running", "ai_provider": "NVIDIA NIM (Free Tier)", "database": "Neon PostgreSQL"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
""")

print("All files written!")
print(f"Run: python {os.path.join(BASE, 'setup_enigma.py')}")