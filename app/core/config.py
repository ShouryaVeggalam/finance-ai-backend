import json
import os

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://finance-ai--dun.vercel.app",
    "https://finance-ai-frontend.vercel.app",
]

# Env var names Render / hosting platforms may use for Postgres
_DB_ENV_KEYS = (
    "DATABASE_URL",
    "DATABASE_URL_SYNC",
    "POSTGRES_URL",
    "POSTGRESQL_URL",
    "POSTGRES_PRISMA_URL",
    "PGDATABASE_URL",
    "RENDER_DATABASE_URL",
    "DB_URL",
    "DATABASE_CONNECTION_STRING",
    "INTERNAL_DATABASE_URL",
    "EXTERNAL_DATABASE_URL",
)


def _first_db_url() -> tuple[str, str]:
    """Return (async_url_source, env_key_used)."""
    for key in _DB_ENV_KEYS:
        value = os.getenv(key, "").strip()
        if value:
            return value, key
    return "", ""


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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    APP_NAME: str = "Celestra Finance AI"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

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

    CORS_ORIGINS: list[str] = _DEFAULT_CORS_ORIGINS.copy()
    FRONTEND_URL: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            return _DEFAULT_CORS_ORIGINS.copy()
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return _DEFAULT_CORS_ORIGINS.copy()
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [part.strip() for part in stripped.split(",") if part.strip()]
        return _DEFAULT_CORS_ORIGINS.copy()

    @model_validator(mode="after")
    def resolve_urls(self) -> "Settings":
        async_url = self.DATABASE_URL.strip()
        sync_url = self.DATABASE_URL_SYNC.strip()

        if not async_url and not sync_url:
            discovered, env_key = _first_db_url()
            if discovered:
                async_url = discovered
                # Log which env var was used (visible in Render logs)
                print(f"[celestra] Using database URL from env var: {env_key}")

        if async_url and not sync_url:
            sync_url = _to_sync_pg_url(async_url)
        elif sync_url and not async_url:
            async_url = _to_asyncpg_url(sync_url)
        elif async_url:
            async_url = _to_asyncpg_url(async_url)
            if not sync_url:
                sync_url = _to_sync_pg_url(async_url)

        if not async_url:
            present = [k for k in ("APP_ENV", "FRONTEND_URL", "SECRET_KEY", *_DB_ENV_KEYS) if os.getenv(k)]
            raise ValueError(
                "DATABASE_URL is not set on this Render service. "
                "Fix: Web Service → Environment → Add Environment Variable → "
                "'Add from Render Postgres' (pick your existing DB), OR paste "
                "Internal Database URL as DATABASE_URL. "
                f"Env vars currently present: {', '.join(present) or 'none'}"
            )

        if not self.SECRET_KEY:
            if self.APP_ENV == "production":
                raise ValueError(
                    "SECRET_KEY is required. Add any long random string under Environment in Render."
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
