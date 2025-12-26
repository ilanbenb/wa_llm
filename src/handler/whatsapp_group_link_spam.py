# This handler is used to handle whatsapp group link spam

import logging
from .base_handler import BaseHandler
from pydantic_ai import Agent
from pydantic import BaseModel
from sqlmodel import Field, select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings
from models import Message
from whatsapp import WhatsAppClient
from whatsapp.jid import parse_jid
from services.prompt_manager import prompt_manager
from utils.model_factory import get_model

# Creating an object
logger = logging.getLogger(__name__)


class WhatsappGroupLinkSpamHandler(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
        settings: Settings,
    ):
        self.settings = settings
        super().__init__(session, whatsapp, embedding_client)

    class SpamCheckResult(BaseModel):
        score: int = Field(
            ge=1, le=5, description="Spam score from 1-5 1 is not spam, 5 is very hight"
        )
        explanation: str = Field(max_length=100, description="Short explanation")

    async def __call__(self, message: Message):
        agent = Agent(
            model=get_model(self.settings),
            system_prompt=prompt_manager.render("link_spam_detector.j2"),
            output_type=self.SpamCheckResult,
            output_retries=3,
        )

        last_messages_text = ""
        if message.group_jid:
            stmt = (
                select(Message)
                .where(Message.group_jid == message.group_jid)
                .order_by(desc(Message.timestamp))
                .limit(10)
            )
            result = await self.session.exec(stmt)
            last_messages = result.all()
            # Reverse to show in chronological order
            last_messages = reversed(last_messages)

            last_messages_text = "\n".join(
                [
                    f"@{parse_jid(msg.sender_jid).user}: {msg.text}"
                    for msg in last_messages
                    if msg.text
                ]
            )

        result = await agent.run(
            (
                f"@{parse_jid(message.sender_jid).user}:"
                f"{message.text}"
                f"The message is from a group chat. The group name is {message.group.group_name if message.group else 'Unknown'} and the group description is {message.group.group_topic if message.group else 'Unknown'}"
                f"These are the last 10 messages in the group for context:\n{last_messages_text}"
            )
        )
        spam_result = result.output

        assert message.group is not None, "Group is required"
        assert message.group.owner_jid is not None, "Group owner JID is required"

        # Construct message with validated data
        message_to_send = (
            f"@{message.group.owner_jid.split('@')[0]} - A Whatsapp group link was shared in the group."
            f"This might be a spam. Please check and remove if it is spam.\n\n"
            f"Spam Confidence Level: *{spam_result.score}*  (1 not spam - 5 spam) \n"
            f"Explanation: {spam_result.explanation}"
        )

        await self.send_message(
            message.chat_jid,
            message_to_send,
            # message.message_id,
        )
