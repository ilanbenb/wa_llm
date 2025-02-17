from sqlmodel.ext.asyncio.session import AsyncSession

from handler.router import Router
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from voyageai.client_async import AsyncClient
from .base_handler import BaseHandler

class topicsLoader(BaseHandler):
    def __init__(self, session: AsyncSession, whatsapp: WhatsAppClient, embedding_client: AsyncClient):
        self.router = Router(session, whatsapp, embedding_client)
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        await self.router.load_topics()