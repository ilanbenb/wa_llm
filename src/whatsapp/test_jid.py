import pytest

from whatsapp.jid import (
    JID,
    JIDParseError,
    new_ad_jid,
    normalize_jid,
    parse_jid,
)


def test_jid_creation():
    jid = JID(user="1234567890", server="s.whatsapp.net")
    assert str(jid) == "1234567890@s.whatsapp.net"
    assert not jid.is_empty()
    assert not jid.is_group()
    assert not jid.is_broadcast_list()


def test_ad_jid_creation():
    jid = new_ad_jid("1234567890", 1, 1)
    assert str(jid) == "1234567890.1:1@s.whatsapp.net"
    assert jid.ad
    assert jid.agent == 1
    assert jid.device == 1


def test_parse_jid():
    # Test normal JID parsing
    jid = parse_jid("1234567890@s.whatsapp.net")
    assert jid.user == "1234567890"
    assert jid.server == "s.whatsapp.net"

    # Test AD JID parsing
    jid = parse_jid("1234567890.1:1@s.whatsapp.net")
    assert jid.user == "1234567890"
    assert jid.agent == 1
    assert jid.device == 1
    assert jid.ad

    # Test group JID parsing
    jid = parse_jid("123456789-123456@g.us")
    assert jid.user == "123456789-123456"
    assert jid.server == "g.us"
    assert jid.is_group()


def test_normalize_jid():
    # Test string normalization
    assert normalize_jid("1234567890.1:1@s.whatsapp.net") == "1234567890@s.whatsapp.net"
    assert normalize_jid("1234567890@s.whatsapp.net") == "1234567890@s.whatsapp.net"

    # Test JID object normalization
    jid = new_ad_jid("1234567890", 1, 1)
    assert normalize_jid(jid) == "1234567890@s.whatsapp.net"


def test_invalid_jid():
    with pytest.raises(JIDParseError):
        parse_jid("invalid")

    with pytest.raises(JIDParseError):
        parse_jid("1234567890.abc:1@s.whatsapp.net")

    with pytest.raises(JIDParseError):
        parse_jid("1234567890.1:abc@s.whatsapp.net")
