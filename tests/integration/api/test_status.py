from unittest.mock import AsyncMock, MagicMock
from app.main import app


def test_readiness(client):
    response = client.get("/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status_healthy(client):
    # Mock WhatsApp devices
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.device = 1

    mock_devices_response = MagicMock()
    mock_devices_response.results = [mock_device]
    app.state.whatsapp.get_devices.return_value = mock_devices_response

    # Mock DB connection and query
    mock_session = app.state.async_session.return_value.__aenter__.return_value
    print(f"DEBUG: type(mock_session)={type(mock_session)}")
    mock_conn = AsyncMock()
    mock_session.connection = AsyncMock(return_value=mock_conn)

    mock_result = MagicMock()
    mock_result.fetchone.return_value = (2,)
    mock_conn.execute.return_value = mock_result

    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["whatsapp"]["status"] == "healthy"
    assert data["checks"]["database"]["status"] == "healthy"
