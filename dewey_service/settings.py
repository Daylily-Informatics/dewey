"""Runtime settings for Dewey."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEWEY_",
        case_sensitive=False,
        extra="ignore",
    )

    api_bearer_token: str = "dewey-dev-token"
    operator_username: str = "operator"
    operator_password: str = "dewey-dev-password"
    session_secret_key: str = "dewey-dev-session-secret-change-me"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
