from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime

from .jid import normalize_jid, parse_jid, JID
from .webhook import WhatsAppWebhookPayload, Message as PayloadMessage

if TYPE_CHECKING:
    from .group import Group
    from .sender import Sender


class BaseMessage(SQLModel):
    message_id: str = Field(primary_key=True, max_length=255)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    text: Optional[str] = Field(default=None)
    media_url: Optional[str] = Field(default=None)
    chat_jid: str = Field(max_length=255)
    sender_jid: str = Field(max_length=255, foreign_key="sender.jid")
    group_jid: Optional[str] = Field(
        max_length=255,
        foreign_key="group.group_jid",
        nullable=True,
        default=None,
    )
    reply_to_id: Optional[str] = Field(default=None, nullable=True)

    @model_validator(mode="before")
    @classmethod
    def validate_chat_jid(self, data) -> dict:
        if "chat_jid" not in data:
            return data

        jid = parse_jid(data["chat_jid"])

        if jid.is_group():
            data["group_jid"] = str(jid.to_non_ad())

        data["chat_jid"] = str(jid.to_non_ad())
        return data

    @field_validator("group_jid", "sender_jid", mode="before")
    @classmethod
    def normalize(cls, value: Optional[str]) -> str | None:
        return normalize_jid(value) if value else None

    def has_mentioned(self, jid: str | JID) -> bool:
        if isinstance(jid, str):
            jid = parse_jid(jid)

        return f"@{jid.user}" in self.text


class Message(BaseMessage, table=True):
    sender: Optional["Sender"] = Relationship(
        back_populates="messages", sa_relationship_kwargs={"lazy": "selectin"}
    )
    group: Optional["Group"] = Relationship(
        back_populates="messages", sa_relationship_kwargs={"lazy": "selectin"}
    )
    replies: List["Message"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Message.message_id==foreign(Message.reply_to_id)",
            "remote_side": "Message.message_id",  # Add this to clarify direction
            "backref": "replied_to",
        }
    )

    @classmethod
    def from_webhook(cls, payload: WhatsAppWebhookPayload) -> "Message":
        """Create Message instance from WhatsApp webhook payload."""
        if not payload.message:
            payload.message = PayloadMessage(id=f"na-{payload.timestamp.timestamp()}")
        assert payload.message, "Missing message"
        assert payload.message.id, "Missing message ID"
        assert payload.from_, "Missing sender"

        # Parse sender and chat JIDs
        if " in " in payload.from_:
            sender_jid, chat_jid = payload.from_.split(" in ")
        else:
            sender_jid = chat_jid = payload.from_

        return cls(
            **BaseMessage(
                message_id=payload.message.id,
                text=cls._extract_message_text(payload),
                chat_jid=chat_jid,
                sender_jid=sender_jid,
                timestamp=payload.timestamp,
                reply_to_id=payload.message.replied_id,
                media_url=cls._extract_media_url(payload),
            ).model_dump()
        )

    @staticmethod
    def _extract_media_url(payload: WhatsAppWebhookPayload) -> Optional[str]:
        """Get media URL from first available media attachment."""
        media_types = ["image", "video", "audio", "document", "sticker"]

        for media_type in media_types:
            if media := getattr(payload, media_type, None):
                if media.media_path:
                    return media.media_path

        return None

    @staticmethod
    def _extract_message_text(payload: WhatsAppWebhookPayload) -> Optional[str]:
        """Extract message text based on content type."""
        # Return direct message text if available
        if payload.message.text:
            return payload.message.text

        # Map content types to their caption attributes
        content_types = {
            "image": "caption",
            "video": "caption",
            "audio": "caption",
            "document": "caption",
            "sticker": "caption",
            "contact": "display_name",
            "location": "name",
            "poll": "question",
            "list": "title",
            "order": "message",
        }

        # Check each content type for available caption
        for content_type, caption_attr in content_types.items():
            if content := getattr(payload, content_type, None):
                if caption := getattr(content, caption_attr, None):
                    return f"[[Attached {content_type.title()}]] {caption}"

        return None


Message.model_rebuild()
