"""
Database configuration with async SQLAlchemy + Neon PostgreSQL
"""
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()

# Convert postgresql:// to postgresql+asyncpg:// for async support
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Remove sslmode from URL (asyncpg doesn't accept it as kwarg)
import urllib.parse
parsed = urllib.parse.urlparse(DATABASE_URL)
query_params = urllib.parse.parse_qs(parsed.query)

# Extract sslmode if present
sslmode = query_params.pop('sslmode', ['require'])[0]
channel_binding = query_params.pop('channel_binding', [None])[0]

# Rebuild URL without sslmode
new_query = urllib.parse.urlencode(query_params, doseq=True)
DATABASE_URL = urllib.parse.urlunparse(parsed._replace(query=new_query))

# Create SSL context
ssl_context = ssl.create_default_context()
if sslmode == 'require':
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED

# Create async engine with SSL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    future=True,
    connect_args={
        "ssl": ssl_context
    }
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

async def get_db():
    """Dependency to get DB session"""
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
    """Create all tables"""
    import app.models  # noqa: F401 - registers every model on Base.metadata before create_all
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)