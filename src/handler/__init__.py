import logging
import httpx

from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings
from handler.router import Router
from handler.whatsapp_group_link_spam import WhatsappGroupLinkSpamHandler
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

settings = Settings()

class MessageHandler(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
    ):
        self.router = Router(session, whatsapp, embedding_client)
        self.whatsapp_group_link_spam = WhatsappGroupLinkSpamHandler(
            session, whatsapp, embedding_client
        )
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)

        # forward messages to the group's configured forward URL
        if (
            message
            and message.group
            and message.group.managed
            and message.group.forward_url
        ):
            await self.forward_message(payload, message.group.forward_url)

        # ignore messages that don't exist or don't have text
        if not message or not message.text:
            return

        # autoreply to private messages
        if message and not message.group and settings.dm_autoreply_enabled:
            await self.send_message(
                message.sender_jid,
                settings.dm_autoreply_message,
                message.message_id,
            )
            return

        # ignore messages from unmanaged groups
        if message and message.group and not message.group.managed:
            return

        if message.has_mentioned(await self.whatsapp.get_my_jid()):
            await self.router(message)

        # Handle whatsapp links in group
        if (
            message.group
            and message.group.notify_on_spam
            and "https://chat.whatsapp.com/" in message.text
        ):
            await self.whatsapp_group_link_spam(message)

    async def forward_message(
        self, payload: WhatsAppWebhookPayload, forward_url: str
    ) -> None:
        """
        Forward a message to the group's configured forward URL using HTTP POST.

        :param payload: The WhatsApp webhook payload to forward
        :param forward_url: The URL to forward the message to
        """
        # Ensure we have a forward URL
        if not forward_url:
            return

        try:
            # Create an async HTTP client and forward the message
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    forward_url,
                    json=payload.model_dump_json(),  # Convert Pydantic model to dict for JSON serialization
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

        except httpx.HTTPError as exc:
            # Log the error but don't raise it to avoid breaking message processing
            logger.error(f"Failed to forward message to {forward_url}: {exc}")
        except Exception as exc:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error forwarding message to {forward_url}: {exc}")
