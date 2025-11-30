from unittest.mock import AsyncMock, patch, MagicMock
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from handler.router import Intent, IntentEnum


def test_full_flow_ask_question(client):
    # Mock Agent.run to avoid LLM calls
    # We need to mock multiple agents: Router, Rephraser, Generator

    # Mock Router Agent
    mock_router_result = AgentRunResult(output=Intent(intent=IntentEnum.ask_question))

    # Mock Rephraser Agent
    mock_rephraser_result = AgentRunResult(output="Rephrased question")

    # Mock Generator Agent
    mock_generator_result = AgentRunResult(output="Generated answer")

    # We can use side_effect to return different results based on the agent instance or call count
    # But since Agent is instantiated inside Router, it's hard to target specific instances easily without more complex mocking.
    # A simpler approach is to mock Agent.run to return results in sequence.

    with patch("pydantic_ai.Agent.run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            mock_router_result,  # 1. Router
            mock_rephraser_result,  # 2. Rephraser
            mock_generator_result,  # 3. Generator
        ]

        payload = {
            "from": "1234567890@s.whatsapp.net",
            "timestamp": "2024-01-29T12:00:00Z",
            "pushname": "Test User",
            "message": {"id": "123456", "text": "Hello @bot"},
        }

        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == "ok"

        # Verify Agent.run was called 3 times
        assert mock_run.call_count == 3
