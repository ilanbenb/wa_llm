import logging
import httpx
import traceback
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.router import Router
from handler.whatsapp_group_link_spam import WhatsappGroupLinkSpamHandler
from models import (
    WhatsAppWebhookPayload,
    Message,
)
from utils.phone_mapper import phone_mapper
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

# Global variable to store access state
_bot_access_enabled = False

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
        print("=== MESSAGE HANDLER START ===")
        
        try:
            message = await self.store_message(payload)
            print(f"Message stored: {message is not None}")

            if (
                message
                and message.group
                and message.group.managed
                and message.group.forward_url
            ):
                await self.forward_message(payload, message.group.forward_url)

            # ignore messages that don't exist or don't have text
            if not message or not message.text:
                print("No message or no text - returning")
                return

            # Update global phone number database when messages come in
            await self.update_global_phone_database(message)

            # ignore messages from unmanaged groups
            # TEMPORARILY DISABLED FOR TESTING
            # if message and message.group and not message.group.managed:
            #     return

            # NEW FEATURE: Check for @כולם mentions (only for non-forwarded messages)
            if "@כולם" in message.text and not payload.forwarded:
                print("Found @כולם mention - tagging all participants")
                await self.tag_all_participants(message)
                return  # Exit early, don't process bot mentions

            print("Checking if bot was mentioned...")
            my_jid = await self.whatsapp.get_my_jid()
            
            # If bot was mentioned
            if message.has_mentioned(my_jid):
                print("Bot was mentioned!")
                
                global _bot_access_enabled

                # Admin command - check if message contains "allow"
                if message.sender_jid.startswith("972532741041") and "allow" in message.text.lower():
                    _bot_access_enabled = not _bot_access_enabled
                    await self.send_message(message.chat_jid, f"🔐 *מצב גישה:* {'מופעל' if _bot_access_enabled else 'מושבתת'}", message.message_id)
                    return
                
                # Simple access check - either access is enabled OR user is admin
                if _bot_access_enabled or message.sender_jid.startswith("972532741041"):
                    await self.router(message)
                else:
                    await self.send_message(message.chat_jid, "הלו גברתי אדוני, רק המק״ס יכול לדבר איתי", message.message_id)
            else:
                print("Bot was not mentioned")

            print("=== MESSAGE HANDLER END ===")

        except Exception as e:
            print(f"Error in message handler: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

    async def update_global_phone_database(self, message: Message):
        """Update the global phone number database when messages come in"""
        try:
            if message.sender_jid and '@' in message.sender_jid:
                phone = message.sender_jid.split('@')[0]
                jid = message.sender_jid
                
                # Store JID -> phone mapping
                phone_mapper.add_mapping(jid, phone)
                
        except Exception as e:
            logger.error(f"Error updating global phone database: {e}")

    async def tag_all_participants(self, message: Message):
        """Tag all participants in the group when @כולם is mentioned"""
        try:
            # Get bot's phone number to exclude it
            my_jid = await self.whatsapp.get_my_jid()
            bot_phone = my_jid.user
            
            # Get all groups and find this one
            groups_response = await self.whatsapp.get_user_groups()
            
            # Find the target group first
            target_group = next(
                (group for group in groups_response.results.data if group.JID == message.chat_jid),
                None
            )
            
            if target_group:
                # Tag everyone except the bot
                tagged_message = ""
                for participant in target_group.Participants:
                    # Use phone mapper to get phone number from JID
                    phone = phone_mapper.get_phone(participant.JID)
                    
                    # Only tag if we have a real phone number and it's not the bot
                    if phone and phone != bot_phone:
                        tagged_message += f"@{phone} "
                
                # Send either the tagged message or fallback
                response_text = tagged_message.strip() or "📢 כולם מוזמנים! 🎉"
                await self.send_message(message.chat_jid, response_text, message.message_id)
                return
                    
        except Exception as e:
            logger.error(f"Error tagging participants: {e}")
        
        # Fallback
        await self.send_message(message.chat_jid, "📢 כולם מוזמנים!", message.message_id)

    async def forward_message(
        self, payload: WhatsAppWebhookPayload, forward_url: str
    ) -> None:
        """Forward a message to the group's configured forward URL using HTTP POST."""
        if not forward_url:
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    forward_url,
                    json=payload.model_dump(mode="json"),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

        except httpx.HTTPError as exc:
            logger.error(f"Failed to forward message to {forward_url}: {exc}")
        except Exception as exc:
            logger.error(f"Unexpected error forwarding message to {forward_url}: {exc}")