import pytest
from datetime import datetime, timezone
from models.reaction import Reaction
from gowa_sdk.webhooks import WebhookEnvelope
from unittest.mock import AsyncMock, MagicMock


def test_reaction_normalization():
    reaction = Reaction.model_validate(
        {
            "message_id": "msg1",
            "sender_jid": "1234567890.1:1@s.whatsapp.net",
            "emoji": "👍",
        }
    )
    assert reaction.sender_jid == "1234567890@s.whatsapp.net"


def test_from_webhook():
    payload = WebhookEnvelope.model_validate(
        {
            "event": "message.reaction",
            "payload": {
                "id": "reaction_msg_id",
                "chat_id": "1234567890@s.whatsapp.net",
                "from": "1234567890@s.whatsapp.net",
                "from_name": "Test",
                "timestamp": datetime.now(timezone.utc),
                "reaction": "👍",
                "reacted_message_id": "msg1",
            },
        }
    )
    reaction = Reaction.from_webhook(payload)
    assert reaction.message_id == "msg1"
    assert reaction.sender_jid == "1234567890@s.whatsapp.net"
    assert reaction.emoji == "👍"


def test_from_webhook_in_group():
    payload = WebhookEnvelope.model_validate(
        {
            "event": "message.reaction",
            "payload": {
                "id": "reaction_msg_id",
                "chat_id": "group@g.us",
                "from": "1234567890@s.whatsapp.net",
                "from_name": "Test",
                "timestamp": datetime.now(timezone.utc),
                "reaction": "👍",
                "reacted_message_id": "msg1",
            },
        }
    )
    reaction = Reaction.from_webhook(payload)
    assert reaction.sender_jid == "1234567890@s.whatsapp.net"


@pytest.mark.asyncio
async def test_upsert_reaction():
    mock_session = AsyncMock()
    reaction = Reaction(message_id="msg1", sender_jid="sender1", emoji="👍")

    # Mock exec return for select
    mock_result = MagicMock()
    mock_result.first.return_value = reaction
    mock_session.exec.return_value = mock_result

    result = await Reaction.upsert_reaction(mock_session, reaction)

    assert result == reaction
    assert mock_session.exec.call_count == 2  # One for insert/upsert, one for select
