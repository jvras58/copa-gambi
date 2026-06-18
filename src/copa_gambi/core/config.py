from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="COPA_",
        extra="ignore",
    )

    hub_url: HttpUrl = Field(
        default="http://localhost:3000",
        description="Base URL of the Gambi Hub.",
    )
    room_code: str = Field(
        default="ABC123",
        description="Room code created via `gambi room create`.",
    )
    api_key: str = Field(
        default="gambi",
        description="API key forwarded to the OpenAI-compatible Hub endpoint.",
    )
    request_timeout: float = Field(
        default=30.0,
        description="HTTP timeout (seconds) when calling the Hub.",
    )

    @property
    def hub_base(self) -> str:
        return str(self.hub_url).rstrip("/")

    @property
    def openai_base_url(self) -> str:
        return f"{self.hub_base}/v1"

    def participants_url(self) -> str:
        return f"{self.hub_base}/rooms/{self.room_code}/participants"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
