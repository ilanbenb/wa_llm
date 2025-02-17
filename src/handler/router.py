import logging
from datetime import datetime, timedelta
from enum import Enum

from typing import List
from pydantic import BaseModel, TypeAdapter, Field
from pydantic_ai import Agent
from sqlmodel import desc, select
from voyageai.client_async import AsyncClient

from models import Message, KBTopic, KBTopicCreate
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
        logging.warning(f"Routing decision: {route}")
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


    class Discussion(BaseModel):
        subject: str = Field(description="The subject of the summary")
        summary: str = Field(description="A concise summary of the topic discussed. Credit notable insights to the speaker by tagging him (e.g, @user_1)")
        speakers: List[str] = Field(description="The speakers participated. e.g. [@user_1, @user_7, ...]")
        # messages: List[str]

    def _create_user_mapping(wa_df: pd.DataFrame) -> Dict[str, str]:
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

    async def _get_conversation_topic(messages: list[Message] ) -> str:
        def _remap_user_mapping_to_tagged_users(message: str, user_mapping: Dict[str, str]) -> str:
            for k, v in user_mapping.items():
                message = message.replace(k, f'@{v}')
            return message
        

        def _swap_numbers_tags_in_messages_to_user_tags(message: str, user_mapping: Dict[str, str]) -> str:
            for k, v in user_mapping.items():
                message = message.replace(f'@{k}', 'v')
            return message

        speaker_mapping = dict(zip(df['username'].astype(str).unique(), df['mapped_username'].unique()))

        # Create the reverse mapping: enumerated number -> original username
        reversed_speaker_mapping = {v: k for k, v in speaker_mapping.items()}

        # Format conversation as "{timestamp}: {participant_enumeration}: {message}"
        # Swap tags in message to user tags E.G. "@972536150150 please comment" to "@user_1 please comment"
        conversation_content = "\n".join(
            f"{row['date']}: {row['mapped_username']}: {_swap_numbers_tags_in_messages_to_user_tags(row['message'], speaker_mapping)}"
            for _, row in df.sort_values('date').iterrows()
        )

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
            remaped_summary = _remap_user_mapping_to_tagged_users(discussion.summary, reversed_speaker_mapping)
            discussion.summary = remaped_summary
        return result.data


    # TODO: This is not the right place for this..
    async def load_topics(self, group_jid: str, embedding_client: AsyncClient):
        time_24_hours_ago = datetime.utcnow() - timedelta(hours=24)
        stmt = (
            select(Message)
            .where(Message.timestamp >= time_24_hours_ago)
            .where(Message.group_jid == group_jid)
            .order_by(desc(Message.timestamp))
        )
        res = await self.session.exec(stmt)
        messages: list[Message] = res.all()

        conversation_topics = await self._get_conversation_topic(messages)

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
        for i in range(0, len(documents), self.batch_size):
            batch_end = i + self.batch_size
            doc_models = [
                KBTopicCreate(
                    id=id,
                    # content=doc,
                    embedding=emb,
                    group=meta["group"],
                    start_time=meta["start_time"],
                    speakers=meta["speakers"],
                    summary=meta.get("summary"),
                    subject=meta.get("subject")
                )
                for doc, emb, meta, id in zip(
                    documents[i:batch_end],
                    embeddings[i:batch_end],
                    metadatas[i:batch_end],
                    ids[i:batch_end]
                )
            ]
            
            self.session.add_all([KBTopic(**doc.dict()) for doc in doc_models])
            await self.session.commit()