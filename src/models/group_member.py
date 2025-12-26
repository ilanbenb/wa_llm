from typing import Optional

from sqlmodel import Field, SQLModel


class GroupMember(SQLModel, table=True):
    group_jid: str = Field(foreign_key="group.group_jid", primary_key=True)
    sender_jid: str = Field(foreign_key="sender.jid", primary_key=True)
    role: Optional[str] = Field(default="participant")
