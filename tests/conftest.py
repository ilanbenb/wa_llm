"""Pytest configuration for test suite."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from config import Settings

pytest_plugins = ["src.test_utils.mock_session"]


@pytest.fixture
def mock_settings():
    return Settings(
        whatsapp_host="http://test-whatsapp",
        whatsapp_basic_auth_user="user",
        whatsapp_basic_auth_password="password",
        db_uri="postgresql+asyncpg://user:pass@localhost/db",
        anthropic_api_key="test-key",
        voyage_api_key="test-voyage-key",
        logfire_token="test-token",
    )


@pytest.fixture
def client(mock_settings):
    # Override settings
    app.state.settings = mock_settings

    with (
        patch("app.main.WhatsAppClient") as MockWhatsAppClient,
        patch("app.main.create_async_engine") as mock_create_engine,
        patch("app.main.async_sessionmaker") as mock_sessionmaker,
        patch("app.main.AsyncClient") as MockAsyncClient,
        patch("app.main.gather_groups"),
        patch("app.main.logfire"),
        patch("handler.base_handler.upsert") as mock_upsert,
    ):
        # Configure mocks
        mock_whatsapp_instance = AsyncMock()
        # Configure get_my_jid to return a real JID object (synchronous behavior for properties)
        from whatsapp.jid import JID

        mock_whatsapp_instance.get_my_jid.return_value = JID(
            user="bot", server="s.whatsapp.net"
        )

        # Configure send_message response
        mock_response = MagicMock()
        mock_response.results.message_id = "msg_123"
        mock_whatsapp_instance.send_message.return_value = mock_response

        MockWhatsAppClient.return_value = mock_whatsapp_instance

        # Configure upsert to return the model
        async def fake_upsert(session, model):
            return model

        mock_upsert.side_effect = fake_upsert

        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine

        mock_session = AsyncMock()

        # Mock begin_nested to return an async context manager
        mock_nested = MagicMock()
        mock_nested.__aenter__.return_value = None
        mock_nested.__aexit__.return_value = None
        mock_session.begin_nested = MagicMock(return_value=mock_nested)

        # Configure exec to return a MagicMock (result object)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_session_factory.return_value.__aexit__.return_value = None
        mock_sessionmaker.return_value = mock_session_factory

        mock_embedding_client = AsyncMock()
        MockAsyncClient.return_value = mock_embedding_client

        # Create TestClient
        with TestClient(app) as c:
            # Ensure state is set (lifespan should have set it using our mocks)
            # But we can also force it if needed, though patching classes is cleaner
            yield c
