from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "URL-Shortner"
    DB_URL: str
    RANGE_ALLOCATOR_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().with_name(".env")
    )

settings = AppSettings()