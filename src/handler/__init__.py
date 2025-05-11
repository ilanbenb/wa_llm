from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.router import Router
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler


class MessageHandler(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
    ):
        self.router = Router(session, whatsapp, embedding_client)
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)
        # ignore messages that don't exist or don't have text
        if not message or not message.text:
            return

        # ignore messages from unmanaged groups
        if message and message.group and not message.group.managed:
            return

        if not message.has_mentioned(await self.whatsapp.get_my_jid()):
            return

        await self.router(message)
