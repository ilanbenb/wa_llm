from typing import List

from models import Message
from whatsapp.jid import parse_jid


def chat2text(history: List[Message], opt_out_map: dict[str, str]) -> str:
    lines = []
    for message in history:
        sender_jid = parse_jid(message.sender_jid)
        sender_user = sender_jid.user
        if sender_user in opt_out_map:
            sender_display = opt_out_map[sender_user]
        else:
            sender_display = f"@{sender_user}"

        lines.append(f"{message.timestamp}: {sender_display}: {message.text}")

    return "\n".join(lines)
