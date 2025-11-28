from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime

from whatsapp.jid import normalize_jid
from .webhook import WhatsAppWebhookPayload

if TYPE_CHECKING:
    from .message import Message
    from .sender import Sender


class BaseReaction(SQLModel):
    """Base reaction model for WhatsApp message reactions."""

    # Primary key - auto-increment ID
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to the message being reacted to
    message_id: str = Field(max_length=255, foreign_key="message.message_id")

    # Foreign key to the sender who reacted
    sender_jid: str = Field(max_length=255, foreign_key="sender.jid")

    # The actual reaction content (emoji)
    emoji: str = Field(max_length=10)

    # Timestamp when the reaction was created
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    @field_validator("sender_jid", mode="before")
    @classmethod
    def normalize_sender_jid(cls, value: str) -> str:
        """Normalize sender JID to ensure consistency."""
        return normalize_jid(value)


class Reaction(BaseReaction, table=True):
    """Reaction model for database storage."""

    # Relationships
    message: Optional["Message"] = Relationship(
        back_populates="reactions", sa_relationship_kwargs={"lazy": "selectin"}
    )
    sender: Optional["Sender"] = Relationship(
        back_populates="reactions", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    def from_webhook(cls, payload: WhatsAppWebhookPayload) -> "Reaction":
        """Create Reaction instance from WhatsApp webhook payload."""
        if not payload.reaction:
            raise ValueError("Missing reaction in webhook payload")

        if not payload.reaction.id:
            raise ValueError("Missing reaction message ID")

        if not payload.reaction.message:
            raise ValueError("Missing reaction emoji")

        if not payload.from_:
            raise ValueError("Missing sender in webhook payload")

        # Parse sender JID from the 'from' field
        # Format can be "sender_jid" or "sender_jid in group_jid"
        if " in " in payload.from_:
            sender_jid, _ = payload.from_.split(" in ")
        else:
            sender_jid = payload.from_

        return cls(
            message_id=payload.reaction.id,
            sender_jid=sender_jid,
            emoji=payload.reaction.message,
            timestamp=payload.timestamp,
        )

    @classmethod
    async def upsert_reaction(cls, session, reaction: "Reaction") -> "Reaction":
        """
        Custom upsert method for reactions that handles auto-increment primary key.
        Updates existing reaction or creates new one based on message_id + sender_jid.
        """
        from sqlalchemy.dialects.postgresql import insert
        from sqlmodel import select

        # Prepare data for insert (exclude id field)
        insert_data = {
            "message_id": reaction.message_id,
            "sender_jid": reaction.sender_jid,
            "emoji": reaction.emoji,
            "timestamp": reaction.timestamp,
        }

        # Create insert statement
        stmt = insert(cls).values(**insert_data)

        # Use the unique constraint (message_id, sender_jid) for conflict resolution
        stmt = stmt.on_conflict_do_update(
            index_elements=["message_id", "sender_jid"],
            set_={
                "emoji": stmt.excluded.emoji,
                "timestamp": stmt.excluded.timestamp,
            },
        )

        # Execute the upsert
        await session.exec(stmt)

        # Query for the updated/created reaction
        select_stmt = select(cls).where(
            cls.message_id == reaction.message_id, cls.sender_jid == reaction.sender_jid
        )
        result = await session.exec(select_stmt)
        return result.first()


# Build the model to resolve relationships
Reaction.model_rebuild()
