import logging
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.knowledge_base_answers import KnowledgeBaseAnswers
from models import Message
from whatsapp.jid import parse_jid
from utils.chat_text import chat2text
from whatsapp import WhatsAppClient
from .base_handler import BaseHandler

# Creating an object
logger = logging.getLogger(__name__)


class IntentEnum(str, Enum):
    summarize = "summarize"
    ask_question = "ask_question"
    about = "about"
    other = "other"


class Intent(BaseModel):
    intent: IntentEnum = Field(
        description="""The intent of the message.
- summarize: The user wants to summarize the chat messages, or to catch up on the chat messages. This will trigger the summarization of the chat messages.
- ask_question: The user wants to ask a question or learn from the collective knowledge of the group. This will trigger the knowledge base to answer the question.
- about: The user wants to know more about the bot and its capabilities. This will trigger the about section.
- other: the user wants to do something else. This will trigger the default response."""
    )


class Router(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
    ):
        self.ask_knowledge_base = KnowledgeBaseAnswers(
            session, whatsapp, embedding_client
        )
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, message: Message):
        route = await self._route(message.text)
        match route:
            case IntentEnum.summarize:
                await self.summarize(message)
            case IntentEnum.ask_question:
                await self.ask_knowledge_base(message)
            case IntentEnum.about:
                await self.about(message)
            case IntentEnum.other:
                await self.default_response(message)

    async def _route(self, message: str) -> IntentEnum:
        agent = Agent(
            model="anthropic:claude-3-7-sonnet-latest",
            system_prompt="What is the intent of the message? What does the user want us to help with?",
            result_type=Intent,
        )

        result = await agent.run(message)
        return result.data.intent

    async def summarize(self, message: Message):
        time_24_hours_ago = datetime.now() - timedelta(hours=24)
        stmt = (
            select(Message)
            .where(Message.chat_jid == message.chat_jid)
            .where(Message.timestamp >= time_24_hours_ago)
            .order_by(desc(Message.timestamp))
            .limit(30)
        )
        res = await self.session.exec(stmt)
        messages: list[Message] = res.all()

        agent = Agent(
            model="anthropic:claude-3-7-sonnet-latest",
            system_prompt="""Summarize the following group chat messages in a few words.
            
            - You MUST state that this is a summary of TODAY's messages. even if the user asked for a summary of a different time period (in this case, also state this you can only do today's summary)
            - Always personalize the summary to user request
            - Keep it short and conversational
            - Tag users when mentioning them
            - Write in the same language as the request
            """,
            result_type=str,
        )

        # TODO: format messages in a way that is easy for the LLM to read
        response = await agent.run(
            f"@{parse_jid(message.sender_jid).user}: {message.text}\n\n # History:\n {chat2text(messages)}"
        )
        await self.send_message(message.chat_jid, response.data, message.message_id,)

    async def about(self, message):
        await self.send_message(
            message.chat_jid,
            """Hi! I'm an bot based on an open sourc project that was originally created for the llm.org.il community.
            I can help you catch up on the chat messages and answer questions based on the group's knowledge.
            Check out the project on github: https://github.com/ilanbenb/wa_llm
            """,
            message.message_id,
        )

    async def default_response(self, message):
        await self.send_message(
            message.chat_jid,
            "I'm sorry, but I dont think this is something I can help with right now 😅.\n I can help with catching up on the chat messages or answering questions based on the group's knowledge.",
            message.message_id,
        )
