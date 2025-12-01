from datetime import datetime

from models import Message
from utils.chat_text import chat2text


def test_chat2text_no_opt_out():
    messages = [
        Message(
            message_id="1",
            chat_jid="123@g.us",
            sender_jid="123456789@s.whatsapp.net",
            text="Hello",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
        )
    ]
    result = chat2text(messages, {})
    assert result == "2023-01-01 12:00:00: @123456789: Hello"


def test_chat2text_with_opt_out_name():
    messages = [
        Message(
            message_id="1",
            chat_jid="123@g.us",
            sender_jid="123456789@s.whatsapp.net",
            text="Hello",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
        )
    ]
    opt_out_map = {"123456789": "John Doe"}
    result = chat2text(messages, opt_out_map)
    assert result == "2023-01-01 12:00:00: John Doe: Hello"


def test_chat2text_with_opt_out_no_name():
    messages = [
        Message(
            message_id="1",
            chat_jid="123@g.us",
            sender_jid="123456789@s.whatsapp.net",
            text="Hello",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
        )
    ]
    opt_out_map = {"123456789": "123 456789"}
    result = chat2text(messages, opt_out_map)
    assert result == "2023-01-01 12:00:00: 123 456789: Hello"


def test_chat2text_mixed():
    messages = [
        Message(
            message_id="1",
            chat_jid="123@g.us",
            sender_jid="123456789@s.whatsapp.net",
            text="Hello",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
        ),
        Message(
            message_id="2",
            chat_jid="123@g.us",
            sender_jid="987654321@s.whatsapp.net",
            text="Hi",
            timestamp=datetime(2023, 1, 1, 12, 1, 0),
        ),
    ]
    opt_out_map = {"123456789": "John Doe"}
    result = chat2text(messages, opt_out_map)
    expected = (
        "2023-01-01 12:00:00: John Doe: Hello\n2023-01-01 12:01:00: @987654321: Hi"
    )
    assert result == expected
