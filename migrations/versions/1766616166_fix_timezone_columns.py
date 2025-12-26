"""Fix timezone for last_ingest and last_summary_sync columns

Revision ID: fix_timezone_columns
Revises: e15ea65a6a8f
Create Date: 2025-12-22 21:02:46

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_timezone_columns'
down_revision = 'e15ea65a6a8f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert last_ingest to timezone-aware (TIMESTAMP WITH TIME ZONE)
    # Existing naive timestamps are assumed to be UTC
    op.execute("""
        ALTER TABLE "group" 
        ALTER COLUMN last_ingest TYPE TIMESTAMP WITH TIME ZONE 
        USING last_ingest AT TIME ZONE 'UTC'
    """)
    
    # Convert last_summary_sync to timezone-aware (TIMESTAMP WITH TIME ZONE)
    # Existing naive timestamps are assumed to be UTC
    op.execute("""
        ALTER TABLE "group" 
        ALTER COLUMN last_summary_sync TYPE TIMESTAMP WITH TIME ZONE 
        USING last_summary_sync AT TIME ZONE 'UTC'
    """)


def downgrade() -> None:
    # Revert to naive timestamp (TIMESTAMP WITHOUT TIME ZONE)
    op.execute("""
        ALTER TABLE "group" 
        ALTER COLUMN last_ingest TYPE TIMESTAMP WITHOUT TIME ZONE
    """)
    
    op.execute("""
        ALTER TABLE "group" 
        ALTER COLUMN last_summary_sync TYPE TIMESTAMP WITHOUT TIME ZONE
    """)
