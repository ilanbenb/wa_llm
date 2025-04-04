from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

from whatsapp.jid import normalize_jid

if TYPE_CHECKING:
    from .group import Group
    from .message import Message


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


Sender.model_rebuild()
