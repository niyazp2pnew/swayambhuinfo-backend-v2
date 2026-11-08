from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Swayambhu Operations Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"

    SECRET_KEY: str = "096722edfabe6ca46e79f5322a6b31854417a6a2068c7d5a0f61094b80e4b395"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Raw connection URL from environment (.env)
    DATABASE_URL: str

    STORAGE_DIR: str = "/app/storage"

    @computed_field
    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL.strip().strip("'").strip('"')

        # 1. Clean parameters that break asyncpg
        for bad_param in ["&channel_binding=require", "channel_binding=require&", "channel_binding=require"]:
            url = url.replace(bad_param, "")

        # 2. Convert sslmode=... to ssl=... for asyncpg compatibility
        if "sslmode=" in url:
            url = url.replace("sslmode=require", "ssl=require").replace("sslmode=prefer", "ssl=prefer")

        # 3. Ensure asyncpg dialect
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @computed_field
    @property
    def sync_database_url(self) -> str:
        url = self.DATABASE_URL.strip().strip("'").strip('"')

        # Clean channel_binding for synchronous psycopg2
        for bad_param in ["&channel_binding=require", "channel_binding=require&", "channel_binding=require"]:
            url = url.replace(bad_param, "")

        # Ensure sync psycopg2 dialect
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