"""add gin index for message text search

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create GIN index for full-text search on message.text
    # We use COALESCE to handle NULL text values, matching the query usage
    op.create_index(
        "ix_message_text_tsv",
        "message",
        [sa.text("to_tsvector('simple', COALESCE(text, ''))")],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_message_text_tsv", table_name="message", postgresql_using="gin")
