import logging
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings
from handler.base_handler import BaseHandler
from handler.knowledge_base_answers import KnowledgeBaseAnswers
from models import Message, Group
from whatsapp import WhatsAppClient
from whatsapp.jid import parse_jid

logger = logging.getLogger(__name__)


class KBQAHandler(BaseHandler):
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
        """Handle the /kb_qa <group_name> <query> command for cross-group KB search."""
        # This handler expects to be called only when the command matches,
        # but we can add a safety check or just assume usage in MessageHandler controls it.
        # The logic below is adapted from Router._handle_qa_command

        # Check if this group is allowed to run /qa commands
        if message.chat_jid not in self.settings.qa_test_groups:
            logger.warning(
                f"QA command attempted from non-whitelisted group: {message.chat_jid}"
            )
            return  # Silent failure

        sender_jid = parse_jid(message.sender_jid)
        sender_user = sender_jid.user

        # Check if sender is a QA tester
        if sender_user not in self.settings.qa_testers:
            logger.warning(f"Unauthorized /qa attempt from {sender_user}")
            return  # Silent failure

        # Parse command: /kb_qa <group_name> <query>
        # Format: /kb_qa "Group Name" question here
        # or: /kb_qa GroupName question here
        if not message.text:
            return

        command_prefix = "/kb_qa "
        if not message.text.startswith(command_prefix):
            # Should not happen if filtered correctly before calling, but handle gracefully
            return

        text = message.text[len(command_prefix) :].strip()

        if text.startswith('"'):
            # Quoted group name
            end_quote = text.find('"', 1)
            if end_quote == -1:
                await self.send_message(
                    message.chat_jid,
                    'Invalid format. Use: /kb_qa "Group Name" <question>',
                )
                return
            group_name = text[1:end_quote]
            query = text[end_quote + 1 :].strip()
        else:
            # Space-separated
            parts = text.split(" ", 1)
            if len(parts) < 2:
                await self.send_message(
                    message.chat_jid,
                    "Invalid format. Use: /kb_qa <group_name> <question>",
                )
                return
            group_name = parts[0]
            query = parts[1]

        # Find the group by name
        # Try exact match first (case-insensitive)
        stmt = select(Group).where(col(Group.group_name).ilike(group_name))
        result = await self.session.exec(stmt)
        groups = list(result.all())

        if not groups:
            # Fallback to partial match if no exact match found
            stmt = select(Group).where(col(Group.group_name).ilike(f"%{group_name}%"))
            result = await self.session.exec(stmt)
            groups = list(result.all())

        if len(groups) == 0:
            await self.send_message(
                message.chat_jid, f"No group found matching '{group_name}'"
            )
            return
        elif len(groups) > 1:
            group_list = "\n".join([f"- {g.group_name}" for g in groups[:5]])
            await self.send_message(
                message.chat_jid,
                f"Multiple groups found matching '{group_name}':\n{group_list}\nPlease be more specific.",
            )
            return

        target_group = groups[0]
        logger.info(
            f"QA command: querying group '{target_group.group_name}' with: {query}"
        )

        # Create a synthetic message pointing to the target group
        qa_message = Message(
            message_id=message.message_id,
            timestamp=message.timestamp,
            text=query,
            chat_jid=message.chat_jid,  # Reply to original chat
            sender_jid=message.sender_jid,
            group_jid=target_group.group_jid,  # But search in target group
        )

        # Run the knowledge base search
        await self.ask_knowledge_base(qa_message)
