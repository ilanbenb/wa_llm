"""add last ingest/summarysync

Revision ID: f26c6bacce0b
Revises: 05d84f746fc7
Create Date: 2025-02-19 12:43:36.080722

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f26c6bacce0b"
down_revision: Union[str, None] = "05d84f746fc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # First add the columns as nullable
    op.add_column("group", sa.Column("last_ingest", sa.DateTime(), nullable=True))
    op.add_column("group", sa.Column("last_summary_sync", sa.DateTime(), nullable=True))

    # Set their values
    op.execute(
        """
        UPDATE "group" 
        SET last_ingest = NOW(),
            last_summary_sync = NOW()
        """
    )

    # Now alter the columns to be non-nullable
    op.alter_column("group", "last_ingest", existing_type=sa.DateTime(), nullable=False)
    op.alter_column(
        "group", "last_summary_sync", existing_type=sa.DateTime(), nullable=False
    )


def downgrade():
    op.drop_column("group", "last_ingest")
    op.drop_column("group", "last_summary_sync")
