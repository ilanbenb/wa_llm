from os import environ
from typing import Optional, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API settings
    port: int = 5001
    host: str = "0.0.0.0"

    # Database settings
    db_uri: str

    # WhatsApp settings
    whatsapp_host: str
    whatsapp_basic_auth_password: Optional[str] = None
    whatsapp_basic_auth_user: Optional[str] = None

    anthropic_api_key: str

    # Voyage settings
    voyage_api_key: str
    voyage_max_retries: int = 5

    # Direct Message settings
    dm_autoreply_enabled: bool = False
    dm_autoreply_message: str = "Hello, I am not designed to answer to specific messages."

    # Optional settings
    debug: bool = False
    log_level: str = "INFO"
    logfire_token: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        arbitrary_types_allowed=True,
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def apply_env(self) -> Self:
        if self.anthropic_api_key:
            environ["ANTHROPIC_API_KEY"] = self.anthropic_api_key

        if self.logfire_token:
            environ["LOGFIRE_TOKEN"] = self.logfire_token

        return self
