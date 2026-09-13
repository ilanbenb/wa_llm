from os import environ
from typing import Final, Optional, Self

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

# Provider prefixes this app manages credentials for.
# prefix -> (Settings attribute, environment variable pydantic-ai reads)
_MANAGED_PROVIDERS: Final[dict[str, tuple[str, str]]] = {
    "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
    "openrouter": ("openrouter_api_key", "OPENROUTER_API_KEY"),
}

# pydantic-ai still accepts unprefixed legacy names, mapping them to a provider by
# prefix (its private `_LEGACY_MODEL_PREFIXES`). We mirror only the entry that maps
# to a provider we manage, so `MODEL_NAME=claude-sonnet-4-6` is credential-checked
# the same as `anthropic:claude-sonnet-4-6`.
_LEGACY_NAME_PROVIDERS: Final[dict[str, str]] = {"claude": "anthropic"}


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

    # LLM provider credentials. Which one is required depends on the provider
    # `model_name` resolves to — see `validate_model_credentials`.
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # Voyage settings
    voyage_api_key: str
    voyage_max_retries: int = 5

    # Model settings
    model_name: str = "anthropic:claude-sonnet-4-6"

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
    def validate_model_credentials(self) -> Self:
        """Require the API key for the provider `model_name` resolves to.

        Mirrors pydantic-ai's resolution order: an explicit `provider:` prefix first,
        then its legacy unprefixed names. Providers we don't manage are left alone —
        pydantic-ai is the authority on what it supports and raises its own error.
        """
        model_name = self.model_name.strip()
        provider, sep, _ = model_name.partition(":")
        if not sep:
            provider = next(
                (
                    name
                    for prefix, name in _LEGACY_NAME_PROVIDERS.items()
                    if model_name.startswith(prefix)
                ),
                "",
            )

        managed = _MANAGED_PROVIDERS.get(provider)
        if managed is None:
            return self

        attr, env_var = managed
        if not getattr(self, attr):
            raise ValueError(
                f"model_name '{self.model_name}' uses the '{provider}' provider, "
                f"so {env_var} must be set."
            )
        return self

    @model_validator(mode="after")
    def apply_env(self) -> Self:
        if self.anthropic_api_key:
            environ["ANTHROPIC_API_KEY"] = self.anthropic_api_key

        if self.openrouter_api_key:
            environ["OPENROUTER_API_KEY"] = self.openrouter_api_key

        if self.logfire_token:
            environ["LOGFIRE_TOKEN"] = self.logfire_token

        return self


@lru_cache
def get_settings() -> Settings:
    # Use model_validate({}) to trigger Pydantic's validation and environment variable loading
    # without passing arguments directly, which satisfies type checkers that would otherwise
    # complain about missing required fields in __init__.
    return Settings.model_validate({})
