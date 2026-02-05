from __future__ import annotations

from typing import Optional

from ..models import GenericResponse, UnfollowNewsletterRequest
from ..protocols import GoWaClientProtocol


class NewsletterMixin(GoWaClientProtocol):
    async def unfollow_newsletter(
        self, newsletter_id: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        response = await self._post(
            "/newsletter/unfollow",
            json=UnfollowNewsletterRequest(newsletter_id=newsletter_id),
            device_id=device_id,
        )
        return GenericResponse.model_validate_json(response.content)
