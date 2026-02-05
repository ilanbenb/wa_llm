from __future__ import annotations

from typing import Optional

from ..models import MessageActionRequest, MessageSendResponse
from ..protocols import GoWaClientProtocol


class MessageMixin(GoWaClientProtocol):
    async def revoke_message(
        self, message_id: str, phone: str, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/revoke",
            json=MessageActionRequest(phone=phone),
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def delete_message(
        self, message_id: str, phone: str, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/delete",
            json=MessageActionRequest(phone=phone),
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def react_to_message(
        self,
        message_id: str,
        phone: str,
        emoji: str,
        *,
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/reaction",
            json={"phone": phone, "emoji": emoji},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def update_message(
        self,
        message_id: str,
        phone: str,
        message: str,
        *,
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/update",
            json={"phone": phone, "message": message},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def read_message(
        self, message_id: str, phone: str, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/read",
            json=MessageActionRequest(phone=phone),
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def star_message(
        self, message_id: str, phone: str, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/star",
            json=MessageActionRequest(phone=phone),
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def unstar_message(
        self, message_id: str, phone: str, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/unstar",
            json=MessageActionRequest(phone=phone),
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def download_message_media(
        self, message_id: str, *, device_id: Optional[str] = None
    ) -> bytes:
        response = await self._get(
            f"/message/{message_id}/download", device_id=device_id
        )
        return response.content
