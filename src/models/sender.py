from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

from whatsapp.jid import normalize_jid
from .group_member import GroupMember

if TYPE_CHECKING:
    from .group import Group
    from .message import Message
    from .reaction import Reaction


class BaseSender(SQLModel):
    jid: str = Field(primary_key=True, max_length=255)
    push_name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("jid", mode="before")
    @classmethod
    def normalize(cls, value: str) -> str:
        return normalize_jid(value)


class Sender(BaseSender, table=True):
    messages: List["Message"] = Relationship(back_populates="sender")
    groups_owned: List["Group"] = Relationship(back_populates="owner")
    groups: List["Group"] = Relationship(back_populates="members", link_model=GroupMember)
    # Reactions relationship - one sender can have many reactions
    reactions: List["Reaction"] = Relationship(
        back_populates="sender", sa_relationship_kwargs={"lazy": "selectin"}
    )


Sender.model_rebuild()
