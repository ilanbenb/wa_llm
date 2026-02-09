from unittest.mock import AsyncMock

import pytest

from api import webhook as webhook_api
from gowa_sdk.webhooks import WebhookEnvelope


@pytest.mark.asyncio
async def test_webhook_calls_handler_for_message_event(monkeypatch: pytest.MonkeyPatch):
    payload = WebhookEnvelope.model_validate(
        {"event": "message", "payload": {"id": "m1"}}
    )
    handler = AsyncMock()
    whatsapp = AsyncMock()
    session = AsyncMock()
    gather_groups_mock = AsyncMock()
    monkeypatch.setattr(webhook_api, "gather_groups", gather_groups_mock)

    result = await webhook_api.webhook(payload, handler, session, whatsapp)

    assert result == "ok"
    handler.assert_awaited_once_with(payload)
    gather_groups_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_webhook_syncs_groups_for_group_participants_event(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = WebhookEnvelope.model_validate(
        {"event": "group.participants", "payload": {"chat_id": "120363@g.us"}}
    )
    handler = AsyncMock()
    whatsapp = AsyncMock()
    session = AsyncMock()
    gather_groups_mock = AsyncMock()
    monkeypatch.setattr(webhook_api, "gather_groups", gather_groups_mock)

    result = await webhook_api.webhook(payload, handler, session, whatsapp)

    assert result == "ok"
    handler.assert_not_awaited()
    gather_groups_mock.assert_awaited_once_with(session, whatsapp)


@pytest.mark.asyncio
async def test_webhook_syncs_groups_for_group_joined_event_case_insensitive(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = WebhookEnvelope.model_validate(
        {"event": "Group.Joined", "payload": {"chat_id": "120363@g.us"}}
    )
    handler = AsyncMock()
    whatsapp = AsyncMock()
    session = AsyncMock()
    gather_groups_mock = AsyncMock()
    monkeypatch.setattr(webhook_api, "gather_groups", gather_groups_mock)

    result = await webhook_api.webhook(payload, handler, session, whatsapp)

    assert result == "ok"
    handler.assert_not_awaited()
    gather_groups_mock.assert_awaited_once_with(session, whatsapp)
