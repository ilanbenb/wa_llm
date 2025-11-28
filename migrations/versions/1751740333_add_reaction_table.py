"""add_reaction_table

Revision ID: 1751740333_add_reaction_table
Revises: bbba88e22126
Create Date: 2025-01-16 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1751740333_add_reaction_table"
down_revision: Union[str, None] = "bbba88e22126"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create reaction table
    op.create_table(
        "reaction",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.Column("sender_jid", sa.String(length=255), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["message.message_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sender_jid"],
            ["sender.jid"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better performance
    op.create_index("idx_reaction_message_id", "reaction", ["message_id"], unique=False)
    op.create_index("idx_reaction_sender_jid", "reaction", ["sender_jid"], unique=False)

    # Create unique index to prevent duplicate reactions from same sender on same message
    op.create_index(
        "idx_reaction_unique_message_sender",
        "reaction",
        ["message_id", "sender_jid"],
        unique=True,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_reaction_unique_message_sender", table_name="reaction")
    op.drop_index("idx_reaction_sender_jid", table_name="reaction")
    op.drop_index("idx_reaction_message_id", table_name="reaction")

    # Drop reaction table
    op.drop_table("reaction")
