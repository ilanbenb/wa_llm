from typing import TYPE_CHECKING
from ..protocols import WhatsAppClientProtocol

from ..models import (
    UnfollowNewsletterRequest,
    GenericResponse,
)

if TYPE_CHECKING:
    from ..base_client import BaseWhatsAppClient


class NewsletterMixin(WhatsAppClientProtocol):
    async def unfollow_newsletter(
        self, newsletter_id: str
    ) -> GenericResponse:
        response = await self._post(
            "/newsletter/unfollow",
            json=UnfollowNewsletterRequest(newsletter_id=newsletter_id),
        )
        return GenericResponse.model_validate_json(response.content)
