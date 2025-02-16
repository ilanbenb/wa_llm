from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, TypeAdapter
from pydantic_ai import Agent
from sqlmodel import desc, select

from models import Message, KBTopic
from .base_handler import BaseHandler


class RouteEnum(str, Enum):
    hey = "HEY"
    summarize = "SUMMARIZE"
    ask_question = "ASK_QUESTION"
    ignore = "IGNORE"


class RouteModel(BaseModel):
    route: RouteEnum


class Router(BaseHandler):
    async def __call__(self, message: Message):
        route = await self._route(message.text)
        match route:
            case RouteEnum.hey:
                await self.send_message(
                    message.chat_jid, "Who is calling my name?"
                )
            case RouteEnum.summarize:
                await self.summarize(message.chat_jid)
            case RouteEnum.ask_question:
                await self.ask_question(message.text)
            case RouteEnum.ignore:
                pass

    async def _route(self, message: str) -> RouteEnum:
        agent = Agent(
            model="anthropic:claude-3-5-sonnet-latest",
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

    async def ask_question(self, question: str):
        
        refrased_agent = Agent(
            model="anthropic:claude-3-5-sonnet-latest",
            system_prompt="Phrase the following sentence to retrieve information for the knowledge base."
        )

        # We obviously need to translate the question and turn the question vebality to a title / summary text to make it closer to the questions in the rag
        refrased_response = await refrased_agent.run(question)
        print(refrased_response.data)

        # Get query embedding
        embeded_question = self.embedding_function([refrased_response.data])[0]
        
        # self. whatsapp.send_message([refrased_response.data])[0]
        # self.embedding_function.
        # query for user query
        relevant_conversations = self.session.exec(
            select(KBTopic)
            .order_by(KBTopic.embedding.l2_distance(embeded_question))
            .limit(5)
        )
        
        similar_conversations = []
        for result in relevant_conversations:
            similar_conversations.append(result.content)

        agent2 = Agent(
            model="anthropic:claude-3-5-sonnet-latest",
            system_prompt="""Based on the conversation attached, write a response to the query.
            - Write a casual direct response to the query. no need to repeat the query.
            - Answer in the same language as the query.
            - Please do tag users while talking about them (e.g., @972536150150). ONLY answer with the new phrased query, no other text."""
        )

        prompt_template = f'''
        question: {refrased_response.data}

        topics related to the query:
        {"\n---\n".join(similar_conversations)}
        '''
        
        responses2 = await agent2.run(prompt_template)
        return responses2.data

        
