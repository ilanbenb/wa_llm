import asyncio
import logging

from cachetools import TTLCache
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings
from handler.router import Router
from handler.whatsapp_group_link_spam import WhatsappGroupLinkSpamHandler
from handler.kb_qa import KBQAHandler
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler
from models import Message, OptOut

logger = logging.getLogger(__name__)

# In-memory processing guard: 4 minutes TTL to prevent duplicate handling
_processing_cache = TTLCache(maxsize=1000, ttl=4 * 60)
_processing_lock = asyncio.Lock()


class MessageHandler(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
        settings: Settings,
    ):
        self.router = Router(session, whatsapp, embedding_client, settings)
        self.whatsapp_group_link_spam = WhatsappGroupLinkSpamHandler(
            session, whatsapp, embedding_client, settings
        )
        self.kb_qa_handler = KBQAHandler(session, whatsapp, embedding_client, settings)
        self.settings = settings
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)

        # ignore messages that don't exist or don't have text
        if not message or not message.text:
            return

        # Ignore messages sent by the bot itself
        my_jid = await self.whatsapp.get_my_jid()
        if message.sender_jid == my_jid.normalize_str():
            return

        if message.sender_jid.endswith("@lid"):
            logging.info(
                f"Received message from {message.sender_jid}: {payload.model_dump_json()}"
            )

        # direct message
        if message and not message.group:
            command = message.text.strip().lower()
            if command == "opt-out":
                await self.handle_opt_out(message)
                return
            elif command == "opt-in":
                await self.handle_opt_in(message)
                return
            elif command == "status":
                await self.handle_opt_status(message)
                return
            # if autoreply is enabled, send autoreply
            elif self.settings.dm_autoreply_enabled:
                await self.send_message(
                    message.sender_jid,
                    self.settings.dm_autoreply_message,
                    message.message_id,
                )
            return

        # In-memory dedupe: if this message is already being processed/recently processed, skip
        if message and message.message_id:
            async with _processing_lock:
                if message.message_id in _processing_cache:
                    logging.info(
                        f"Message {message.message_id} already in processing cache; skipping."
                    )
                    return
                _processing_cache[message.message_id] = True

        # Check for /kb_qa command (super admin only)
        # This does not have to be a managed group
        if message.group and message.text.startswith("/kb_qa "):
            if message.chat_jid not in self.settings.qa_test_groups:
                logger.warning(
                    f"QA command attempted from non-whitelisted group: {message.chat_jid}"
                )
                return  # Silent failure
            # Check if sender is a QA tester
            if message.sender_jid not in self.settings.qa_testers:
                logger.warning(f"Unauthorized /kb_qa attempt from {message.sender_jid}")
                return  # Silent failure

            await self.kb_qa_handler(message)
            return

        # ignore messages from unmanaged groups
        if message and message.group and not message.group.managed:
            return

        mentioned = message.has_mentioned(my_jid)
        if mentioned:
            await self.router(message)
            return

        if (
            message.group
            and message.group.notify_on_spam
            and "https://chat.whatsapp.com/" in message.text
        ):
            await self.whatsapp_group_link_spam(message)
            return

    async def handle_opt_out(self, message: Message):
        opt_out = await self.session.get(OptOut, message.sender_jid)
        if not opt_out:
            opt_out = OptOut(jid=message.sender_jid)
            await self.upsert(opt_out)
            await self.send_message(
                message.chat_jid,
                "You have been opted out. You will no longer be tagged in summaries and answers.",
            )
        else:
            await self.send_message(
                message.chat_jid,
                "You are already opted out.",
            )

    async def handle_opt_in(self, message: Message):
        opt_out = await self.session.get(OptOut, message.sender_jid)
        if opt_out:
            await self.session.delete(opt_out)
            await self.session.commit()
            await self.send_message(
                message.chat_jid,
                "You have been opted in. You will now be tagged in summaries and answers.",
            )
        else:
            await self.send_message(
                message.chat_jid,
                "You are already opted in.",
            )

    async def handle_opt_status(self, message: Message):
        opt_out = await self.session.get(OptOut, message.sender_jid)
        status = "opted out" if opt_out else "opted in"
        await self.send_message(
            message.chat_jid,
            f"You are currently {status}.",
        )
