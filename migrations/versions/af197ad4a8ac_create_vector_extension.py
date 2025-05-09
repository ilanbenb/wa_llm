import sqlmodel

"""create vector extension

Revision ID: af197ad4a8ac
Revises: f26c6bacce0b
Create Date: 2025-05-09 10:12:15.717489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af197ad4a8ac'
down_revision: Union[str, None] = 'f26c6bacce0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

def downgrade():
    op.execute("DROP EXTENSION IF EXISTS vector;")
