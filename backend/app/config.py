from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["mock"]


class Settings(BaseSettings):
    """Server-side settings used by the local portfolio demo."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "PawPost AI"
    frontend_origin: str = "http://localhost:3000"
    max_image_size_mb: int = Field(default=15, ge=1, le=50)

    image_ai_provider: ProviderName = "mock"
    text_ai_provider: ProviderName = "mock"

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def allowed_frontend_origins(self) -> list[str]:
        """Support configured LAN origins plus both common loopback spellings."""
        configured = [
            origin.strip().rstrip("/")
            for origin in self.frontend_origin.split(",")
            if origin.strip()
        ]
        return list(
            dict.fromkeys(
                [
                    *configured,
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ]
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
