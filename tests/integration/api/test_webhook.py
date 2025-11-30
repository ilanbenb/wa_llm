from api.deps import get_handler
from app.main import app
from unittest.mock import AsyncMock


def test_webhook_post(client):
    # Test webhook event (POST)
    payload = {
        "from": "1234567890@s.whatsapp.net",
        "timestamp": "2024-01-29T12:00:00Z",
        "pushname": "Test User",
        "message": {"id": "123456", "text": "Hello"},
    }

    # Mock the handler
    mock_handler = AsyncMock()
    app.dependency_overrides[get_handler] = lambda: mock_handler

    try:
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == "ok"
        mock_handler.assert_called_once()
    finally:
        app.dependency_overrides = {}
