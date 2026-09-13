from os import environ
from typing import Any

import pytest
from pydantic import ValidationError

from config import Settings

# Required fields unrelated to LLM provider selection, so each test only has to
# state the model/key combination it actually cares about.
_BASE: dict[str, Any] = {
    "db_uri": "postgresql+asyncpg://u:p@localhost:5432/db",
    "whatsapp_host": "http://localhost:3000",
    "voyage_api_key": "voyage-test",
    "logfire_token": "logfire-test",
}

_ENV_VARS = ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "LOGFIRE_TOKEN", "MODEL_NAME")

_OPENROUTER_MODEL = "openrouter:anthropic/claude-sonnet-4.6"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from ambient credentials.

    Registering each variable with monkeypatch first is what allows the direct
    ``os.environ`` writes in ``Settings.apply_env`` to be rolled back afterwards.
    """
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def build(**overrides: Any) -> Settings:
    # `_env_file=None` keeps a developer's local .env from leaking into the test.
    # It goes inside the unpacked dict because pydantic's synthesised __init__
    # signature hides BaseSettings' underscore-prefixed parameters from pyright.
    return Settings(**{**_BASE, **overrides, "_env_file": None})


def test_anthropic_model_with_key_exports_env_var():
    settings = build(anthropic_api_key="sk-ant-test")

    assert settings.model_name == "anthropic:claude-sonnet-4-6"
    assert environ["ANTHROPIC_API_KEY"] == "sk-ant-test"


def test_openrouter_model_needs_no_anthropic_key():
    settings = build(model_name=_OPENROUTER_MODEL, openrouter_api_key="sk-or-v1-test")

    assert settings.anthropic_api_key is None
    assert environ["OPENROUTER_API_KEY"] == "sk-or-v1-test"
    assert "ANTHROPIC_API_KEY" not in environ


def test_openrouter_model_without_key_is_rejected():
    with pytest.raises(ValidationError, match="OPENROUTER_API_KEY"):
        build(model_name=_OPENROUTER_MODEL)


def test_anthropic_model_without_key_is_rejected():
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        build()


def test_unmanaged_provider_passes_through_without_a_key():
    # pydantic-ai owns credential resolution for providers we don't manage.
    settings = build(model_name="openai:gpt-5")

    assert settings.model_name == "openai:gpt-5"


def test_legacy_unprefixed_claude_name_still_requires_anthropic_key():
    # pydantic-ai maps the bare `claude...` name onto the anthropic provider,
    # so the credential check has to follow it there.
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        build(model_name="claude-sonnet-4-6")


def test_test_model_needs_no_credentials():
    assert build(model_name="test").model_name == "test"


def test_both_keys_are_exported_when_both_are_set():
    build(
        model_name=_OPENROUTER_MODEL,
        anthropic_api_key="sk-ant-test",
        openrouter_api_key="sk-or-v1-test",
    )

    assert environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
    assert environ["OPENROUTER_API_KEY"] == "sk-or-v1-test"


def test_default_model_name_is_unchanged():
    # Guards existing deployments that never set MODEL_NAME.
    assert Settings.model_fields["model_name"].default == "anthropic:claude-sonnet-4-6"
