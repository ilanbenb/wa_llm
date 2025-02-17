import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from pydantic_ai import Agent
from voyageai.client_async import AsyncClient
from sqlmodel import desc, select
from models import KBTopicCreate
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession
from collections import Counter
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from models.knowledge_base_topic import KBTopic
from models.message import Message

#temp untill I remove pandas
import pandas as pd
class Discussion(BaseModel):
            subject: str = Field(description="The subject of the summary")
            summary: str = Field(description="A concise summary of the topic discussed. Credit notable insights to the speaker by tagging him (e.g, @user_1)")
            speakers: List[str] = Field(description="The speakers participated. e.g. [@user_1, @user_7, ...]")
            # messages: List[str]

class topicsLoader():

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
        



    async def _get_conversation_topic(self, messages: list[Message] ) -> str:
        sender_test = {msg.sender_jid  for msg in messages}
        speaker_mapping = {sender_jid: f"@user_{i+1}" for i, sender_jid in enumerate(sender_test)}
        
        # #temp create empty df
        # df = pd.DataFrame()
        # speaker_mapping = dict(zip(df['username'].astype(str).unique(), df['mapped_username'].unique()))

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
    Break the conversation into a list of discussions.
    """,
            result_type=List[Discussion],
            retries=5,
        )

        result = await agent.run(conversation_content)
        for discussion in result.data:
            # If for some reason the speaker is not in the mapping, keep the original speaker
            # This case was needed when the speaker is not in the mapping because the user was not in the chat
            remaped_speakers = [reversed_speaker_mapping.get(speaker, speaker) for speaker in discussion.speakers]
            discussion.speakers = remaped_speakers
            remaped_summary = self._remap_user_mapping_to_tagged_users(discussion.summary, reversed_speaker_mapping)
            discussion.summary = remaped_summary
        return result.data

    async def load_topics(self, db_session: AsyncSession, group_jid: str, embedding_client: AsyncClient):
        # Since yesterday at 12:00 UTC
        time_24_hours_ago = datetime.utcnow() - timedelta(hours=24)
        stmt = (
            select(Message)
            .where(Message.timestamp >= time_24_hours_ago)
            .where(Message.group_jid == group_jid)
            .order_by(desc(Message.timestamp))
        )
        res = await db_session.execute(stmt)
        # messages: list[Message] = res.all()
        messages = [row[0] for row in res.all()]  # Unpack the Message objects from the result tuples

        conversation_topics = await self._get_conversation_topic(messages)
        print(conversation_topics)


        #  Continues from here
        #         return {
        #     'conversation_id': conv_id,
        #     'group_name': conv_data['group'].iat[0],
        #     'start_time': conv_data['date'].min(),
        #     'end_time': conv_data['date'].max(),
        #     'duration_minutes': (conv_data['date'].max() - conv_data['date'].min()).total_seconds() / 60,
        #     'num_messages': len(conv_data),
        #     'num_participants': conv_data['username'].nunique(),
        #     'participants': ', '.join(conv_data['username'].astype(str).unique()),
        #     'conversation_content': conv_data,
        #     'discussions': discussions,
        #     'tokens': _estimate_tokens(', '.join(conv_data['message']))
        # }

        # To topics:

        #     for conversation in conversations.iterrows():
        # discussions = conversation[1]['discussions']
        # for discussion in discussions:
        #     conversation_content = "\n".join(
        #         f"{row['date']}: {[row['username']]}: {row['message']}"
        #         for _, row in conversation[1]['conversation_content'].iterrows()
        #     )
        #     new_row = pd.DataFrame([{
        #            'id': f"discussion_{uuid.uuid4()}",
        #            'subject': discussion.subject,
        #            'summary': discussion.summary,
        #            'speakers': discussion.speakers,
        #            'start_time': conversation[1]['start_time'],
        #            "original_conversation": conversation_content,
        #            # 'group': conversation[1]['group_name'],
        #     }])
        #     discussion_df = pd.concat([discussion_df, new_row], ignore_index=True)

        #summary should part of the document
        discussion_df = pd.DataFrame()
        documents = discussion_df.apply(
            lambda row: f"# {row['subject']}\n{row['summary']}", axis=1
        ).tolist()
        metadatas = discussion_df[['summary', 'speakers', 'start_time', 'group']].to_dict(orient='records')
        # TODO: group should be a field in the metadata
        metadatas =[{"summary":  metadata.get("summary"),"speakers": ' ,'.join(metadata.get("speakers")), "group": "GenAI Israel", "start_time": str(metadata["start_time"])} for metadata in metadatas]
        ids = discussion_df['id'].tolist()

        embeddings = await self._embed_text(self.embedding_client, documents)
        
    #     await vector_store.add_documents(
    #         documents=documents,
    #         embeddings=embeddings,
    #         metadatas=metadatas,
    #         ids=ids
    #     )


    # async def add_documents(
    #     self,
    #     documents: List[str],
    #     embeddings: List[List[float]],
    #     metadatas: List[Dict[str, Any]],
    #     ids: List[str]
    # ) -> None:
    #     """Add documents to the vector store in batches"""

        batch_size = 128
        for i in range(0, len(documents), batch_size):
            batch_end = i + batch_size
            doc_models = [
                KBTopicCreate(
                    id=id,
                    # content=doc,
                    embedding=emb,
                    group_jid=meta["group"],
                    start_time=meta["start_time"],
                    speakers=meta["speakers"],
                    summary=meta["summary"],
                    subject=meta["subject"]
                ) # type: ignore
                for doc, emb, meta, id in zip(
                    documents[i:batch_end],
                    embeddings[i:batch_end],
                    metadatas[i:batch_end],
                    ids[i:batch_end]
                )
            ]
            
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
