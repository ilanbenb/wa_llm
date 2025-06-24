from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator
from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
    Index,
    ARRAY,
    Column,
    String,
    select,
    cast,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from whatsapp.jid import normalize_jid

if TYPE_CHECKING:
    from .message import Message
    from .sender import Sender


class BaseGroup(SQLModel):
    group_jid: str = Field(primary_key=True, max_length=255)
    group_name: Optional[str] = Field(default=None, max_length=255)
    group_topic: Optional[str] = Field(default=None)
    owner_jid: Optional[str] = Field(
        max_length=255, foreign_key="sender.jid", nullable=True, default=None
    )
    managed: bool = Field(default=False)
    forward_url: Optional[str] = Field(default=None, nullable=True)
    notify_on_spam: bool = Field(default=False)
    community_keys: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )

    last_ingest: datetime = Field(default_factory=datetime.now)
    last_summary_sync: datetime = Field(default_factory=datetime.now)

    @field_validator("group_jid", "owner_jid", mode="before")
    @classmethod
    def normalize(cls, value: Optional[str]) -> str:
        return normalize_jid(value) if value else None


class Group(BaseGroup, table=True):
    owner: Optional["Sender"] = Relationship(back_populates="groups_owned")
    messages: List["Message"] = Relationship(back_populates="group")

    __table_args__ = (
        Index("idx_group_community_keys", "community_keys", postgresql_using="gin"),
    )

    async def get_related_community_groups(
        self, session: AsyncSession
    ) -> List["Group"]:
        """
        Fetches all other groups that share at least one community key with this group.

        Args:
            session: AsyncSession instance.

        Returns:
            List[Group]: List of groups sharing any community keys, excluding self.
        """
        if not self.community_keys:
            return []

        query = (
            select(Group)
            .where(Group.group_jid != self.group_jid)  # Exclude self
            .where(
                cast(Group.community_keys, ARRAY(String)).op("&&")(self.community_keys)
            )
        )

        result = await session.exec(query)  # Correct async execution
        return result.all()


Group.model_rebuild()
