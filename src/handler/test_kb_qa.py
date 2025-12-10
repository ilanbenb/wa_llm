from unittest.mock import AsyncMock, Mock, patch

import pytest

from handler.kb_qa import KBQAHandler
from models import Message, Group
from whatsapp import SendMessageRequest
from whatsapp.jid import JID

from config import Settings


@pytest.fixture
def mock_whatsapp():
    client = AsyncMock()
    # Mock the return value of send_message to match expected structure
    mock_response = AsyncMock()
    mock_response.results.message_id = "mock_msg_id"
    client.send_message = AsyncMock(return_value=mock_response)

    client.get_my_jid = AsyncMock(return_value=JID(user="bot", server="s.whatsapp.net"))
    return client


@pytest.fixture
def mock_embedding_client():
    client = AsyncMock()
    return client


@pytest.fixture
def mock_settings():
    return Mock(
        spec=Settings,
        qa_test_groups={"allowed@g.us"},
        qa_testers={"tester@s.whatsapp.net"},
        model_name="test-model",
    )


@pytest.fixture
def test_message():
    return Message(
        message_id="test_id",
        text="/kb_qa group: target_group, question: query",
        chat_jid="allowed@g.us",
        sender_jid="tester@s.whatsapp.net",
        timestamp=Mock(),
    )


@pytest.mark.asyncio
async def test_kb_qa_handler_success(
    mock_session,
    mock_whatsapp,
    mock_embedding_client,
    test_message,
    mock_settings,
):
    # Mock group search result
    mock_group = Group(group_jid="target@g.us", group_name="target_group", managed=True)

    mock_result = Mock()
    mock_result.all.return_value = [mock_group]
    mock_session.exec.side_effect = None  # Clear the side_effect from AsyncSessionMock
    mock_session.exec.return_value = mock_result

    # Mock KnowledgeBaseAnswers
    with patch("handler.kb_qa.KnowledgeBaseAnswers") as MockKB:
        mock_kb_instance = AsyncMock()
        MockKB.return_value = mock_kb_instance

        handler = KBQAHandler(
            mock_session, mock_whatsapp, mock_embedding_client, mock_settings
        )
        await handler(test_message)

        # Verify KnowledgeBaseAnswers was called with correct synthetic message
        mock_kb_instance.assert_called_once()
        call_args = mock_kb_instance.call_args[0][0]
        assert isinstance(call_args, Message)
        assert call_args.text == "query"
        assert call_args.group_jid == "target@g.us"
        assert call_args.chat_jid == "allowed@g.us"


@pytest.mark.asyncio
async def test_kb_qa_handler_unauthorized_group(
    mock_session,
    mock_whatsapp,
    mock_embedding_client,
    test_message,
    mock_settings,
):
    test_message.chat_jid = "not_allowed@g.us"

    handler = KBQAHandler(
        mock_session, mock_whatsapp, mock_embedding_client, mock_settings
    )

    with patch("handler.kb_qa.logger") as mock_logger:
        await handler(test_message)
        mock_logger.warning.assert_called_with(
            "QA command attempted from non-whitelisted group: not_allowed@g.us"
        )


@pytest.mark.asyncio
async def test_kb_qa_handler_unauthorized_user(
    mock_session,
    mock_whatsapp,
    mock_embedding_client,
    test_message,
    mock_settings,
):
    test_message.sender_jid = "stranger@s.whatsapp.net"

    handler = KBQAHandler(
        mock_session, mock_whatsapp, mock_embedding_client, mock_settings
    )

    with patch("handler.kb_qa.logger") as mock_logger:
        await handler(test_message)
        mock_logger.warning.assert_called_with(
            "Unauthorized /kb_qa attempt from stranger@s.whatsapp.net"
        )


@pytest.mark.asyncio
async def test_kb_qa_handler_group_not_found(
    mock_session,
    mock_whatsapp,
    mock_embedding_client,
    test_message,
    mock_settings,
):
    # Mock no groups found
    mock_result = Mock()
    mock_result.all.return_value = []
    mock_session.exec.side_effect = None  # Clear the side_effect from AsyncSessionMock
    mock_session.exec.return_value = mock_result

    with patch("handler.kb_qa.KnowledgeBaseAnswers"):
        handler = KBQAHandler(
            mock_session, mock_whatsapp, mock_embedding_client, mock_settings
        )
        await handler(test_message)

        mock_whatsapp.send_message.assert_called_with(
            SendMessageRequest(
                phone="allowed@g.us",
                message="No group found matching 'target_group'",
                reply_message_id=None,
            )
        )
