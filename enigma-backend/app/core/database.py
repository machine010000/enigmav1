"""
Production database configuration.

Database connection management with environment-based configuration.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from app.core.config import settings, is_production
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Database engine
engine = None
async_session_maker = None

Base = declarative_base()


def get_database_url() -> str:
    """Get database URL from settings."""
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    return settings.DATABASE_URL


def init_database() -> None:
    """Initialize database engine and session maker."""
    global engine, async_session_maker
    
    database_url = get_database_url()
    
    # Configure engine based on environment
    if is_production():
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    else:
        engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
        )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    logger.info(f"Database initialized: {database_url[:20]}...")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.
    
    Used as a dependency in FastAPI endpoints.
    """
    if async_session_maker is None:
        init_database()
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database() -> None:
    """Close database connections."""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")


async def check_database_health() -> bool:
    """Check if database is healthy and accessible."""
    try:
        async with async_session_maker() as session:
            # Simple query to test connection
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
