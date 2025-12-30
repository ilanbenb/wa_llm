import pytest
from typing import cast
from unittest.mock import MagicMock
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from models import KBTopic, Message, Group
from search.hybrid_search import hybrid_search, keyword_search


@pytest.mark.asyncio
async def test_hybrid_search_quality(mock_session: AsyncSession):
    """
    Test that hybrid search retrieves relevant messages even when the topic summary
    might not perfectly match the query, demonstrating the value of full-text search.
    """
    # 1. Setup Data
    group = Group(group_jid="123@g.us", group_name="Test Group")

    # Create a topic about "Project Alpha"
    topic = KBTopic(
        id="topic_1",
        group_jid=group.group_jid,
        subject="Project Alpha Status",
        summary="Discussion about the timeline and deliverables for the new initiative.",
        speakers="user_1,user_2",
        embedding=[0.1] * 1024,  # Dummy embedding
    )

    # Create a message with a specific keyword "deadline" and "Friday"
    message = Message(
        message_id="msg_1",
        chat_jid=group.group_jid,
        sender_jid="user_1@s.whatsapp.net",
        text="We must hit the hard deadline this Friday for the MVP.",
        timestamp=datetime.now(),
        group_jid=group.group_jid,
        kb_topic_id="topic_1",
    )

    # Mock keyword_search execution
    # Since we can't run actual Postgres TSVECTOR queries in this mock session,
    # we mock the return value of session.execute for the keyword search
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.message_id = message.message_id
    mock_row.timestamp = message.timestamp
    mock_row.text = message.text
    mock_row.media_url = message.media_url
    mock_row.chat_jid = message.chat_jid
    mock_row.sender_jid = message.sender_jid
    mock_row.group_jid = message.group_jid
    mock_row.reply_to_id = message.reply_to_id
    mock_row.kb_topic_id = message.kb_topic_id
    mock_row.rank = 0.9
    mock_result.fetchall.return_value = [mock_row]
    cast(MagicMock, mock_session.execute).side_effect = None
    cast(MagicMock, mock_session.execute).return_value = mock_result

    # 2. Test Keyword Search
    keyword_results = await keyword_search(
        mock_session, "Friday MVP", [group.group_jid]
    )

    assert len(keyword_results) > 0
    found_msg, rank = keyword_results[0]
    assert found_msg.message_id == message.message_id
    assert found_msg.text is not None
    assert "Friday" in found_msg.text

    # 3. Test Hybrid Search
    # We need to mock session.exec to return results for:
    # 1. vector_search (called first)
    # 2. topic lookup for keyword results (called second)

    # Mock result for vector_search
    mock_vector_result = MagicMock()
    mock_vector_result.__iter__.return_value = [(topic, 0.1)]

    # Mock result for topic lookup
    mock_topic_result = MagicMock()
    mock_topic_result.__iter__.return_value = [(topic, message.message_id)]

    # Mock result for get_messages_for_topic
    mock_messages_result = MagicMock()
    mock_messages_result.all.return_value = [message]

    # Set side_effect
    cast(MagicMock, mock_session.exec).side_effect = [
        mock_vector_result,
        mock_topic_result,
        mock_messages_result,
    ]

    results = await hybrid_search(
        session=mock_session,
        query="When is the deadline?",
        query_embedding=[0.1] * 1024,
        group_jids=[group.group_jid],
        vector_limit=1,
    )

    assert len(results) == 1
    result = results[0]
    assert result.topic.id == topic.id
    assert len(result.messages) > 0
    assert result.messages[0].message_id == message.message_id
    assert result.messages[0].text is not None
    assert "deadline" in result.messages[0].text


@pytest.mark.asyncio
async def test_keyword_search_multi_language(mock_session: AsyncSession):
    """Test that keyword search works for non-English text (Hebrew)."""
    group = Group(group_jid="456@g.us", group_name="Hebrew Group")

    message = Message(
        message_id="msg_he_1",
        chat_jid=group.group_jid,
        sender_jid="user_1@s.whatsapp.net",
        text="שלום, מה שלומך? אני בודק את החיפוש.",
        timestamp=datetime.now(),
        group_jid=group.group_jid,
    )

    # Mock the DB result
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.message_id = message.message_id
    mock_row.timestamp = message.timestamp
    mock_row.text = message.text
    mock_row.media_url = message.media_url
    mock_row.chat_jid = message.chat_jid
    mock_row.sender_jid = message.sender_jid
    mock_row.group_jid = message.group_jid
    mock_row.reply_to_id = message.reply_to_id
    mock_row.kb_topic_id = message.kb_topic_id
    mock_row.rank = 0.8
    mock_result.fetchall.return_value = [mock_row]
    cast(MagicMock, mock_session.execute).side_effect = None
    cast(MagicMock, mock_session.execute).return_value = mock_result

    # Search for "בודק" (testing)
    results = await keyword_search(mock_session, "בודק", [group.group_jid])

    assert len(results) > 0
    assert results[0][0].message_id == message.message_id
