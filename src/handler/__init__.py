from sqlmodel.ext.asyncio.session import AsyncSession

from handler.router import Router
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from voyageai.client_async import AsyncClient
from .base_handler import BaseHandler


class MessageHandler(BaseHandler):
    def __init__(self, session: AsyncSession, whatsapp: WhatsAppClient, embedding_client: AsyncClient):
        self.router = Router(session, whatsapp, embedding_client)
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)

        # ignore messages without text
        if not message.text:
            return

        if message.group and not message.group.managed:
            return

        if not message.has_mentioned(await self.whatsapp.get_my_jid()):
            return

        await self.router(message)
