from typing import ClassVar

from sqlmodel import Field, SQLModel


class KBTopicMessage(SQLModel, table=True):
    __tablename__: ClassVar[str] = "kb_topic_message"
    kb_topic_id: str = Field(foreign_key="kbtopic.id", primary_key=True)
    message_id: str = Field(foreign_key="message.message_id", primary_key=True)
