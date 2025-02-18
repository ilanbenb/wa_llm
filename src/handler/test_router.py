from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic_ai import Agent
from pydantic_ai.result import RunResult

from handler.router import Router, RouteEnum
from models import Message
from whatsapp import SendMessageRequest

from test_utils.mock_session import mock_session  # noqa
from voyageai.object.embeddings import EmbeddingsObject
from voyageai.api_resources.response import VoyageResponse


@pytest.fixture
def mock_whatsapp():
    client = AsyncMock()
    client.send_message = AsyncMock()
    client.get_my_jid = AsyncMock(return_value="bot@s.whatsapp.net")
    return client


@pytest.fixture
def mock_embedding_client():
    client = AsyncMock()
    client.embed = AsyncMock(
        return_value=EmbeddingsObject(
            response=VoyageResponse(
                embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]], usage={"total_tokens": 4}
            )
        )
    )
    return client


@pytest.fixture
def test_message():
    return Message(
        message_id="test_id",
        text="Hello bot!",
        chat_jid="user@s.whatsapp.net",
        sender_jid="user@s.whatsapp.net",
        timestamp=datetime.now(timezone.utc),
    )


def MockAgent(return_value: Any):
    mock = Mock()
    mock.run = AsyncMock(return_value=RunResult([], 0, return_value, None, None))
    return mock


@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping For now until I fix the mock..")
async def test_router_ask_question_route(
    mock_session, mock_whatsapp, mock_embedding_client, test_message, monkeypatch
):
    # Mock the Agent class
    mock_agent = MockAgent(RouteEnum.ask_question)

    monkeypatch.setattr(Agent, "__init__", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agent, "run", mock_agent.run)

    # Mock the Agent class for summarization
    mock_summarize_agent = MockAgent("cool response")

    # Set up mock response for send_message
    mock_whatsapp.send_message.return_value.results.message_id = "response_id"

    # Create router instance
    router = Router(mock_session, mock_whatsapp, mock_embedding_client)

    # Test the route
    await router(test_message)

    # Verify the message was sent
    mock_whatsapp.send_message.assert_called_once_with(
        SendMessageRequest(
            phone="user@s.whatsapp.net",
            message="cool response",
        )
    )


@pytest.mark.asyncio
async def test_router_summarize_route(
    mock_session, mock_whatsapp, mock_embedding_client, test_message, monkeypatch
):
    # Mock the Agent class for routing
    mock_route_agent = MockAgent(RouteEnum.summarize)

    # Mock the Agent class for summarization
    mock_summarize_agent = MockAgent("Summary of messages")

    # Setup agent mocks
    agents = {"route": mock_route_agent, "summarize": mock_summarize_agent}
    agent_counter = 0

    def mock_agent_init(*args, **kwargs):
        nonlocal agent_counter
        return None

    def mock_agent_run(*args, **kwargs):
        nonlocal agent_counter
        agent = list(agents.values())[agent_counter]
        agent_counter = (agent_counter + 1) % len(agents)
        return agent.run(*args, **kwargs)

    monkeypatch.setattr(Agent, "__init__", mock_agent_init)
    monkeypatch.setattr(Agent, "run", mock_agent_run)

    # Mock session.exec() for message history
    mock_exec = AsyncMock()
    mock_exec.all.return_value = [test_message]
    mock_session.exec.return_value = mock_exec

    # Set up mock response for send_message
    mock_whatsapp.send_message.return_value.results.message_id = "response_id"

    # Create router instance
    router = Router(mock_session, mock_whatsapp, mock_embedding_client)

    # Test the route
    await router(test_message)

    # Verify the summary was sent
    mock_whatsapp.send_message.assert_called_once_with(
        SendMessageRequest(
            phone="user@s.whatsapp.net",
            message="Summary of messages",
        )
    )


@pytest.mark.asyncio
async def test_router_other_route(
    mock_session, mock_whatsapp, mock_embedding_client, test_message, monkeypatch
):
    # Mock the Agent class
    mock_agent = MockAgent(RouteEnum.other)
    monkeypatch.setattr(Agent, "__init__", lambda *args, **kwargs: None)
    monkeypatch.setattr(Agent, "run", mock_agent.run)

    # Create router instance
    router = Router(mock_session, mock_whatsapp, mock_embedding_client)

    # Test the route
    await router(test_message)

    # Verify no message was sent
    mock_whatsapp.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_message(mock_session, mock_whatsapp, mock_embedding_client):
    # Set up mock response
    mock_whatsapp.send_message.return_value.results.message_id = "response_id"
    mock_session.get.return_value = None  # Simulate sender doesn't exist

    # Create router instance
    router = Router(mock_session, mock_whatsapp, mock_embedding_client)

    # Test sending a message
    await router.send_message("user@s.whatsapp.net", "Test message")

    # Verify the message was sent and stored
    mock_whatsapp.send_message.assert_called_once()
    mock_session.flush.assert_called()
