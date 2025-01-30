import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel

from .jid import normalize_jid, parse_jid
from .webhook import WhatsAppWebhookPayload

if TYPE_CHECKING:
    from .group import Group
    from .sender import Sender


class BaseMessage(SQLModel):
    message_id: str = Field(primary_key=True, max_length=255)
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    text: Optional[str] = Field(default=None)
    chat_jid: str = Field(max_length=255)
    sender_jid: str = Field(max_length=255, foreign_key="sender.jid")
    group_jid: Optional[str] = Field(
        max_length=255,
        foreign_key="group.group_jid",
        nullable=True,
        default=None,
    )
    reply_to_id: Optional[str] = Field(
        default=None, nullable=True
    )

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


class Message(BaseMessage, table=True):
    sender: Optional["Sender"] = Relationship(back_populates="messages")
    group: Optional["Group"] = Relationship(back_populates="messages")
    replies: List["Message"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Message.message_id==foreign(Message.reply_to_id)",
            "remote_side": "Message.message_id",  # Add this to clarify direction
            "backref": "replied_to",
        }
    )

    @classmethod
    def from_webhook(cls, payload: WhatsAppWebhookPayload) -> "Message":
        assert payload.message

        chat_jid = sender_jid = payload.from_
        assert chat_jid

        if " in " in chat_jid:
            sender_jid, chat_jid = chat_jid.split(" in ")

        assert chat_jid
        assert sender_jid
        assert payload.message.id

        return cls(**BaseMessage(
            message_id=payload.message.id,
            text=payload.message.text,
            chat_jid=chat_jid,
            sender_jid=sender_jid,
            timestamp=payload.timestamp,
            reply_to_id=payload.message.replied_id,
        ).model_dump())

Message.model_rebuild()
