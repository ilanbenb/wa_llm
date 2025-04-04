from typing import List

from models import Message
from whatsapp.jid import parse_jid


def chat2text(history: List[Message]) -> str:
    return "\n".join(
        [
            f"{message.timestamp}: @{parse_jid(message.sender_jid).user}: {message.text}"
            for message in history
        ]
    )
