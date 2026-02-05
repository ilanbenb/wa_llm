from __future__ import annotations

from typing import Optional

from ..models import (
    MessageSendResponse,
    SendAudioRequest,
    SendChatPresenceRequest,
    SendContactRequest,
    SendFileRequest,
    SendImageRequest,
    SendLinkRequest,
    SendLocationRequest,
    SendMessageRequest,
    SendPollRequest,
    SendPresenceRequest,
    SendStickerRequest,
    SendVideoRequest,
)
from ..protocols import GoWaClientProtocol


class SendMixin(GoWaClientProtocol):
    async def send_message(
        self, request: SendMessageRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post("/send/message", json=request, device_id=device_id)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_image(
        self,
        request: SendImageRequest,
        image: bytes,
        *,
        filename: str = "image.jpg",
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/image",
            data=request,
            files={"image": (filename, image)},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_audio(
        self,
        request: SendAudioRequest,
        audio: bytes,
        *,
        filename: str = "audio.ogg",
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/audio",
            data=request,
            files={"audio": (filename, audio)},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_file(
        self,
        request: SendFileRequest,
        file: bytes,
        *,
        filename: str = "file",
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/file",
            data=request,
            files={"file": (filename, file)},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_sticker(
        self,
        request: SendStickerRequest,
        sticker: bytes,
        *,
        filename: str = "sticker.webp",
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/sticker",
            data=request,
            files={"sticker": (filename, sticker)},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_video(
        self,
        request: SendVideoRequest,
        video: bytes,
        *,
        filename: str = "video.mp4",
        device_id: Optional[str] = None,
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/video",
            data=request,
            files={"video": (filename, video)},
            device_id=device_id,
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_contact(
        self, request: SendContactRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post("/send/contact", json=request, device_id=device_id)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_link(
        self, request: SendLinkRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post("/send/link", json=request, device_id=device_id)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_location(
        self, request: SendLocationRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post("/send/location", json=request, device_id=device_id)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_poll(
        self, request: SendPollRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post("/send/poll", json=request, device_id=device_id)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_presence(
        self, request: SendPresenceRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post("/send/presence", json=request, device_id=device_id)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_chat_presence(
        self, request: SendChatPresenceRequest, *, device_id: Optional[str] = None
    ) -> MessageSendResponse:
        response = await self._post(
            "/send/chat-presence", json=request, device_id=device_id
        )
        return MessageSendResponse.model_validate_json(response.content)
