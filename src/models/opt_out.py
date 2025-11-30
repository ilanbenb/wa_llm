from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, Column, DateTime

from whatsapp.jid import normalize_jid


class OptOut(SQLModel, table=True):
    __tablename__: str = "opt_out"

    jid: str = Field(primary_key=True, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    @classmethod
    def normalize(cls, value: str) -> str:
        return normalize_jid(value)
