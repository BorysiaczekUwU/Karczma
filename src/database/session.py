import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from src.config import settings

# Engine for SQLAlchemy (asyncpg)
# In production, we'd use a better pool class than NullPool, but it works well for initial dev
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # poolclass=NullPool
)

# Async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for getting the database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
