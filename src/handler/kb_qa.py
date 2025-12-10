import logging
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from voyageai.client_async import AsyncClient

from config import Settings
from handler.base_handler import BaseHandler
from handler.knowledge_base_answers import KnowledgeBaseAnswers
from models import Message, Group
from whatsapp import WhatsAppClient

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

        # Check if this group is allowed to run /kb_qa commands
        if message.chat_jid not in self.settings.qa_test_groups:
            logger.warning(
                f"QA command attempted from non-whitelisted group: {message.chat_jid}"
            )
            return  # Silent failure

        # Check if sender is a QA tester
        if message.sender_jid not in self.settings.qa_testers:
            logger.warning(f"Unauthorized /kb_qa attempt from {message.sender_jid}")
            return  # Silent failure

        # Parse command: /kb_qa group: <group_name>, question: <query>
        # Format: /kb_qa group: Tech Support Group, question: How do I reset?
        if not message.text:
            return

        command_prefix = "/kb_qa "
        if not message.text.startswith(command_prefix):
            # Should not happen if filtered correctly before calling, but handle gracefully
            return

        text = message.text[len(command_prefix) :].strip()

        # Handle --help / -h
        if text in ("--help", "-h", ""):
            help_text = (
                "**/kb_qa - Knowledge Base Query**\n\n"
                "Search the knowledge base of a specific managed group.\n\n"
                "**Usage:**\n"
                "`/kb_qa group: <group_name>, question: <question>`\n\n"
                "**Options:**\n"
                "• `--help`, `-h` - Show this help message\n\n"
                "**Examples:**\n"
                "• `/kb_qa group: TechGroup, question: What is the latest update?`\n"
                "• `/kb_qa group: Tech Support Group, question: How do I reset my password?`\n\n"
                "_Note: Only managed groups are searchable._"
            )
            await self.send_message(message.chat_jid, help_text)
            return

        # Parse named parameters: group: <name>, question: <query>
        # Using simple string parsing instead of regex
        text_lower = text.lower()

        # Check for required prefixes
        if not text_lower.startswith("group:"):
            await self.send_message(
                message.chat_jid,
                "Invalid format. Use: /kb_qa group: <group_name>, question: <question>",
            )
            return

        # Find the separator ", question:"
        separator = ", question:"
        separator_pos = text_lower.find(separator)

        if separator_pos == -1:
            await self.send_message(
                message.chat_jid,
                "Invalid format. Use: /kb_qa group: <group_name>, question: <question>",
            )
            return

        # Extract group name (after "group:" prefix, before separator)
        group_name = text[len("group:") : separator_pos].strip()
        # Extract query (after separator)
        query = text[separator_pos + len(separator) :].strip()

        if not group_name or not query:
            await self.send_message(
                message.chat_jid,
                "Both group name and question are required.\n"
                "Use: /kb_qa group: <group_name>, question: <question>",
            )
            return

        # Find the group by name (only managed groups)
        # Try exact match first (case-insensitive)
        stmt = select(Group).where(
            col(Group.group_name).ilike(group_name),
            Group.managed == True,  # noqa: E712  https://stackoverflow.com/a/18998106
        )
        result = await self.session.exec(stmt)
        groups = list(result.all())

        if not groups:
            # Fallback to partial match if no exact match found
            stmt = select(Group).where(
                col(Group.group_name).ilike(f"%{group_name}%"),
                Group.managed == True,  # noqa: E712  https://stackoverflow.com/a/18998106
            )
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
