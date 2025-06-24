"""group_forward_url

Revision ID: bbba88e22126
Revises: 5a9be1edde3d
Create Date: 2025-06-20 10:11:33.663205

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bbba88e22126"
down_revision: Union[str, None] = "5a9be1edde3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "group",
        sa.Column("forward_url", sa.Text(), nullable=True),
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column("group", "forward_url")
