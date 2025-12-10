from os import environ
from typing import Optional, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

from whatsapp.jid import (
    parse_jid,
    JIDParseError,
    DefaultUserServer,
    LegacyUserServer,
    GroupServer,
)


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

    # Model settings
    model_name: str = "anthropic:claude-sonnet-4-5-20250929"

    # Direct Message settings
    dm_autoreply_enabled: bool = False
    dm_autoreply_message: str = (
        "Hello, I am not designed to answer to personal messages."
    )

    # QA tester settings (user JIDs allowed to use /kb_qa command)
    qa_testers: list[str] = []

    # QA test groups (group JIDs where /kb_qa command is allowed)
    qa_test_groups: list[str] = []

    # Optional settings
    debug: bool = False
    log_level: str = "INFO"
    logfire_token: str

    @field_validator("qa_testers")
    @classmethod
    def validate_qa_testers(cls, v: list[str]) -> list[str]:
        """Validate that qa_testers contains valid user JIDs."""
        valid_user_servers = (DefaultUserServer, LegacyUserServer)
        for jid_str in v:
            try:
                jid = parse_jid(jid_str)
            except JIDParseError as e:
                raise ValueError(f"Invalid JID '{jid_str}': {e}") from e

            if jid.server not in valid_user_servers:
                raise ValueError(
                    f"Invalid user JID '{jid_str}'. Expected server to be one of "
                    f"{valid_user_servers}, got '{jid.server}'"
                )
            if not jid.user:
                raise ValueError(f"Invalid user JID '{jid_str}'. Missing user part.")
        return v

    @field_validator("qa_test_groups")
    @classmethod
    def validate_qa_test_groups(cls, v: list[str]) -> list[str]:
        """Validate that qa_test_groups contains valid group JIDs."""
        for jid_str in v:
            try:
                jid = parse_jid(jid_str)
            except JIDParseError as e:
                raise ValueError(f"Invalid JID '{jid_str}': {e}") from e

            if not jid.is_group():
                raise ValueError(
                    f"Invalid group JID '{jid_str}'. Expected server '{GroupServer}', "
                    f"got '{jid.server}'"
                )
            if not jid.user:
                raise ValueError(
                    f"Invalid group JID '{jid_str}'. Missing group ID part."
                )
        return v

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


@lru_cache
def get_settings() -> Settings:
    # Use model_validate({}) to trigger Pydantic's validation and environment variable loading
    # without passing arguments directly, which satisfies type checkers that would otherwise
    # complain about missing required fields in __init__.
    return Settings.model_validate({})
