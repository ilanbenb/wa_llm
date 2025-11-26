"""remove group forward url

Revision ID: 781037dc30ec
Revises: bbba88e22126
Create Date: 2025-11-27 00:30:25.118912

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '781037dc30ec'
down_revision: Union[str, None] = 'bbba88e22126'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("group", "forward_url")


def downgrade() -> None:
    op.add_column(
        "group",
        sa.Column("forward_url", sa.Text(), nullable=True),
    )
