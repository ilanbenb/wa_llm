from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from handler import MessageHandler
from gowa_sdk.webhooks import WebhookEnvelope
from models import Message
from test_utils.mock_session import AsyncSessionMock
from whatsapp import SendMessageRequest
from whatsapp.jid import JID
from config import Settings


@pytest.fixture
def mock_whatsapp():
    client = AsyncMock()
    client.send_message = AsyncMock()
    client.get_my_jid = AsyncMock(return_value=JID(user="bot", server="s.whatsapp.net"))
    return client


@pytest.fixture
def mock_embedding_client():
    client = AsyncMock()
    return client


@pytest.fixture
def mock_settings():
    return Mock(spec=Settings, model_name="test-model", dm_autoreply_enabled=False)


@pytest.mark.asyncio
async def test_message_handler_dm_opt_out(
    mock_session: AsyncSessionMock,
    mock_whatsapp: AsyncMock,
    mock_embedding_client: AsyncMock,
    mock_settings: Mock,
):
    # Create handler instance
    handler = MessageHandler(
        mock_session, mock_whatsapp, mock_embedding_client, mock_settings
    )

    # Mock store_message to return our test message
    test_message = Message(
        message_id="1",
        chat_jid="user@s.whatsapp.net",
        sender_jid="user@s.whatsapp.net",  # DM: sender == chat (usually, but logic checks message.group)
        text="opt-out",
        timestamp=datetime.now(timezone.utc),
    )
    # Ensure message.group is None for DM check
    # In the code: if message and not message.group:
    # Message model has a 'group' relationship. We can just set it to None or rely on default.
    # But wait, store_message returns a Message object.

    # We need to mock store_message because __call__ calls it.
    # However, store_message is an async method on the instance.
    handler.store_message = AsyncMock(return_value=test_message)

    # Create a dummy payload
    payload = WebhookEnvelope.model_validate(
        {
            "event": "message",
            "payload": {
                "id": "msg_opt_out",
                "chat_id": "user@s.whatsapp.net",
                "from": "user@s.whatsapp.net",
                "from_name": "User",
                "timestamp": datetime.now(timezone.utc),
                "body": "opt-out",
            },
        }
    )

    # Fix mock response for send_message
    mock_response = AsyncMock()
    mock_response.results.message_id = "response_id"
    mock_whatsapp.send_message.return_value = mock_response

    await handler(payload)

    # Verify upsert was called (which calls execute)
    mock_session.execute.assert_called()

    # Verify confirmation message
    mock_whatsapp.send_message.assert_called_with(
        SendMessageRequest(
            phone="user@s.whatsapp.net",
            message="You have been opted out. You will no longer be tagged in summaries and answers.",
            reply_message_id=None,
        )
    )


@pytest.mark.asyncio
async def test_message_handler_dm_opt_in(
    mock_session: AsyncSessionMock,
    mock_whatsapp: AsyncMock,
    mock_embedding_client: AsyncMock,
    mock_settings: Mock,
):
    handler = MessageHandler(
        mock_session, mock_whatsapp, mock_embedding_client, mock_settings
    )

    test_message = Message(
        message_id="1",
        chat_jid="user@s.whatsapp.net",
        sender_jid="user@s.whatsapp.net",
        text="opt-in",
        timestamp=datetime.now(timezone.utc),
    )
    handler.store_message = AsyncMock(return_value=test_message)

    payload = WebhookEnvelope.model_validate(
        {
            "event": "message",
            "payload": {
                "id": "msg_opt_in",
                "chat_id": "user@s.whatsapp.net",
                "from": "user@s.whatsapp.net",
                "from_name": "User",
                "timestamp": datetime.now(timezone.utc),
                "body": "opt-in",
            },
        }
    )

    # Mock existing opt-out record
    from models import OptOut

    opt_out = OptOut(jid="user@s.whatsapp.net")
    mock_session._storage[("OptOut", "user@s.whatsapp.net")] = opt_out

    mock_response = AsyncMock()
    mock_response.results.message_id = "response_id"
    mock_whatsapp.send_message.return_value = mock_response

    await handler(payload)

    # Verify delete was called
    mock_session.delete.assert_called_with(opt_out)
    mock_session.commit.assert_called()

    # Verify confirmation message
    mock_whatsapp.send_message.assert_called_with(
        SendMessageRequest(
            phone="user@s.whatsapp.net",
            message="You have been opted in. You will now be tagged in summaries and answers.",
            reply_message_id=None,
        )
    )


@pytest.mark.asyncio
async def test_message_handler_dm_status(
    mock_session: AsyncSessionMock,
    mock_whatsapp: AsyncMock,
    mock_embedding_client: AsyncMock,
    mock_settings: Mock,
):
    handler = MessageHandler(
        mock_session, mock_whatsapp, mock_embedding_client, mock_settings
    )

    test_message = Message(
        message_id="1",
        chat_jid="user@s.whatsapp.net",
        sender_jid="user@s.whatsapp.net",
        text="status",
        timestamp=datetime.now(timezone.utc),
    )
    handler.store_message = AsyncMock(return_value=test_message)

    payload = WebhookEnvelope.model_validate(
        {
            "event": "message",
            "payload": {
                "id": "msg_status",
                "chat_id": "user@s.whatsapp.net",
                "from": "user@s.whatsapp.net",
                "from_name": "User",
                "timestamp": datetime.now(timezone.utc),
                "body": "status",
            },
        }
    )

    # Mock get to return None (opted in)
    mock_session.get.return_value = None

    mock_response = AsyncMock()
    mock_response.results.message_id = "response_id"
    mock_whatsapp.send_message.return_value = mock_response

    await handler(payload)

    # Verify status message
    mock_whatsapp.send_message.assert_called_with(
        SendMessageRequest(
            phone="user@s.whatsapp.net",
            message="You are currently opted in.",
            reply_message_id=None,
        )
    )
