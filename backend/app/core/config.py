"""Application configuration settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    app_name: str = "Reimagined Job Board"
    database_url: str = "sqlite+aiosqlite:///./jobboard.db"
    sync_database_url: str = "sqlite:///./jobboard.db"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    cors_origins: List[AnyHttpUrl] = []
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/1"
    rate_limit_per_minute: int = 60

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
