from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def normalize_async_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def engine_connect_args(url: str) -> dict:
    if "render.com" in url:
        return {"ssl": True}
    return {}


def _require_async_url(url: str) -> str:
    normalized = normalize_async_url(url)
    if not normalized.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            f"DATABASE_URL must use PostgreSQL async driver (postgresql+asyncpg://). Got: {normalized[:40]}..."
        )
    return normalized


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = _require_async_url(settings.DATABASE_URL)
        _engine = create_async_engine(
            url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args=engine_connect_args(url),
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
