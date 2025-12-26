import logging
from typing import List

from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    before_sleep_log,
)
from voyageai.client_async import AsyncClient

from models import Message
from whatsapp import WhatsAppClient
from whatsapp.jid import parse_jid
from utils.chat_text import chat2text
from utils.opt_out import get_opt_out_map
from utils.voyage_embed_text import voyage_embed_text
from .base_handler import BaseHandler
from config import Settings
from services.prompt_manager import prompt_manager
from utils.model_factory import get_model
from services.web_search import web_search_service


# Creating an object
logger = logging.getLogger(__name__)


class KnowledgeBaseAnswers(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
        settings: Settings,
    ):
        self.settings = settings
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, message: Message):
        # Ensure message.text is not None before passing to generation_agent
        if message.text is None:
            logger.warning(f"Received message with no text from {message.sender_jid}")
            return
        # get the last 7 messages
        stmt = (
            select(Message)
            .where(Message.chat_jid == message.chat_jid)
            .order_by(desc(Message.timestamp))
            .limit(7)
        )
        res = await self.session.exec(stmt)
        history: list[Message] = list(res.all())

        # Get opt-out map
        all_jids = {m.sender_jid for m in history}
        all_jids.add(message.sender_jid)
        opt_out_map = await get_opt_out_map(self.session, list(all_jids))

        rephrased_result = await self.rephrasing_agent(
            (await self.whatsapp.get_my_jid()).user, message, history, opt_out_map
        )
        # Get query embedding
        embedded_question = (
            await voyage_embed_text(self.embedding_client, [rephrased_result.output])
        )[0]

        # Determine which groups to search
        group_jids = None
        enable_web_search = False
        if message.group:
            enable_web_search = message.group.enable_web_search
            group_jids = [message.group.group_jid]
            if message.group.community_keys:
                related_groups = await message.group.get_related_community_groups(
                    self.session
                )
                group_jids.extend([g.group_jid for g in related_groups])

        # Use hybrid search to get topics with their source messages
        from search.hybrid_search import hybrid_search, format_search_results_for_prompt

        search_results = await hybrid_search(
            session=self.session,
            query=message.text,
            query_embedding=embedded_question,
            group_jids=group_jids,
            vector_limit=10,
            messages_per_topic=5,
        )

        # Format results for the generation agent
        formatted_topics = format_search_results_for_prompt(search_results, opt_out_map)

        # Also prepare distances for logging
        similar_topics_distances = [
            f"topic_distance: {r.vector_distance}" for r in search_results
        ]

        sender_number = parse_jid(message.sender_jid).user
        
        logger.info(f"Generating answer for {sender_number}. Web search enabled: {enable_web_search}")

        if enable_web_search:
            await self.send_message(
                message.chat_jid,
                "I'm checking the web for this information, please wait a moment... 🌐"
            )
        
        generation_result = await self.generation_agent(
            message.text,
            formatted_topics,
            message.sender_jid,
            history,
            opt_out_map,
            enable_web_search,
        )
        logger.info(
            "RAG Query Results:\n"
            f"Sender: {sender_number}\n"
            f"Question: {message.text}\n"
            f"Rephrased Question: {rephrased_result.output}\n"
            f"Chat JID: {message.chat_jid}\n"
            f"Retrieved Topics: {len(search_results)}\n"
            f"Total Messages: {sum(len(r.messages) for r in search_results)}\n"
            f"Similarity Scores: {similar_topics_distances}\n"
            f"Generated Response: {generation_result.output}"
        )

        await self.send_message(
            message.chat_jid,
            generation_result.output,
            # in_reply_to=message.message_id,
        )

    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(6),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def generation_agent(
        self,
        query: str,
        topics: str,  # receives pre-formatted topics
        sender: str,
        history: List[Message],
        opt_out_map: dict[str, str],
        enable_web_search: bool = False,
    ) -> AgentRunResult[str]:
        tools = []
        if enable_web_search:
            tools.append(web_search_service.search)

        agent = Agent(
            model=get_model(self.settings),
            system_prompt=prompt_manager.render(
                "rag.j2", enable_web_search=enable_web_search
            ),
            tools=tools,
        )

        sender_user = parse_jid(sender).user
        sender_display = opt_out_map.get(sender_user, f"@{sender_user}")

        prompt_template = f"""
        {sender_display}: {query}
        
        # Recent chat history:
        {chat2text(history, opt_out_map)}
        
        # Related Topics:
        {topics}
        """

        return await agent.run(prompt_template)

    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(6),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def rephrasing_agent(
        self,
        my_jid: str,
        message: Message,
        history: List[Message],
        opt_out_map: dict[str, str],
    ) -> AgentRunResult[str]:
        rephrased_agent = Agent(
            model=get_model(self.settings),
            system_prompt=prompt_manager.render("rephrase.j2", my_jid=my_jid),
        )

        # We obviously need to translate the question and turn the question vebality to a title / summary text to make it closer to the questions in the rag
        return await rephrased_agent.run(
            f"{message.text}\n\n## Recent chat history:\n {chat2text(history, opt_out_map)}"
        )
