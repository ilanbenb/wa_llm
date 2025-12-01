import pytest
from models.group import Group
from unittest.mock import AsyncMock, MagicMock


def test_group_normalization():
    group = Group(group_jid="123456789-123456@g.us")
    assert group.group_jid == "123456789-123456@g.us"

    # Test normalization via field validator (if applicable during init)
    # The validator is on the class, so we can test it directly or via init if pydantic validates
    # Pydantic validation happens on init
    # Test with model_validate
    group_validated = Group.model_validate(
        {
            "group_jid": "123456789-123456@g.us",
            "owner_jid": "1234567890.1:1@s.whatsapp.net",
        }
    )
    assert group_validated.owner_jid == "1234567890@s.whatsapp.net"


@pytest.mark.asyncio
async def test_get_related_community_groups():
    group = Group(group_jid="g1@g.us", community_keys=["key1"])
    mock_session = AsyncMock()

    # Mock result
    mock_result = MagicMock()
    mock_result.all.return_value = [Group(group_jid="g2@g.us")]
    mock_session.exec.return_value = mock_result

    related = await group.get_related_community_groups(mock_session)
    assert len(related) == 1
    assert related[0].group_jid == "g2@g.us"
    mock_session.exec.assert_called_once()


@pytest.mark.asyncio
async def test_get_related_community_groups_no_keys():
    group = Group(group_jid="g1@g.us", community_keys=[])
    mock_session = AsyncMock()

    related = await group.get_related_community_groups(mock_session)
    assert related == []
    mock_session.exec.assert_not_called()
