import pytest
from pytest_httpx import HTTPXMock
from whatsapp.client import WhatsAppClient
from gowa_sdk import ApiResponse


@pytest.fixture
def client():
    return WhatsAppClient(base_url="http://test-api")


@pytest.mark.asyncio
async def test_login(client: WhatsAppClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://test-api/app/login",
        json={
            "code": "200",
            "message": "Success",
            "results": {"qr_link": "test_qr", "qr_duration": 60},
        },
    )
    response = await client.login()
    assert isinstance(response, ApiResponse)
    assert response.code == "200"
    assert response.results is not None
    assert response.results.qr_link == "test_qr"


@pytest.mark.asyncio
async def test_get_user_info(client: WhatsAppClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://test-api/user/info?phone=1234567890",
        json={
            "code": "200",
            "message": "Success",
            "results": {
                "verified_name": "Test User",
                "status": "Hey there!",
                "picture_id": "http://pfp.url",
                "devices": [],
            },
        },
    )
    response = await client.get_user_info("1234567890")
    assert isinstance(response, ApiResponse)
    assert response.code == "200"
    assert response.results is not None
    assert response.results.verified_name == "Test User"


@pytest.mark.asyncio
async def test_send_message(client: WhatsAppClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://test-api/send/message",
        method="POST",
        json={
            "code": "200",
            "message": "Success",
            "results": {"message_id": "msg_123", "status": "SENT"},
        },
    )
    from gowa_sdk import SendMessageRequest

    request = SendMessageRequest(phone="1234567890", message="Hello")
    response = await client.send_message(request)
    assert isinstance(response, ApiResponse)
    assert response.code == "200"
    assert response.results is not None
    assert response.results.message_id == "msg_123"
