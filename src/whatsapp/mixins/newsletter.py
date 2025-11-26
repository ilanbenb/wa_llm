from typing import TYPE_CHECKING

from ..models import (
    UnfollowNewsletterRequest,
    GenericResponse,
)

if TYPE_CHECKING:
    from ..base_client import BaseWhatsAppClient


class NewsletterMixin:
    async def unfollow_newsletter(
        self: "BaseWhatsAppClient", newsletter_id: str
    ) -> GenericResponse:
        response = await self._post(
            "/newsletter/unfollow",
            json=UnfollowNewsletterRequest(newsletter_id=newsletter_id),
        )
        return GenericResponse.model_validate_json(response.content)
