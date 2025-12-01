# This handler is used to handle whatsapp group link spam

import logging
from .base_handler import BaseHandler
from pydantic_ai import Agent
from pydantic import BaseModel
from sqlmodel import Field
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings
from models import Message
from whatsapp import WhatsAppClient
from whatsapp.jid import parse_jid

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
            model=self.settings.model_name,
            system_prompt="""You are a spam whatsapp link spam detector. You are given a message and you need to return a score of 1-5 and a SHORT 7 words explanation of why you gave that score.
            """,
            output_type=self.SpamCheckResult,
            output_retries=3,
        )

        result = await agent.run(
            (
                f"@{parse_jid(message.sender_jid).user}:"
                f"{message.text}"
                f"The message is from a group chat. The group name is {message.group.group_name if message.group else 'Unknown'} and the group description is {message.group.group_topic if message.group else 'Unknown'}"
            )
        )

        spam_result = result.output

        if message and message.group and not message.group.owner_jid:
            raise ValueError("Group owner JID is required")

        # Construct message with validated data
        message_to_send = (
            f"@{message.group.owner_jid.split('@')[0]} - A Whatsapp group link was shared in the group. "  # type: ignore
            f"This might be a spam. Please check and remove if it is spam.\n\n"
            f"Spam Confidence Level: *{spam_result.score}*  (1 not spam - 5 spam) \n"
            f"Explanation: {spam_result.explanation}"
        )

        await self.send_message(
            message.chat_jid,
            message_to_send,
            # message.message_id,
        )
