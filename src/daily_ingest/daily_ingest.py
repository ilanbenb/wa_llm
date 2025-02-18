import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from pydantic_ai import Agent
from voyageai.client_async import AsyncClient
from sqlmodel import desc, select
from models import KBTopicCreate, Group, Message
from pydantic import BaseModel, Field
from models.knowledge_base_topic import KBTopic
from models.upsert import bulk_upsert
from utils.voyage_embed_text import voyage_embed_text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
import hashlib
from tenacity import retry, wait_random_exponential, stop_after_attempt, after_log
import logging

logger = logging.getLogger(__name__)


class Topic(BaseModel):
    subject: str = Field(description="The subject of the summary")
    summary: str = Field(
        description="A concise summary of the topic discussed. Credit notable insights to the speaker by tagging him (e.g, @user_1)"
    )
    speakers: List[str] = Field(
        description="The speakers participated. e.g. [@user_1, @user_7, ...]"
    )


def _swap_numbers_tags_in_messages_to_user_tags(
    message: str, user_mapping: Dict[str, str]
) -> str:
    for k, v in user_mapping.items():
        message = message.replace(f"@{k}", "v")
    return message


def _remap_user_mapping_to_tagged_users(
    message: str, user_mapping: Dict[str, str]
) -> str:
    for k, v in user_mapping.items():
        message = message.replace(k, f"@{v}")
    return message


async def get_conversation_topics(messages: list[Message]) -> List[Topic]:
    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(6),
        after=after_log(logger, logging.ERROR),
    )
    async def _run_agent(content):
        return await agent.run(content)

    sender_jids = {msg.sender_jid for msg in messages}
    speaker_mapping = {
        sender_jid: f"@user_{i+1}" for i, sender_jid in enumerate(sender_jids)
    }

    # Create the reverse mapping: enumerated number -> original username
    reversed_speaker_mapping = {v: k for k, v in speaker_mapping.items()}

    # Format conversation as "{timestamp}: {participant_enumeration}: {message}"
    # Swap tags in message to user tags E.G. "@972536150150 please comment" to "@user_1 please comment"
    conversation_content = "\n".join(
        [
            f"{message.timestamp}: {speaker_mapping[message.sender_jid]}: {_swap_numbers_tags_in_messages_to_user_tags(message.text, speaker_mapping)}"
            for message in messages
            if message.text is not None
        ]
    )

    agent = Agent(
        model="anthropic:claude-3-5-sonnet-latest",
        system_prompt="""This conversation is a chain of messages that was uninterrupted by a break in the conversation of up to 3 hours.
Break the conversation into a list of topics.
""",
        result_type=List[Topic],
        retries=5,
    )

    result = await _run_agent(conversation_content)
    for topic in result.data:
        # If for some reason the speaker is not in the mapping, keep the original speaker
        # This case was needed when the speaker is not in the mapping because the user was not in the chat
        remaped_speakers = [
            reversed_speaker_mapping.get(speaker, speaker) for speaker in topic.speakers
        ]
        topic.speakers = remaped_speakers
        remaped_summary = _remap_user_mapping_to_tagged_users(
            topic.summary, reversed_speaker_mapping
        )
        topic.summary = remaped_summary
    return result.data


async def load_topics(
    db_session: AsyncSession,
    group_jid: str,
    embedding_client: AsyncClient,
    topics: List[Topic],
    start_time: datetime,
):
    documents = [f"# {topic.subject}\n{topic.summary}" for topic in topics]
    topics_embeddings = await voyage_embed_text(embedding_client, documents)

    doc_models = [
        KBTopicCreate(
            id=str(
                hashlib.sha256(
                    f"{group_jid}_{start_time}_{topic.subject}".encode()
                ).hexdigest()
            ),
            embedding=emb,
            group_jid=group_jid,
            start_time=start_time,
            speakers=",".join(topic.speakers),
            summary=topic.summary,
            subject=topic.subject,
        )
        for topic, emb in zip(topics, topics_embeddings)
    ]
    # Once we give a meaningfull ID, we should migrate to upsert!
    await bulk_upsert(db_session, [KBTopic(**doc.model_dump()) for doc in doc_models])
    await db_session.commit()


class topicsLoader:
    async def load_topics(
        self, db_session: AsyncSession, group_jid: str, embedding_client: AsyncClient
    ):
        # Since yesterday at 12:00 UTC. Between 24 hours to 48 hours ago
        # This function is probably be called every day at at midnight+1 UTC
        today = datetime.utcnow().date()
        yesterday_at_midnight = datetime.combine(
            today - timedelta(days=1), datetime.min.time()
        )
        stmt = (
            select(Message)
            .where(Message.timestamp >= yesterday_at_midnight)
            .where(Message.group_jid == group_jid)
            .order_by(desc(Message.timestamp))
        )
        res = await db_session.exec(stmt)
        messages: list[Message] = res.all()

        if len(messages) == 0:
            print("No messages found for group", group_jid)
            return

        # The result is ordered by timestamp, so the first message is the oldest
        start_time = messages[0].timestamp
        daily_topics = await get_conversation_topics(messages)
        await load_topics(
            db_session, group_jid, embedding_client, daily_topics, start_time
        )


# TODO: This is a test entrypoint, remove it when we have a proper way to run the daily ingest
if __name__ == "__main__":
    import os

    DB_URI = os.getenv("DB_URI")
    VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

    engine = create_async_engine(DB_URI)
    db_session = AsyncSession(engine)
    embedding_client = AsyncClient(api_key=VOYAGE_API_KEY, max_retries=5)
    topics_loader = topicsLoader()

    async def main():
        groups = (await db_session.exec(select(Group))).all()
        for group in groups:
            if not group.managed:
                continue
            await topics_loader.load_topics(
                db_session=db_session,
                group_jid=group.group_jid,
                embedding_client=embedding_client,
            )

    asyncio.run(main())
