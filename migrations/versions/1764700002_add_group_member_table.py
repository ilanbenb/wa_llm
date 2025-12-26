"""add group member table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groupmember",
        sa.Column("group_jid", sa.String(), nullable=False),
        sa.Column("sender_jid", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_jid"],
            ["group.group_jid"],
        ),
        sa.ForeignKeyConstraint(
            ["sender_jid"],
            ["sender.jid"],
        ),
        sa.PrimaryKeyConstraint("group_jid", "sender_jid"),
    )


def downgrade() -> None:
    op.drop_table("groupmember")
