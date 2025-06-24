"""add alert_on_spam to group table

Revision ID: 5a9be1edde3d
Revises: f26c6bacce0b
Create Date: 2025-06-12 19:56:15.892122

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a9be1edde3d"
down_revision: Union[str, None] = "f26c6bacce0b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """
    Add alert_on_spam column to group table.
    This boolean column will track whether groups should alert on spam detection.
    Default value is False for all existing groups.
    """
    # Add the alert_on_spam column with default value False
    op.add_column(
        "group",
        sa.Column(
            "notify_on_spam",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """
    Remove alert_on_spam column from group table.
    """
    op.drop_column("group", "notify_on_spam")
