from datetime import datetime, timezone

import pytest

from models import Message
from models.webhook import WhatsAppWebhookPayload, ExtractedMedia
from test_utils.mock_session import mock_session  # noqa


@pytest.mark.asyncio
async def test_webhook_to_message():
    payload = WhatsAppWebhookPayload(
        from_="1234567890@s.whatsapp.net in 123456789-123456@g.us",
        timestamp=datetime.now(timezone.utc),
        pushname="Test User",
        message={
            "id": "test_message_id",
            "text": "Hello @bot how are you?",
            "replied_id": None,
        },
    )

    message = Message.from_webhook(payload)
    assert message.message_id == "test_message_id"
    assert message.text == "Hello @bot how are you?"
    assert message.sender_jid == "1234567890@s.whatsapp.net"
    assert message.group_jid == "123456789-123456@g.us"


@pytest.mark.asyncio
async def test_message_mentions(mock_session):
    message = Message(
        message_id="test_mention",
        text="Hey @1234567890 check this out",
        chat_jid="group@g.us",
        sender_jid="sender@s.whatsapp.net",
    )

    assert message.has_mentioned("1234567890")
    assert message.has_mentioned("1234567890@s.whatsapp.net")
    assert not message.has_mentioned("9876543210@s.whatsapp.net")


async def test_message_with_image(mock_session):
    # {'from': '972546610050:33@s.whatsapp.net in 972546610050@s.whatsapp.net',
    #  'image': {'media_path': 'statics/media/1739707428-82e94149-f7bf-4300-9621-70af93bda5a4.jpeg',
    #   'mime_type': 'image/jpeg',
    #   'caption': 'https://github.com/mongodb-developer/GenAI-Showcase\n\nMongoDB\nמשחררים Repository די מרשים של דוגמאות של agents ו-RAG.\n\n10,000 נקודות למי שמנחש באיזה DB הם משתמשים.'},
    #  'pushname': 'Ilan Benborhoum',
    #  'timestamp': '2025-02-16T12:03:48Z'}
    payload = WhatsAppWebhookPayload(
        from_="1234567890@s.whatsapp.net in 123456789-123456@g.us",
        timestamp=datetime.now(timezone.utc),
        pushname="Test User",
        image=ExtractedMedia(
            caption="This is an image",
            media_path="https://example.com/image.jpg",
            mime_type="image/jpeg",
        ),
    )

    message = Message.from_webhook(payload)
    assert message.text == "[[Attached Image]] This is an image"
