"""refactor topic message 1:N and set null

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add kb_topic_id to message
    op.add_column("message", sa.Column("kb_topic_id", sa.String(), nullable=True))
    
    # 2. Add foreign key with ON DELETE SET NULL
    op.create_foreign_key(
        "fk_message_kb_topic_id_kbtopic",
        "message",
        "kbtopic",
        ["kb_topic_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 3. Drop existing many-to-many table
    op.drop_table("kb_topic_message")


def downgrade() -> None:
    # 1. Recreate kb_topic_message table
    op.create_table(
        "kb_topic_message",
        sa.Column("kb_topic_id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["kb_topic_id"],
            ["kbtopic.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["message.message_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("kb_topic_id", "message_id"),
    )
    
    # 2. Recreate indices
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
    
    # 3. Drop foreign key and column from message
    op.drop_constraint("fk_message_kb_topic_id_kbtopic", "message", type_="foreignkey")
    op.drop_column("message", "kb_topic_id")
