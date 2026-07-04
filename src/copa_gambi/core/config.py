from functools import lru_cache
from pathlib import Path

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
    skills_dir: Path = Field(
        default=Path("skills"),
        description="Directory containing shared Agno skills (relative to CWD when not absolute).",
    )

    reddit_client_id: str | None = Field(
        default=None,
        description="Reddit OAuth client id. When unset, RedditTools is skipped.",
    )
    reddit_client_secret: str | None = Field(
        default=None,
        description="Reddit OAuth client secret. When unset, RedditTools is skipped.",
    )
    reddit_user_agent: str = Field(
        default="copa-gambi/0.1 (sentiment)",
        description="User-Agent string Reddit requires for API access.",
    )

    football_data_token: str | None = Field(
        default=None,
        description="football-data.org API token. When unset, the stats tool is skipped.",
    )

    exa_api_key: str | None = Field(
        default=None,
        description="Exa API key (https://exa.ai). When unset, ExaTools is skipped.",
    )

    no_tools_models: str = Field(
        default="",
        description=(
            "Comma-separated model-id substrings that cannot do function calling "
            "(e.g. 'llama3.2:1b,tinyllama'). Matching agents debate without tools "
            "or skills, using only their own knowledge."
        ),
    )
    no_skills_models: str = Field(
        default="",
        description=(
            "Comma-separated model-id substrings that handle plain tools but not "
            "the skill workflow. Matching agents keep tools and lose skills."
        ),
    )
    preflight_probe: bool = Field(
        default=True,
        description=(
            "Probe each undeclared participant with a one-token tool request "
            "before the debate; models whose server rejects tools join without "
            "them instead of crashing the run."
        ),
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
