from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Celestra Finance AI"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

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

    @property
    def all_cors_origins(self) -> list[str]:
        origins = list(self.CORS_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL.rstrip("/") not in origins:
            origins.append(self.FRONTEND_URL.rstrip("/"))
        return origins


settings = Settings()
