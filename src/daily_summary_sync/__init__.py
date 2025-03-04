import asyncio
import logging
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.result import RunResult
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    before_sleep_log,
)

from models import Group, Message
from utils.chat_text import chat2text
from whatsapp import WhatsAppClient, SendMessageRequest

logger = logging.getLogger(__name__)


@retry(
    wait=wait_random_exponential(min=1, max=30),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
    reraise=True,
)
async def summarize(group_name: str, messages: list[Message]) -> RunResult[str]:
    agent = Agent(
        model="anthropic:claude-3-5-haiku-latest",
        system_prompt=f""""
        Write a quick summary of what happened in the chat group since the last summary.
        
        - Start by stating this is a quick summary of what happened in "{group_name}" group recently.
        - Use a casual conversational writing style.
        - Keep it short and sweet.
        - Write in the same language as the chat group.
        - Please do tag users while talking about them (e.g., @972536150150). ONLY answer with the new phrased query, no other text.
        """,
        result_type=str,
    )

    return await agent.run(chat2text(messages))


async def sync_group(session, whatsapp: WhatsAppClient, group: Group):
    community_groups = await group.get_related_community_groups(session)
    if not community_groups:
        logging.info("No community groups found for group %s", group.group_name)
        return

    messages = await session.exec(
        select(Message)
        .where(Message.group_jid == group.group_jid)
        .where(Message.timestamp >= group.last_summary_sync)
        .where(Message.sender_jid != (await whatsapp.get_my_jid()).normalize_str())
        .order_by(desc(Message.timestamp))
    )
    messages: list[Message] = messages.all()

    if len(messages) < 7:
        logging.info("Not enough messages to summarize in group %s", group.group_name)
        return

    response = await summarize(group.group_name, messages)

    for cg in community_groups:
        await whatsapp.send_message(
            SendMessageRequest(phone=cg.group_jid, message=response.data)
        )

    # Update the group with the new last_summary_sync
    group.last_summary_sync = datetime.now()
    session.add(group)
    await session.commit()


async def daily_summary_sync(session: AsyncSession, whatsapp: WhatsAppClient):
    groups = await session.exec(select(Group).where(Group.managed == True))
    tasks = [sync_group(session, whatsapp, group) for group in list(groups.all())]
    errs = await asyncio.gather(*tasks, return_exceptions=True)
    for e in errs:
        if isinstance(e, BaseException):
            logging.error("Error syncing group: %s", e)
