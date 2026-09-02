import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Celery prefork children inherit the parent's connection pool, and each task's
# asyncio.run() creates a fresh event loop while asyncpg connections stay bound
# to the loop that made them. Both cause "another operation is in progress" /
# "attached to a different loop" crashes. Workers therefore use NullPool:
# every session opens its own connection and never shares it.
_engine_kwargs = {"echo": settings.environment == "development"}
if os.getenv("MELA_CELERY_WORKER"):
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a session per request, always closes it."""
    async with AsyncSessionLocal() as session:
        yield session
