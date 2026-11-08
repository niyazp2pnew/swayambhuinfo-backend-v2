import os
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory pointing to the repository root (swayambhu-backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    PROJECT_NAME: str = "Swayambhu Operations Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str

    # Defaults to ./storage inside your project folder where Render has full write permissions
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage")

    @computed_field
    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL.strip().strip("'").strip('"')
        for bad_param in [
            "&channel_binding=require",
            "channel_binding=require&",
            "channel_binding=require",
        ]:
            url = url.replace(bad_param, "")
        if "sslmode=" in url:
            url = url.replace("sslmode=require", "ssl=require").replace(
                "sslmode=prefer", "ssl=prefer"
            )
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @computed_field
    @property
    def sync_database_url(self) -> str:
        url = self.DATABASE_URL.strip().strip("'").strip('"')
        for bad_param in [
            "&channel_binding=require",
            "channel_binding=require&",
            "channel_binding=require",
        ]:
            url = url.replace(bad_param, "")
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()