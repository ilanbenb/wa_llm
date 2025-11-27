from typing import TYPE_CHECKING
from ..protocols import WhatsAppClientProtocol

from ..models import (
    UserInfoResponse,
    UserAvatarResponse,
    UserPrivacyResponse,
    GroupResponse,
    NewsletterResponse,
)

if TYPE_CHECKING:
    from ..base_client import BaseWhatsAppClient


class UserMixin(WhatsAppClientProtocol):
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
