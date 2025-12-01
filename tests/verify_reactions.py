import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.chat_text import chat2text
from models import Message, Reaction


def test_chat2text_reactions():
    print("Testing chat2text reactions...")

    # Mock message with no reactions
    msg1 = Message(
        message_id="1",
        chat_jid="123@g.us",
        sender_jid="123@s.whatsapp.net",
        text="Hello",
        timestamp=datetime.now(),
        reactions=[],
    )

    # Mock message with single reactions (all count 1)
    msg2 = Message(
        message_id="2",
        chat_jid="123@g.us",
        sender_jid="456@s.whatsapp.net",
        text="World",
        timestamp=datetime.now(),
        reactions=[
            Reaction(emoji="👍", sender_jid="111@s.whatsapp.net", message_id="2"),
            Reaction(emoji="❤️", sender_jid="222@s.whatsapp.net", message_id="2"),
        ],
    )

    # Mock message with multiple reactions (some count > 1)
    msg3 = Message(
        message_id="3",
        chat_jid="123@g.us",
        sender_jid="789@s.whatsapp.net",
        text="Python",
        timestamp=datetime.now(),
        reactions=[
            Reaction(emoji="👍", sender_jid="111@s.whatsapp.net", message_id="3"),
            Reaction(emoji="👍", sender_jid="222@s.whatsapp.net", message_id="3"),
            Reaction(emoji="🔥", sender_jid="333@s.whatsapp.net", message_id="3"),
        ],
    )

    opt_out_map = {}

    output = chat2text([msg1, msg2, msg3], opt_out_map)
    print("Output:\n" + output)

    # Verify msg1 (no reactions)
    assert "Hello" in output
    assert "Reactions:" not in output.split("\n")[0]

    # Verify msg2 (single counts)
    assert "World" in output
    assert "Reactions: 👍, ❤️" in output or "Reactions: ❤️, 👍" in output

    # Verify msg3 (multiple counts)
    assert "Python" in output
    assert "Reactions: 👍 2, 🔥 1" in output or "Reactions: 🔥 1, 👍 2" in output

    print("\n✅ All reaction tests passed!")


if __name__ == "__main__":
    test_chat2text_reactions()
