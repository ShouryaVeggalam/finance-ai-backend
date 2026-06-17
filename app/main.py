from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.router import api_router
from app.core.config import settings
from app.core.error_handlers import celestra_exception_handler
from app.core.exceptions import CelestraError
from app.core.logging import setup_logging
from app.database.base import Base
from app.models import *  # noqa: F401, F403


def _database_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    if settings.APP_ENV == "production":
        engine = create_async_engine(_database_url())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Your AI Finance Department — AI-powered Finance Operating System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(CelestraError, celestra_exception_handler)
app.include_router(api_router, prefix="/api/v1")

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}
