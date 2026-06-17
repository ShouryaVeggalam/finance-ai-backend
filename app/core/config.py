from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _to_sync_pg_url(url: str) -> str:
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Celestra Finance AI"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Render injects DATABASE_URL when you link Postgres — only one is required
    DATABASE_URL: str = ""
    DATABASE_URL_SYNC: str = ""
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "celestra"
    S3_SECRET_KEY: str = "celestra_secret"
    S3_BUCKET: str = "celestra-finance"
    S3_REGION: str = "us-east-1"

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://finance-ai--dun.vercel.app",
        "https://finance-ai-frontend.vercel.app",
    ]
    FRONTEND_URL: str = ""

    @model_validator(mode="after")
    def resolve_urls(self) -> "Settings":
        async_url = self.DATABASE_URL.strip()
        sync_url = self.DATABASE_URL_SYNC.strip()

        if async_url and not sync_url:
            sync_url = _to_sync_pg_url(async_url)
        elif sync_url and not async_url:
            async_url = _to_asyncpg_url(sync_url)
        elif async_url:
            async_url = _to_asyncpg_url(async_url)
            if not sync_url:
                sync_url = _to_sync_pg_url(async_url)

        if not async_url:
            raise ValueError(
                "Database not configured. On Render: open your Web Service → "
                "Environment → link your existing Postgres (adds DATABASE_URL), "
                "or set DATABASE_URL / DATABASE_URL_SYNC manually."
            )

        if not self.SECRET_KEY:
            if self.APP_ENV == "production":
                raise ValueError(
                    "SECRET_KEY is required in production. "
                    "Add it under Environment in Render (any long random string)."
                )
            object.__setattr__(self, "SECRET_KEY", "dev-only-insecure-secret-key")

        object.__setattr__(self, "DATABASE_URL", async_url)
        object.__setattr__(self, "DATABASE_URL_SYNC", sync_url)

        if not self.REDIS_URL:
            object.__setattr__(self, "REDIS_URL", "redis://localhost:6379/0")
        if not self.CELERY_BROKER_URL:
            object.__setattr__(self, "CELERY_BROKER_URL", self.REDIS_URL)
        if not self.CELERY_RESULT_BACKEND:
            object.__setattr__(self, "CELERY_RESULT_BACKEND", self.REDIS_URL)

        return self

    @property
    def all_cors_origins(self) -> list[str]:
        origins = list(self.CORS_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL.rstrip("/") not in origins:
            origins.append(self.FRONTEND_URL.rstrip("/"))
        return origins


settings = Settings()
