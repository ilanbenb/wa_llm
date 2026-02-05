from __future__ import annotations

from typing import Optional

from ..models import (
    ApiResponse,
    GroupResponse,
    NewsletterResponse,
    UserAvatarResponse,
    UserInfoResponse,
    UserPrivacyResponse,
)
from ..protocols import GoWaClientProtocol


class UserMixin(GoWaClientProtocol):
    async def get_user_info(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> UserInfoResponse:
        response = await self._get(
            "/user/info", params={"phone": phone}, device_id=device_id
        )
        return UserInfoResponse.model_validate_json(response.content)

    async def get_user_avatar(
        self, phone: str, *, is_preview: bool = True, device_id: Optional[str] = None
    ) -> UserAvatarResponse:
        response = await self._get(
            "/user/avatar",
            params={"phone": phone, "is_preview": is_preview},
            device_id=device_id,
        )
        return UserAvatarResponse.model_validate_json(response.content)

    async def set_user_avatar(
        self,
        image: bytes,
        *,
        filename: str = "avatar.jpg",
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._post(
            "/user/avatar",
            files={"image": (filename, image)},
            device_id=device_id,
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def update_pushname(
        self, pushname: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._post(
            "/user/pushname", json={"pushname": pushname}, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def get_user_privacy(
        self, *, device_id: Optional[str] = None
    ) -> UserPrivacyResponse:
        response = await self._get("/user/my/privacy", device_id=device_id)
        return UserPrivacyResponse.model_validate_json(response.content)

    async def get_user_groups(
        self, *, device_id: Optional[str] = None
    ) -> GroupResponse:
        response = await self._get("/user/my/groups", device_id=device_id)
        return GroupResponse.model_validate_json(response.content)

    async def get_user_newsletters(
        self, *, device_id: Optional[str] = None
    ) -> NewsletterResponse:
        response = await self._get("/user/my/newsletters", device_id=device_id)
        return NewsletterResponse.model_validate_json(response.content)

    async def get_user_contacts(
        self, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get("/user/my/contacts", device_id=device_id)
        return ApiResponse[dict].model_validate_json(response.content)

    async def check_user(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get(
            "/user/check", params={"phone": phone}, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def get_business_profile(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get(
            "/user/business-profile", params={"phone": phone}, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)
