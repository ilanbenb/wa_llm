import hashlib
import logging
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field, PrivateAttr
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    before_sleep_log,
)
from voyageai.client_async import AsyncClient

from models import KBTopicCreate, Group, Message
from models.knowledge_base_topic import KBTopic
from models.upsert import bulk_upsert
from utils.voyage_embed_text import voyage_embed_text
from whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


class Topic(BaseModel):
    subject: str = Field(description="The subject of the summary")
    summary: str = Field(
        description="A concise summary of the topic discussed. Credit notable insights to the speaker by tagging him (e.g, @user_1)"
    )
    _speaker_map: Dict[str, str] = PrivateAttr()


def _deid_text(message: str, user_mapping: Dict[str, str]) -> str:
    for k, v in user_mapping.items():
        message = message.replace(f"@{k}", f"@{v}")
    return message


@retry(
    wait=wait_random_exponential(min=5, max=90, multiplier=1.5),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
    reraise=True,
)
async def conversation_splitter_agent(content: str) -> AgentRunResult[List[Topic]]:
    agent = Agent(
        model="anthropic:claude-4-sonnet-20250514",
        # Set bigger then 1024 max token for this agent, because it's a long conversation
        # https://github.com/santokalayil/ai_agents/blame/26b51578ef5864b7f4f0c540e89297867c76d8ab/pydantic_ai/models/anthropic.py#L207C1-L208C1
        model_settings={"max_tokens": 10000},
        system_prompt="""Attached is a snapshot from a group chat conversation. The conversation is a mix of different topics. Your task is to:
- Break the conversation into a list of topics, each topic have the same theme of subject.
- For each topic, write a concise summary of the topic. This will help me to understand the group dynamics and the topics discussed.
- Don't miss any topic! Every subject discussed should be highlighted in the summary, even if it's a small one. You MUST include ALL topics.
- You MUST respond in English.

My goal is learn the different subject discussed in the group chat. This will be used as a knowledge base for the group, so it should not loose any important information or insights.
""",
        output_type=List[Topic],
        retries=5,
    )

    return await agent.run(content)


def _get_speaker_mapping(messages: List[Message]) -> Dict[str, str]:
    i = 1
    sender_jids = {msg.sender_jid for msg in messages}
    speaker_mapping = {}
    for sender_jid in sender_jids:
        speaker_mapping[sender_jid] = f"user_{i}"
        i += 1

    for message in messages:
        # extract all regex @d+ from message.text and add them to speaker_mapping
        for speaker in (message.text or "").split():
            if speaker.startswith("@") and speaker[1:].isdigit():
                if speaker[1:] not in speaker_mapping:
                    speaker_mapping[speaker[1:]] = f"user_{i}"

    return speaker_mapping


def _topic_with_filtered_speakers(
    topic: Topic, speaker_mapping: Dict[str, str]
) -> Topic:
    # find all @user_d+ in topic.summary and topic.subject, then filter them from speaker_mapping
    speakers = set()
    for token in topic.summary.split():
        if token.startswith("@user_") and token[6:].isdigit():
            speakers.add(token[1:])
    for token in topic.subject.split():
        if token.startswith("@user_") and token[6:].isdigit():
            speakers.add(token[1:])

    topic._speaker_map = {v: k for k, v in speaker_mapping.items() if v in speakers}
    return topic


async def get_conversation_topics(
    messages: list[Message], my_number: str
) -> List[Topic]:
    if len(messages) == 0:
        return []

    speaker_mapping = _get_speaker_mapping(messages)
    speaker_mapping[my_number] = "bot"

    # Format conversation as "{timestamp}: {participant_enumeration}: {message}"
    # Swap tags in message to user tags E.G. "@972536150150 please comment" to "@user_1 please comment"
    conversation_content = "\n".join(
        [
            f"{message.timestamp}: @{speaker_mapping[message.sender_jid]}: {_deid_text(message.text, speaker_mapping)}"
            for message in messages
            if message.text is not None
        ]
    )

    result = await conversation_splitter_agent(conversation_content)
    return [
        _topic_with_filtered_speakers(topic, speaker_mapping) for topic in result.data
    ]


async def load_topics(
    db_session: AsyncSession,
    group: Group,
    embedding_client: AsyncClient,
    topics: List[Topic],
    start_time: datetime,
):
    if len(topics) == 0:
        return
    documents = [f"# {topic.subject}\n{topic.summary}" for topic in topics]
    topics_embeddings = await voyage_embed_text(embedding_client, documents)

    doc_models = [
        # TODO: Replace topic.subject with something else that is deterministic.
        # topic.subject is not deterministic because it's the result of the LLM.
        KBTopicCreate(
            id=str(
                hashlib.sha256(
                    f"{group.group_jid}_{start_time}_{topic.subject}".encode()
                ).hexdigest()
            ),
            embedding=emb,
            group_jid=group.group_jid,
            start_time=start_time,
            speakers=",".join(topic._speaker_map.values()),
            summary=_deid_text(topic.summary, topic._speaker_map),
            subject=_deid_text(topic.subject, topic._speaker_map),
        )
        for topic, emb in zip(topics, topics_embeddings)
    ]
    # Once we give a meaningfull ID, we should migrate to upsert!
    await bulk_upsert(db_session, [KBTopic(**doc.model_dump()) for doc in doc_models])

    # Update the group with the new last_ingest
    group.last_ingest = datetime.now()
    db_session.add(group)
    await db_session.commit()


class topicsLoader:
    async def load_topics(
        self,
        db_session: AsyncSession,
        group: Group,
        embedding_client: AsyncClient,
        whatsapp: WhatsAppClient,
    ):
        my_jid = await whatsapp.get_my_jid()
        try:
            # Since yesterday at 12:00 UTC. Between 24 hours to 48 hours ago
            stmt = (
                select(Message)
                .where(Message.timestamp >= group.last_ingest)
                .where(Message.group_jid == group.group_jid)
                .where(Message.sender_jid != my_jid.normalize_str())
                .order_by(desc(Message.timestamp))
            )
            res = await db_session.exec(stmt)
            # Convert Sequence to list explicitly
            messages = list(res.all())

            if len(messages) == 0:
                logger.info(f"No messages found for group {group.group_name}")
                return

            # The result is ordered by timestamp, so the first message is the oldest
            start_time = messages[0].timestamp
            topics = await get_conversation_topics(messages, my_jid.user)
            logger.info(f"Loaded {len(topics)} topics for group {group.group_name}")
            await load_topics(db_session, group, embedding_client, topics, start_time)
            logger.info(f"topics loaded for group {group.group_name}")
        except Exception as e:
            logger.error(f"Error loading topics for group {group.group_name}: {str(e)}")
            raise

    async def load_topics_for_all_groups(
        self,
        session: AsyncSession,
        embedding_client: AsyncClient,
        whatsapp: WhatsAppClient,
    ):
        groups = await session.exec(select(Group).where(Group.managed == True))  # noqa: E712 https://stackoverflow.com/a/18998106
        for group in list(groups.all()):
            await self.load_topics(session, group, embedding_client, whatsapp)
