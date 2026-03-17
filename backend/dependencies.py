import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool
from backend.config import settings

logger = logging.getLogger(__name__)

def _get_engine_kwargs() -> dict:
    base_kwargs = {
        "echo": settings.DATABASE_ECHO,
    }

    if settings.is_sqlite:
        logger.info("Using SQLite database")
        return {
            **base_kwargs,
            "connect_args": {"check_same_thread": False},
            "poolclass": NullPool,  
        }

    elif settings.is_postgresql:
        logger.info("Using PostgreSQL database")
        return {
            **base_kwargs,
            "connect_args": {"server_settings": {"jit": "off"}},
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,  
        }

    elif settings.is_mysql:
        logger.info("🐬 Using MySQL database")
        return {
            **base_kwargs,
            "connect_args": {"charset": "utf8mb4"},
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,  
        }

    else:
        logger.warning("Unknown database type, using default settings")
        return {
            **base_kwargs,
            "connect_args": {"check_same_thread": False},
            "poolclass": NullPool,
        }

logger.info(f"Connecting to database: {settings.DATABASE_URL}")

engine = create_async_engine(
    settings.DATABASE_URL,
    **_get_engine_kwargs()
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()