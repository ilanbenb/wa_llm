import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from models import (
    WhatsAppWebhookPayload,
    BaseGroup,
    BaseSender,
    Message,
    Sender,
    Group,
    BaseMessage,
    Reaction,
    BaseReaction,
    upsert,
)
from whatsapp import WhatsAppClient, SendMessageRequest
from whatsapp.jid import normalize_jid

logger = logging.getLogger(__name__)


class BaseHandler:
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
    ):
        self.session = session
        self.whatsapp = whatsapp
        self.embedding_client = embedding_client

    async def store_message(
        self,
        message: Message | BaseMessage | WhatsAppWebhookPayload,
        sender_pushname: str | None = None,
    ) -> Message | None:
        """
        Store a message or reaction in the database
        :param message:  Message to store - can be a Message, BaseMessage or WhatsAppWebhookPayload
        :param sender_pushname:  Pushname of the sender [Optional]
        :return: The stored message, or None if a reaction was stored
        """
        # Handle webhook payload - could be message or reaction
        if isinstance(message, WhatsAppWebhookPayload):
            sender_pushname = message.pushname
            
            # Check if this is a reaction payload
            if message.reaction:
                await self.store_reaction(message)
                return None  # Reaction stored, no message to return
            
            # Otherwise, treat as regular message
            message = Message.from_webhook(message)
        
        if isinstance(message, BaseMessage):
            message = Message(**message.model_dump())

        if not message.text:
            return message  # Don't store messages without text

        async with self.session.begin_nested():
            # Ensure sender exists and is committed
            sender = await self.session.get(Sender, message.sender_jid)
            if sender is None:
                sender = Sender(
                    **BaseSender(
                        jid=message.sender_jid,  # Use normalized JID from message
                        push_name=sender_pushname,
                    ).model_dump()
                )
                await self.upsert(sender)
                await (
                    self.session.flush()
                )  # Ensure sender is visible in this transaction

            if message.group_jid:
                group = await self.session.get(Group, message.group_jid)
                if group is None:
                    group = Group(**BaseGroup(group_jid=message.group_jid).model_dump())
                    await self.upsert(group)
                    await self.session.flush()

            # Finally add the message
            stored_message = await self.upsert(message)
            return stored_message if isinstance(stored_message, Message) else message

    async def store_reaction(self, payload: WhatsAppWebhookPayload) -> Reaction | None:
        """
        Store a reaction from a WhatsApp webhook payload
        :param payload: WhatsApp webhook payload containing reaction data
        :return: The stored reaction, or None if failed
        """
        if not payload.reaction:
            logger.warning("No reaction found in webhook payload")
            return None
            
        try:
            # Create reaction from webhook payload
            reaction = Reaction.from_webhook(payload)
            
            async with self.session.begin_nested():
                # Ensure sender exists
                sender = await self.session.get(Sender, reaction.sender_jid)
                if sender is None:
                    sender = Sender(
                        **BaseSender(
                            jid=reaction.sender_jid,
                            push_name=payload.pushname,
                        ).model_dump()
                    )
                    await self.upsert(sender)
                    await self.session.flush()
                
                # Ensure the message being reacted to exists
                message = await self.session.get(Message, reaction.message_id)
                if message is None:
                    logger.warning(f"Message {reaction.message_id} not found for reaction")
                    # We could still store the reaction, but log it as orphaned
                    # return None  # Uncomment to skip storing orphaned reactions
                
                # Use custom upsert method for reactions
                stored_reaction = await Reaction.upsert_reaction(self.session, reaction)
                logger.info(f"Stored/updated reaction from {reaction.sender_jid} on message {reaction.message_id}")
                return stored_reaction
                    
        except Exception as e:
            logger.error(f"Error storing reaction: {e}")
            return None

    async def remove_reaction(self, message_id: str, sender_jid: str) -> bool:
        """
        Remove a reaction from a message
        :param message_id: ID of the message
        :param sender_jid: JID of the sender who made the reaction
        :return: True if reaction was removed, False if not found
        """
        try:
            from sqlmodel import select
            
            async with self.session.begin_nested():
                # Find the reaction to remove
                result = await self.session.exec(
                    select(Reaction).where(
                        Reaction.message_id == message_id,
                        Reaction.sender_jid == normalize_jid(sender_jid)
                    )
                )
                
                reaction = result.first()
                if reaction:
                    await self.session.delete(reaction)
                    await self.session.flush()
                    logger.info(f"Removed reaction from {sender_jid} on message {message_id}")
                    return True
                else:
                    logger.warning(f"No reaction found from {sender_jid} on message {message_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing reaction: {e}")
            return False

    async def send_message(
        self, to_jid: str, message: str, in_reply_to: str | None = None
    ) -> Message:
        """
        Send a message to a JID over WhatsApp, and store the message in the database
        :param to_jid: The JID to send the message to
        :param message: The message text to send
        :param in_reply_to: The JID of the message to reply to [Optional]
        :return: The stored message
        """
        assert to_jid, "to_jid is required"
        assert message, "message is required"
        to_jid = normalize_jid(to_jid)

        resp = await self.whatsapp.send_message(
            SendMessageRequest(
                phone=to_jid,
                message=message,
                reply_message_id=in_reply_to,
            )
        )
        assert resp.results, "Failed to send message"
        my_number = await self.whatsapp.get_my_jid()
        new_message = BaseMessage(
            message_id=resp.results.message_id if resp.results else "unknown",
            text=message,
            sender_jid=str(my_number),
            chat_jid=to_jid,
            reply_to_id=in_reply_to,
        )
        stored_message = await self.store_message(Message(**new_message.model_dump()))
        assert stored_message, "Failed to store message"
        return stored_message

    async def upsert(self, model):
        return await upsert(self.session, model)
