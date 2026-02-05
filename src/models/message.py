from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime


from whatsapp.jid import normalize_jid, parse_jid, JID
from gowa_sdk.webhooks import WebhookEnvelope, WebhookMessagePayload
from .kb_topic_message import KBTopicMessage

if TYPE_CHECKING:
    from .group import Group
    from .sender import Sender
    from .reaction import Reaction
    from .knowledge_base_topic import KBTopic


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
    def validate_chat_jid(cls, data) -> dict:
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

        if not self.text:
            return False
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
    # Reactions relationship - one message can have many reactions
    reactions: List["Reaction"] = Relationship(
        back_populates="message", sa_relationship_kwargs={"lazy": "selectin"}
    )

    kb_topics: List["KBTopic"] = Relationship(
        back_populates="messages", link_model=KBTopicMessage
    )

    @classmethod
    def from_webhook(cls, payload: WebhookEnvelope) -> "Message":
        """Create Message instance from WhatsApp webhook payload."""
        if payload.event != "message":
            raise ValueError(f"Unsupported webhook event: {payload.event}")

        data = WebhookMessagePayload.model_validate(payload.payload)
        if not data.id:
            timestamp = data.timestamp or payload.timestamp
            if timestamp:
                fallback = timestamp.timestamp()
            else:
                fallback = datetime.now(timezone.utc).timestamp()
            data.id = f"na-{fallback}"

        assert data.id, "Missing message ID"
        assert data.from_, "Missing sender"

        chat_jid = data.chat_id or data.from_
        assert chat_jid, "Missing chat ID"
        sender_jid = data.from_

        return cls(
            **BaseMessage(
                message_id=data.id,
                text=cls._extract_message_text(data),
                chat_jid=chat_jid,
                sender_jid=normalize_jid(sender_jid),
                timestamp=data.timestamp or payload.timestamp or datetime.now(timezone.utc),
                reply_to_id=data.replied_to_id,
                media_url=cls._extract_media_url(data),
            ).model_dump()
        )

    @staticmethod
    def _extract_media_url(payload: WebhookMessagePayload) -> Optional[str]:
        """Get media URL from first available media attachment."""
        media_types = ["image", "video", "audio", "document", "sticker"]

        for media_type in media_types:
            if media := getattr(payload, media_type, None):
                url = Message._extract_media_path(media)
                if url:
                    return url

        return None

    @staticmethod
    def _extract_message_text(payload: WebhookMessagePayload) -> Optional[str]:
        """Extract message text based on content type."""
        # Return direct message text if available
        if payload.text:
            return payload.text

        # Map content types to their caption attributes
        content_types = {
            "image": ["caption"],
            "video": ["caption"],
            "audio": ["caption"],
            "document": ["caption", "file_name", "filename"],
            "sticker": ["caption"],
            "contact": ["display_name", "displayName", "name"],
            "location": ["name", "address"],
            "poll": ["question", "title"],
            "list": ["title", "description"],
            "order": ["message", "order_title", "orderTitle"],
        }

        # Check each content type for available caption
        for content_type, caption_keys in content_types.items():
            if content := getattr(payload, content_type, None):
                caption = Message._extract_caption(content, caption_keys)
                if caption:
                    return f"[[Attached {content_type.title()}]] {caption}"

        return None

    @staticmethod
    def _extract_media_path(media: Any) -> Optional[str]:
        if isinstance(media, str):
            return media
        if isinstance(media, dict):
            for key in ("media_path", "path", "url", "direct_path"):
                value = media.get(key)
                if value:
                    return value
        return None

    @staticmethod
    def _extract_caption(media: Any, keys: list[str]) -> Optional[str]:
        if isinstance(media, dict):
            for key in keys:
                value = media.get(key)
                if value:
                    return str(value)
        return None


Message.model_rebuild()
