import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from pydantic_ai import Agent
from voyageai.client_async import AsyncClient
from sqlmodel import desc, select
from models import KBTopicCreate
from pydantic import BaseModel, Field
from models.knowledge_base_topic import KBTopic
from models.message import Message
from utils.voyage_embed_text import voyage_embed_text
import uuid

class Topic(BaseModel):
    subject: str = Field(description="The subject of the summary")
    summary: str = Field(description="A concise summary of the topic discussed. Credit notable insights to the speaker by tagging him (e.g, @user_1)")
    speakers: List[str] = Field(description="The speakers participated. e.g. [@user_1, @user_7, ...]")


class topicsLoader():

    # will be used for the historical data
    def _create_user_mapping(self, wa_df: pd.DataFrame) -> Dict[str, str]:
        """
        Creates a mapping of usernames to shortened names (@user_[id]),
        where more frequent speakers get lower IDs.
        
        Parameters:
        df (pandas.DataFrame): DataFrame containing WhatsApp chat data with 'username' column
        
        Returns:
        Dict[str, str]: Mapping of original usernames to shortened names
        """
        # Count messages per user and sort by frequency (descending)
        user_counts = wa_df['username'].value_counts()
        
        # Create mapping with lower IDs for more frequent speakers
        user_mapping = {username: f"@user_{i+1}" 
                    for i, (username, _) in enumerate(user_counts.items())}
        
        return user_mapping

    def _swap_numbers_tags_in_messages_to_user_tags(self, message: str, user_mapping: Dict[str, str]) -> str:
        for k, v in user_mapping.items():
            message = message.replace(f'@{k}', 'v')
        return message

    def _remap_user_mapping_to_tagged_users(self,   message: str, user_mapping: Dict[str, str]) -> str:
        for k, v in user_mapping.items():
            message = message.replace(k, f'@{v}')
        return message
        
    async def _get_conversation_topics(self, messages: list[Message] ) -> List[Topic]:
        sender_test = {msg.sender_jid  for msg in messages}
        speaker_mapping = {sender_jid: f"@user_{i+1}" for i, sender_jid in enumerate(sender_test)}
        
        # Create the reverse mapping: enumerated number -> original username
        reversed_speaker_mapping = {v: k for k, v in speaker_mapping.items()}

        # Format conversation as "{timestamp}: {participant_enumeration}: {message}"
        # Swap tags in message to user tags E.G. "@972536150150 please comment" to "@user_1 please comment"
        conversation_content = "\n".join([
            f"{message.timestamp}: {speaker_mapping[message.sender_jid]}: {self._swap_numbers_tags_in_messages_to_user_tags(message.text, speaker_mapping)}"
            for message in messages
        ])

        agent = Agent(
            model="anthropic:claude-3-5-sonnet-latest",
            system_prompt="""This conversation is a chain of messages that was uninterrupted by a break in the conversation of up to 3 hours.
    Break the conversation into a list of topics.
    """,
            result_type=List[Topic],
            retries=5,
        )

        result = await agent.run(conversation_content)
        for topic in result.data:
            # If for some reason the speaker is not in the mapping, keep the original speaker
            # This case was needed when the speaker is not in the mapping because the user was not in the chat
            remaped_speakers = [reversed_speaker_mapping.get(speaker, speaker) for speaker in topic.speakers]
            topic.speakers = remaped_speakers
            remaped_summary = self._remap_user_mapping_to_tagged_users(topic.summary, reversed_speaker_mapping)
            topic.summary = remaped_summary
        return result.data

    async def load_topics(self, db_session: AsyncSession, group_jid: str, embedding_client: AsyncClient):
        # Since yesterday at 12:00 UTC. Between 24 hours to 48 hours ago
        # This function is probably be called every day at at midnight+1 UTC 
        today = datetime.utcnow().date()
        yesterday_at_midnight = datetime.combine(today - timedelta(days=1), datetime.min.time())
        stmt = (
            select(Message)
            .where(Message.timestamp >= yesterday_at_midnight)
            .where(Message.group_jid == group_jid)
            .order_by(desc(Message.timestamp))
        )
        res = await db_session.execute(stmt)
        # messages: list[Message] = res.all()
        messages = [row[0] for row in res.all()]  # Unpack the Message objects from the result tuples

        if len(messages) == 0:
            print("No messages found for group", group_jid)
            return
          
        # The result is ordered by timestamp, so the first message is the oldest
        start_time = messages[0].timestamp
        daily_topics = await self._get_conversation_topics(messages)
        print(daily_topics)

        documents = [f"# {topic.subject}\n{topic.summary}" for topic in daily_topics]
        daily_topics_embeddings = await voyage_embed_text(embedding_client, documents)

        doc_models = [
                KBTopicCreate(
                    #  TODO: decide on a meaningfull ID to allow upserts. Probably group_jid + subject and start_time to allow for multiple topics with the same subject
                    id=str(uuid.uuid4()),
                    embedding=emb,
                    group_jid=group_jid,
                    start_time=start_time,
                    # TODO: migrate speakers to a list
                    speakers=','.join(topic.speakers),
                    summary=topic.summary,
                    subject=topic.subject
                ) # type: ignore
                for topic, emb in zip(
                    daily_topics,
                    daily_topics_embeddings
                )
            ]
        # Once we give a meaningfull ID, we should migrate to upsert! 
        db_session.add_all([KBTopic(**doc.dict()) for doc in doc_models])
        await db_session.commit()


if __name__ == "__main__":
    DB_URI="postgresql+asyncpg://user:password@localhost:5432/webhook_db"
    VOYAGE_API_KEY="pa-Zjvv5hZ7QCG52rvGoLVbyRoXQjSuj3w-W96iX6-6Sjb"

    engine = create_async_engine(DB_URI)
    db_session = AsyncSession(engine)
    embedding_client = AsyncClient(
        api_key=VOYAGE_API_KEY,
        max_retries=5
    )
    topics_loader = topicsLoader()
    
    async def main():
        await topics_loader.load_topics(
            db_session=db_session,
            group_jid="120363129163784940@g.us",
            embedding_client=embedding_client
        )
        
    asyncio.run(main())
