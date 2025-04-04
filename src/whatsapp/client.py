import base64
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from .jid import JID, parse_jid
from .models import (
    LoginResponse,
    LoginWithCodeResponse,
    GenericResponse,
    DeviceResponse,
    UserInfoResponse,
    UserAvatarResponse,
    UserPrivacyResponse,
    GroupResponse,
    NewsletterResponse,
    SendMessageRequest,
    MessageSendResponse,
    SendContactRequest,
    SendLinkRequest,
    SendLocationRequest,
    SendPollRequest,
    MessageActionRequest,
    CreateGroupRequest,
    ManageParticipantRequest,
    ManageParticipantResponse,
    JoinGroupRequest,
    LeaveGroupRequest,
    UnfollowNewsletterRequest,
    CreateGroupResponse,
)


class WhatsAppClient:
    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = httpx.Timeout(300.0),
    ):
        """
        Initialize WhatsApp Client

        Args:
            base_url: Base URL for the WhatsApp API
            username: Optional username for basic auth
            password: Optional password for basic auth
            timeout: Request timeout in seconds
        """
        # Validate and normalize base URL
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid base URL provided")
        self.base_url = base_url.rstrip("/")

        # Configure headers
        headers = {
            "Accept": "application/json",
        }

        # Add basic auth if credentials provided
        if username and password:
            auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()  # noqa
            headers["Authorization"] = f"Basic {auth_str}"

        # Initialize httpx client with configuration
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Internal GET request method

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = await self.client.get(path, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if response.content:
                exc.args = (
                    f"{exc.args[0]}. Response content: {response.text}",
                ) + exc.args[1:]
            raise
        return response

    async def _post(
        self,
        path: str,
        json: Optional[Dict[str, Any] | BaseModel] = None,
        data: Optional[Dict[str, Any] | BaseModel] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Internal POST request method

        Args:
            path: API endpoint path
            json: Optional JSON body
            data: Optional form data
            files: Optional files to upload

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If the request fails
        """
        headers = None
        if isinstance(json, BaseModel) or isinstance(data, BaseModel):
            data = (
                json.model_dump_json()
                if isinstance(json, BaseModel)
                else data.model_dump_json()
            )
            headers = {"Content-Type": "application/json"}
            json = None

        response = await self.client.post(
            path, json=json, data=data, files=files, headers=headers
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if response.content:
                exc.args = (
                    f"{exc.args[0]}. Response content: {response.text}",
                ) + exc.args[1:]
            raise
        return response

    # App Operations
    async def login(self) -> LoginResponse:
        """Login to WhatsApp and get QR code"""
        response = await self._get("/app/login")
        return LoginResponse.model_validate_json(response.content)

    async def login_with_code(self, phone: str) -> LoginWithCodeResponse:
        """Login with pairing code"""
        response = await self._get("/app/login-with-code", params={"phone": phone})
        return LoginWithCodeResponse.model_validate_json(response.content)

    async def logout(self) -> GenericResponse:
        """Logout and remove database"""
        response = await self._get("/app/logout")
        return GenericResponse.model_validate_json(response.content)

    async def reconnect(self) -> GenericResponse:
        """Reconnect to WhatsApp server"""
        response = await self._get("/app/reconnect")
        return GenericResponse.model_validate_json(response.content)

    async def get_devices(self) -> DeviceResponse:
        """Get list of connected devices"""
        response = await self._get("/app/devices")
        return DeviceResponse.model_validate_json(response.content)

    _jid: Optional[JID] = None

    async def get_my_jid(self) -> JID:
        if self._jid:
            return self._jid

        info = await self.get_devices()
        self._jid = parse_jid(info.results[0].device)
        return self._jid

    # User Operations
    async def get_user_info(self, phone: str) -> UserInfoResponse:
        response = await self._get("/user/info", params={"phone": phone})
        return UserInfoResponse.model_validate_json(response.content)

    async def get_user_avatar(
        self, phone: str, is_preview: bool = True
    ) -> UserAvatarResponse:
        response = await self._get(
            "/user/avatar", params={"phone": phone, "is_preview": is_preview}
        )
        return UserAvatarResponse.model_validate_json(response.content)

    async def get_user_privacy(self) -> UserPrivacyResponse:
        response = await self._get("/user/my/privacy")
        return UserPrivacyResponse.model_validate_json(response.content)

    async def get_user_groups(self) -> GroupResponse:
        response = await self._get("/user/my/groups")
        return GroupResponse.model_validate_json(response.content)

    async def get_user_newsletters(self) -> NewsletterResponse:
        response = await self._get("/user/my/newsletters")
        return NewsletterResponse.model_validate_json(response.content)

    # Send Operations
    async def send_message(self, request: SendMessageRequest) -> MessageSendResponse:
        response = await self._post("/send/message", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_image(
        self,
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

    async def send_audio(self, phone: str, audio: bytes) -> MessageSendResponse:
        response = await self._post(
            "/send/audio", data={"phone": phone}, files={"audio": audio}
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def send_file(
        self, phone: str, file: bytes, caption: Optional[str] = None
    ) -> MessageSendResponse:
        data = {"phone": phone}
        if caption:
            data["caption"] = caption

        response = await self._post("/send/file", data=data, files={"file": file})
        return MessageSendResponse.model_validate_json(response.content)

    async def send_video(
        self,
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

    async def send_contact(self, request: SendContactRequest) -> MessageSendResponse:
        response = await self._post("/send/contact", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_link(self, request: SendLinkRequest) -> MessageSendResponse:
        response = await self._post("/send/link", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_location(self, request: SendLocationRequest) -> MessageSendResponse:
        response = await self._post("/send/location", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    async def send_poll(self, request: SendPollRequest) -> MessageSendResponse:
        response = await self._post("/send/poll", json=request)
        return MessageSendResponse.model_validate_json(response.content)

    # Message Operations
    async def revoke_message(self, message_id: str, phone: str) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/revoke",
            json=MessageActionRequest(phone=phone),
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def delete_message(self, message_id: str, phone: str) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/delete",
            json=MessageActionRequest(phone=phone),
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def react_to_message(
        self, message_id: str, phone: str, emoji: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/reaction", json={"phone": phone, "emoji": emoji}
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def update_message(
        self, message_id: str, phone: str, message: str
    ) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/update", json={"phone": phone, "message": message}
        )
        return MessageSendResponse.model_validate_json(response.content)

    async def read_message(self, message_id: str, phone: str) -> MessageSendResponse:
        response = await self._post(
            f"/message/{message_id}/read", json=MessageActionRequest(phone=phone)
        )
        return MessageSendResponse.model_validate_json(response.content)

    # Group Operations
    async def create_group(self, request: CreateGroupRequest) -> CreateGroupResponse:
        response = await self._post("/group", json=request)
        return CreateGroupResponse.model_validate_json(response.content)

    async def add_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def remove_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/remove", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def promote_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/promote", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def demote_participants(
        self, request: ManageParticipantRequest
    ) -> ManageParticipantResponse:
        response = await self._post("/group/participants/demote", json=request)
        return ManageParticipantResponse.model_validate_json(response.content)

    async def join_group_with_link(self, link: str) -> GenericResponse:
        response = await self._post(
            "/group/join-with-link", json=JoinGroupRequest(link=link)
        )
        return GenericResponse.model_validate_json(response.content)

    async def leave_group(self, group_id: str) -> GenericResponse:
        response = await self._post(
            "/group/leave", json=LeaveGroupRequest(group_id=group_id)
        )
        return GenericResponse.model_validate_json(response.content)

    # Newsletter Operations
    async def unfollow_newsletter(self, newsletter_id: str) -> GenericResponse:
        response = await self._post(
            "/newsletter/unfollow",
            json=UnfollowNewsletterRequest(newsletter_id=newsletter_id),
        )
        return GenericResponse.model_validate_json(response.content)
