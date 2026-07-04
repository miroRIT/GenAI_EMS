from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EmergencyPulse"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://emergencypulse:emergencypulse@localhost:5432/emergencypulse"
    )
    jwt_issuer: str = "emergencypulse"
    jwt_audience: str = "emergencypulse-api"
    jwt_secret: str = Field(default="local-development-secret-change-me", min_length=24)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30

    admin_username: str = "dispatcher"
    admin_password_hash: str = Field(
        default="$2y$05$5jgoN0K85u0eA2jorSfF2OcRni/1hGVGKAzZxXykE6TnurhCqiwv6"
    )

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
