import asyncio
import logging

from cachetools import TTLCache
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings, get_settings
from handler.router import Router
from handler.whatsapp_group_link_spam import WhatsappGroupLinkSpamHandler
from handler.kb_qa import KBQAHandler
from models import (
    WhatsAppWebhookPayload,
)
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler
from models import Message, OptOut, Group
from summarize_and_send_to_groups import summarize_and_send_to_group
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# In-memory processing guard: 4 minutes TTL to prevent duplicate handling
_processing_cache = TTLCache(maxsize=1000, ttl=4 * 60)
_processing_lock = asyncio.Lock()

# Track groups currently being summarized to prevent duplicate triggers
_summary_in_progress: set[str] = set()

# Rate limiters
_settings = get_settings()
_user_rate_limiter = RateLimiter(_settings.rate_limit_user_messages, _settings.rate_limit_user_window_seconds)
_group_rate_limiter = RateLimiter(_settings.rate_limit_group_messages, _settings.rate_limit_group_window_seconds)



async def run_summary_task(settings, session_factory, whatsapp, group_jid):
    try:
        async with session_factory() as session:
            # Re-fetch group because it's a new session
            group = await session.get(Group, group_jid)
            if group:
                await summarize_and_send_to_group(settings, session, whatsapp, group)
    finally:
        # Always remove from in-progress set, even if summary fails
        _summary_in_progress.discard(group_jid)


class MessageHandler(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
        settings: Settings,
        session_factory=None,
    ):
        self.router = Router(session, whatsapp, embedding_client, settings)
        self.whatsapp_group_link_spam = WhatsappGroupLinkSpamHandler(
            session, whatsapp, embedding_client, settings
        )
        self.kb_qa_handler = KBQAHandler(session, whatsapp, embedding_client, settings)
        self.settings = settings
        self.session_factory = session_factory
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, payload: WhatsAppWebhookPayload):
        message = await self.store_message(payload)

        # ignore messages that don't exist or don't have text
        if not message or not message.text:
            return

        # Flush to ensure the message is visible for the count query
        await self.session.flush()

        # Update message count for auto-summary
        if message.group_jid:
            group = await self.session.get(Group, message.group_jid)
            if group and group.auto_summary_threshold and self.session_factory:
                # Skip if a summary is already in progress for this group
                if group.group_jid in _summary_in_progress:
                    logging.debug(f"Summary already in progress for {group.group_name}, skipping trigger check")
                else:
                    # Get bot JID to exclude bot messages from count
                    bot_jid = (await self.whatsapp.get_my_jid()).normalize_str()
                    
                    # Count messages since last summary (excluding bot messages)
                    # We use the DB count instead of a manual counter to avoid race conditions
                    query = select(func.count()).select_from(Message).where(
                        Message.group_jid == group.group_jid,
                        Message.timestamp > group.last_summary_sync,
                        Message.sender_jid != bot_jid
                    )
                    result = await self.session.exec(query)
                    count = result.one()
                    
                    logging.info(f"Group: {group.group_name} ({group.group_jid}) | DB Count: {count} | Threshold: {group.auto_summary_threshold}")

                    if count >= group.auto_summary_threshold:
                        logging.info(f"Triggering auto-summary for group {group.group_name}")
                        
                        # Mark as in-progress BEFORE spawning to prevent race conditions
                        _summary_in_progress.add(group.group_jid)
                        
                        asyncio.create_task(run_summary_task(
                            self.settings, self.session_factory, self.whatsapp, group.group_jid
                        ))

        # Ignore messages sent by the bot itself
        my_jid = await self.whatsapp.get_my_jid()
        print(f"Bot JID: {my_jid.normalize_str()}")
        if message.sender_jid == my_jid.normalize_str():
            return

        if message.sender_jid.endswith("@lid"):
            logging.info(
                f"Received message from {message.sender_jid}: {payload.model_dump_json()}"
            )

        # direct message
        if message and not message.group:
            logger.info(f"Processing DM from {message.sender_jid}. Autoreply enabled: {self.settings.dm_autoreply_enabled}")

            # Rate limit check for DMs
            if not _user_rate_limiter.is_allowed(message.sender_jid):
                logger.warning(f"Rate limit exceeded for user {message.sender_jid} in DM")
                return

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
                logger.info(f"Sending autoreply to {message.sender_jid}")
                await self.send_message(
                    message.sender_jid,
                    self.settings.dm_autoreply_message,
                    message.message_id,
                )
                return
            else:
                logger.info(f"Autoreply disabled, ignoring DM from {message.sender_jid}")
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
            logger.info(f"Ignoring message from unmanaged group: {message.group.group_name} ({message.group.group_jid})")
            return

        mentioned = message.has_mentioned(my_jid) or (not message.group)
        logger.info(f"Message text: '{message.text}' | Bot user: '{my_jid.user}' | Mentioned: {mentioned}")
        if mentioned:
            # Rate limit check for mentions
            # Only check user rate limit if it's a group (DMs are checked above)
            if message.group and not _user_rate_limiter.is_allowed(message.sender_jid):
                logger.warning(f"Rate limit exceeded for user {message.sender_jid} in group {message.group_jid}")
                return
            
            if message.group_jid and not _group_rate_limiter.is_allowed(message.group_jid):
                logger.warning(f"Rate limit exceeded for group {message.group_jid}")
                return

            logger.info("Bot was mentioned, routing message...")
            await self.router(message)
            return

        if (
            message.group
            and message.group.notify_on_spam
            and "https://chat.whatsapp.com/" in message.text
        ):
            await self.whatsapp_group_link_spam(message)
            return
        
        logger.info("Message not handled - no mention, not spam, not DM")

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
