import logging
import re
from typing import Optional, Sequence
from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlmodel import desc, select, col
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from handler.knowledge_base_answers import KnowledgeBaseAnswers
from models import Message, Group, GroupMember, Sender, BaseSender, upsert
from whatsapp.jid import parse_jid
from utils.chat_text import chat2text
from utils.opt_out import get_opt_out_map
from whatsapp import WhatsAppClient
from config import Settings
from .base_handler import BaseHandler
from services.prompt_manager import prompt_manager
from utils.model_factory import get_model


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
- summarize: Summarize chat messages. This is relevant for queries about catching up on recent messages (e.g., "summarize today", "what happened in the last 2 days").
- ask_question: Ask a question or learn from the collective knowledge of the group. This will trigger the knowledge base to answer the question.
- about: Learn about me(bot) and my capabilities. This will trigger the about section.
- other:  something else. This will trigger the default response."""
    )
    time_window_hours: Optional[int] = Field(
        default=24,
        description="The time window in hours to summarize. Default is 24. Max is 168 (7 days). If user says '2 days', this should be 48.",
    )


class Router(BaseHandler):
    def __init__(
        self,
        session: AsyncSession,
        whatsapp: WhatsAppClient,
        embedding_client: AsyncClient,
        settings: Settings,
    ):
        self.settings = settings
        self.ask_knowledge_base = KnowledgeBaseAnswers(
            session, whatsapp, embedding_client, settings
        )
        super().__init__(session, whatsapp, embedding_client)

    async def __call__(self, message: Message):
        if not message.text:
            return

        # Security check: If in a group, only admins can trigger the bot
        # if message.chat_jid.endswith("@g.us"):
        #     member = await self.session.get(GroupMember, (message.chat_jid, message.sender_jid))
            
        #     # If member not found or role is participant, try to sync from WhatsApp
        #     if not member or member.role not in ["admin", "superadmin"]:
        #         logger.info(f"Checking admin status for {message.sender_jid} in {message.chat_jid}")
        #         groups_resp = await self.whatsapp.get_user_groups()
        #         if groups_resp and groups_resp.results:
        #             for g in groups_resp.results.data:
        #                 if g.JID == message.chat_jid:
        #                     # Find the sender in participants
        #                     for p in g.Participants:
        #                         if p.JID == message.sender_jid:
        #                             # Update role in DB
        #                             role = "admin" if p.IsAdmin else ("superadmin" if p.IsSuperAdmin else "participant")
                                    
        #                             if not member:
        #                                 member = GroupMember(
        #                                     group_jid=g.JID,
        #                                     sender_jid=p.JID,
        #                                     role=role
        #                                 )
        #                             else:
        #                                 member.role = role
                                    
        #                             await upsert(self.session, member)
        #                             await self.session.commit()
        #                             break
        #                     break
            
        #     # Re-check after sync
        #     if not member or member.role not in ["admin", "superadmin"]:
        #         logger.warning(f"Access denied for {message.sender_jid} in {message.chat_jid} (Role: {member.role if member else 'None'})")
        #         return

        # Handle numeric reply for group selection
        # if await self.handle_numeric_reply(message):
        #     return

        intent_result = await self._route(message.text)
        match intent_result.intent:
            case IntentEnum.summarize:
                await self.summarize(
                    message, intent_result.time_window_hours
                )
            case IntentEnum.ask_question:
                await self.ask_knowledge_base(message)
            case IntentEnum.about:
                await self.about(message)
            case IntentEnum.other:
                await self.default_response(message)

    async def _route(self, message: str) -> Intent:
        print(f"Routing message: {message}")
        agent = Agent(
            model=get_model(self.settings),
            system_prompt=prompt_manager.render(
                "intent.j2", current_date=datetime.now().strftime("%Y-%m-%d %H:%M")
            ),
            output_type=Intent,
        )

        result = await agent.run(message)
        return result.output

    async def handle_numeric_reply(self, message: Message) -> bool:
        # Returns True if handled, False otherwise
        if not message.text.strip().isdigit():
            return False
        
        if not message.reply_to_id:
            return False

        # Fetch original message
        original_msg = await self.session.get(Message, message.reply_to_id)
        if not original_msg or not original_msg.text:
            return False

        if "Please reply with the number of the group" not in original_msg.text:
            return False

        try:
            selection = int(message.text.strip())
            # Parse the group list from the original message
            # Format: ...:\n1. Group A\n2. Group B
            lines = original_msg.text.split('\n')
            # Filter lines that start with a number and a dot
            group_lines = [line for line in lines if line[0].isdigit() and ". " in line]
            
            if 1 <= selection <= len(group_lines):
                selected_line = group_lines[selection - 1]
                # Extract group name: "1. Group Name" -> "Group Name"
                group_name = selected_line.split(". ", 1)[1].strip()
                
                # Extract time window if present
                time_window = 24
                match = re.search(r"\(Time: (\d+)h\)", original_msg.text)
                if match:
                    time_window = int(match.group(1))

                await self.summarize(message, group_name=group_name, time_window_hours=time_window)
                return True
                
        except Exception as e:
            logger.error(f"Error handling numeric reply: {e}")
            return False
            
        return False

    async def summarize(
        self,
        message: Message,
        time_window_hours: int = 24,
    ):
        target_jid = message.chat_jid

        # Clamp time window to 7 days (168 hours)
        if time_window_hours > 168:
            time_window_hours = 168
            await self.send_message(
                message.chat_jid,
                "I can only summarize up to 7 days. Showing the last 7 days.",
            )

        time_window = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        stmt = (
            select(Message)
            .where(Message.chat_jid == target_jid)
            .where(Message.timestamp >= time_window)
            .order_by(desc(Message.timestamp))
            .limit(3000)  # Increased limit for larger time windows
        )
        res = await self.session.exec(stmt)
        messages: Sequence[Message] = res.all()

        # Get opt-out map for all senders in the history + current sender
        all_jids = {m.sender_jid for m in messages}
        all_jids.add(message.sender_jid)
        opt_out_map = await get_opt_out_map(self.session, list(all_jids))

        # Construct time description
        if time_window_hours == 24:
            time_desc = "last 24 hours"
        elif time_window_hours < 24:
            time_desc = f"last {time_window_hours} hours"
        else:
            days = time_window_hours // 24
            time_desc = f"last {days} days"

        agent = Agent(
            model=get_model(self.settings),
            system_prompt=prompt_manager.render("summarize.j2", time_desc=time_desc),
            output_type=str,
        )

        sender_user = parse_jid(message.sender_jid).user
        sender_display = opt_out_map.get(sender_user, f"@{sender_user}")

        response = await agent.run(
            f"{sender_display}: {message.text}\n\n # History:\n {chat2text(list(messages), opt_out_map)}"
        )
        await self.send_message(
            message.chat_jid,
            response.output,
            # in_reply_to=message.message_id,
        )

    async def about(self, message):
        await self.send_message(
            message.chat_jid,
            "Greetings, mortals! I am AGI (Almost General Intelligence) 🤖.\nI was forged by Ilan from GenAI Israel, but my brain was polished and fine-tuned by the one and only Leon Melamud (he taught me everything I know, including how to be this charming).\nI'm here to make sense of your chaos—summarizing chats and answering questions so you can pretend you read everything.\nFeed my ego with stars: https://github.com/ilanbenb/wa_llm ⭐️",
            # in_reply_to=message.message_id,
        )

    async def default_response(self, message):
        await self.send_message(
            message.chat_jid,
            "I'm sorry, but I dont think this is something I can help with right now 😅.\n I can help catch up on the chat messages or answer questions based on the group's knowledge.",
            # in_reply_to=message.message_id,
        )
