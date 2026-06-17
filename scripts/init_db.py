"""Initialize database schema."""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.database.base import Base
from app.models import *  # noqa: F401, F403


async def init_db() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database schema created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
