from typing import TYPE_CHECKING, Optional

from ..models import (
    SendMessageRequest,
    MessageSendResponse,
    SendContactRequest,
    SendLinkRequest,
    SendLocationRequest,
    SendPollRequest,
    MessageActionRequest,
)

if TYPE_CHECKING:
    from ..base_client import BaseWhatsAppClient


class MessageMixin:
    async def send_message(
        self: "BaseWhatsAppClient", request: SendMessageRequest
    ) -> MessageSendResponse:
        response = await self._post("/send/message", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_image(
        self: "BaseWhatsAppClient",
        phone: str,
        image: bytes,
        caption: Optional[str] = None,
        view_once: bool = False,
        compress: bool = False,
    ) -> MessageSendResponse:
        files = {"image": image}
        data = {
            "phone": phone,
            "view_once": str(view_once).lower(),
            "compress": str(compress).lower(),
        }
        if caption:
            data["caption"] = caption

        response = await self._post("/send/image", data=data, files=files)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_audio(
        self: "BaseWhatsAppClient", phone: str, audio: bytes
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/audio", data={"phone": phone}, files={"audio": audio}
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_file(
        self: "BaseWhatsAppClient",
        phone: str,
        file: bytes,
        caption: Optional[str] = None,
    ) -> MessageSendResponse:
        data = {"phone": phone}
        if caption:
            data["caption"] = caption

        response = await self._post("/send/file", data=data, files={"file": file})
        return MessageSendResponse.model_validate_json(response.content)

    async def send_video(
        self: "BaseWhatsAppClient",
        phone: str,
        video: bytes,
        caption: Optional[str] = None,
        view_once: bool = False,
        compress: bool = False,
    ) -> MessageSendResponse:
        data = {
            "phone": phone,
            "view_once": str(view_once).lower(),
            "compress": str(compress).lower(),
        }
        if caption:
            data["caption"] = caption

        response = await self._post("/send/video", data=data, files={"video": video})
        return MessageSendResponse.model_validate_json(response.content)

    async def send_contact(
        self: "BaseWhatsAppClient", request: SendContactRequest
    ) -> MessageSendResponse:
        response = await self._post("/send/contact", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_link(
        self: "BaseWhatsAppClient", request: SendLinkRequest
    ) -> MessageSendResponse:
        response = await self._post("/send/link", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_location(
        self: "BaseWhatsAppClient", request: SendLocationRequest
    ) -> MessageSendResponse:
        response = await self._post("/send/location", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_poll(
        self: "BaseWhatsAppClient", request: SendPollRequest
    ) -> MessageSendResponse:
        response = await self._post("/send/poll", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    # Message Operations
    async def revoke_message(
        self: "BaseWhatsAppClient", message_id: str, phone: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/revoke",
            json=MessageActionRequest(phone=phone),
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def delete_message(
        self: "BaseWhatsAppClient", message_id: str, phone: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/delete",
            json=MessageActionRequest(phone=phone),
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def react_to_message(
        self: "BaseWhatsAppClient", message_id: str, phone: str, emoji: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/reaction", json={"phone": phone, "emoji": emoji}
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def update_message(
        self: "BaseWhatsAppClient", message_id: str, phone: str, message: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/update", json={"phone": phone, "message": message}
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def read_message(
        self: "BaseWhatsAppClient", message_id: str, phone: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/read", json=MessageActionRequest(phone=phone)
        )
        return MessageSendResponse.model_validate_json(response.content)
