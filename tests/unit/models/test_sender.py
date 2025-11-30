import pytest
from models.sender import Sender


def test_sender_normalization():
    sender = Sender.model_validate({"jid": "1234567890.1:1@s.whatsapp.net"})
    assert sender.jid == "1234567890@s.whatsapp.net"
