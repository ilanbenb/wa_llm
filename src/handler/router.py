import logging
from datetime import datetime, timedelta
from enum import Enum

from typing import List
from pydantic import BaseModel, TypeAdapter
from pydantic_ai import Agent
from sqlmodel import desc, select
from voyageai.client_async import AsyncClient

from models import Message, KBTopic
from .base_handler import BaseHandler


class RouteEnum(str, Enum):
    summarize = "SUMMARIZE"
    ask_question = "ASK_QUESTION"
    other = "OTHER"


class RouteModel(BaseModel):
    route: RouteEnum


class Router(BaseHandler):
    async def __call__(self, message: Message):
        route = await self._route(message.text)
        match route:
            case RouteEnum.summarize:
                await self.summarize(message.chat_jid)
            case RouteEnum.ask_question:
                await self.ask_question(message.text)
            case RouteEnum.other:
                logging.warning(f"OTHER route was chosen Lets see why: {message.text}, {message.chat_jid}")

    async def _route(self, message: str) -> RouteEnum:
        agent = Agent(
            model="anthropic:claude-3-5-haiku-latest",
            system_prompt="Extract a routing decision from the input.",
            result_type=RouteEnum,
        )

        result = await agent.run(message)
        return result.data
    async def summarize(self, chat_jid: str):
        time_24_hours_ago = datetime.utcnow() - timedelta(hours=24)
        stmt = (
            select(Message)
            .where(Message.chat_jid == chat_jid)
            .where(Message.timestamp >= time_24_hours_ago)
            .order_by(desc(Message.timestamp))
        )
        res = await self.session.exec(stmt)
        messages: list[Message] = res.all()

        agent = Agent(
            model="anthropic:claude-3-5-sonnet-latest",
            system_prompt="Summarize the following messages in a few words.",
            result_type=str,
        )

        # TODO: format messages in a way that is easy for the LLM to read
        response = await agent.run(
            TypeAdapter(list[Message]).dump_json(messages).decode()
        )
        await self.send_message(chat_jid, response.data)

    async def _embed_text(self, embedding_client: AsyncClient, input: List[str]) -> List[List[float]]:
        model_name = 'voyage-3'
        batch_size = 128
        embeddings = []
        total_tokens = 0

        for i in range(0, len(input), batch_size):
            res = await embedding_client.embed(
                input[i : i + batch_size],
                model=model_name,
                input_type="document"
            )
            embeddings += res.embeddings
            total_tokens += res.total_tokens
        return embeddings
    
    async def ask_question(self, question: str):
        
        rephrased_agent = Agent(
            model="anthropic:claude-3-5-haiku-latest",
            system_prompt="Phrase the following sentence to retrieve information for the knowledge base. ONLY answer with the new phrased query, no other text"
        )

        # We obviously need to translate the question and turn the question vebality to a title / summary text to make it closer to the questions in the rag
        rephrased_response = await rephrased_agent.run(question)
        # Get query embedding
        embedded_question = (await self._embed_text(self.embedding_client, [rephrased_response.data]))[0]
        
        # query for user query
        retrieved_topics = await self.session.exec(
            select(KBTopic)
            .order_by(KBTopic.embedding.l2_distance(embedded_question))
            .limit(5)
        )
        
        similar_topics = []
        for result in retrieved_topics:
            similar_topics.append(result.content)

        generation_agent = Agent(
            model="anthropic:claude-3-5-sonnet-latest",
            system_prompt="""Based on the topics attached, write a response to the query.
            - Write a casual direct response to the query. no need to repeat the query.
            - Answer in the same language as the query.
            - Only answer from the topics attached, no other text.
            - Please do tag users while talking about them (e.g., @972536150150). ONLY answer with the new phrased query, no other text."""
        )

        prompt_template = f'''
        question: {rephrased_response.data}

        topics related to the query:
        {"\n---\n".join(similar_topics)}
        '''
        
        generation_response = await generation_agent.run(prompt_template)
        logging.info(f"retreival: {similar_topics}, generation {generation_response.data}")
        return generation_response.data

        
