"""add kb_topic_message table

Revision ID: a1b2c3d4e5f6
Revises: 8c847c475c9c
Create Date: 2025-12-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8c847c475c9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kb_topic_message",
        sa.Column("kb_topic_id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["kb_topic_id"],
            ["kbtopic.id"],
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["message.message_id"],
        ),
        sa.PrimaryKeyConstraint("kb_topic_id", "message_id"),
    )
    op.create_index(
        "ix_kb_topic_message_kb_topic_id",
        "kb_topic_message",
        ["kb_topic_id"],
        unique=False,
    )
    op.create_index(
        "ix_kb_topic_message_message_id",
        "kb_topic_message",
        ["message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_kb_topic_message_message_id", table_name="kb_topic_message")
    op.drop_index("ix_kb_topic_message_kb_topic_id", table_name="kb_topic_message")
    op.drop_table("kb_topic_message")
