from collections import Counter
from typing import List

from models import Message, Reaction
from whatsapp.jid import parse_jid


# If no reactions, don't display anything.
# Group Reactions by count per reaction. E.g: "👍 5, 👎 2"
# If all reactions has only one count, don't need to display number. E.G: "👍, 👎, 😁"
def render_reactions(reactions: List[Reaction]) -> str:
    if not reactions:
        return ""

    counts = Counter(r.emoji for r in reactions)
    if all(count == 1 for count in counts.values()):
        return f"Reactions: {', '.join(counts.keys())}"

    return (
        f"Reactions: {', '.join(f'{emoji} {count}' for emoji, count in counts.items())}"
    )


def chat2text(history: List[Message], opt_out_map: dict[str, str]) -> str:
    lines = []
    for message in history:
        sender_jid = parse_jid(message.sender_jid)
        sender_user = sender_jid.user
        if sender_user in opt_out_map:
            sender_display = opt_out_map[sender_user]
        else:
            sender_display = f"@{sender_user}"

        reaction_text = render_reactions(message.reactions)
        if reaction_text:
            lines.append(
                f"{message.timestamp}: {sender_display}: {message.text}. {reaction_text}"
            )
        else:
            lines.append(f"{message.timestamp}: {sender_display}: {message.text}")

    return "\n".join(lines)
