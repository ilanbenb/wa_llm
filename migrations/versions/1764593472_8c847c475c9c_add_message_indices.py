"""add_message_indices

Revision ID: 8c847c475c9c
Revises: c48228318e68
Create Date: 2025-12-01 14:51:12.202720

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8c847c475c9c"
down_revision: Union[str, None] = "c48228318e68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add btree index on message.timestamp
    op.create_index(
        "idx_message_timestamp",
        "message",
        ["timestamp"],
        unique=False,
        postgresql_using="btree",
    )

    # Add btree index on message.group_jid
    op.create_index(
        "idx_message_group_jid",
        "message",
        ["group_jid"],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    # Drop the indices in reverse order
    op.drop_index(
        "idx_message_group_jid", table_name="message", postgresql_using="btree"
    )
    op.drop_index(
        "idx_message_timestamp", table_name="message", postgresql_using="btree"
    )
