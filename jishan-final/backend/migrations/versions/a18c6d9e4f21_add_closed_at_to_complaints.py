"""Add a dedicated complaint closed_at timestamp.

Revision ID: a18c6d9e4f21
Revises: 946b7d1225b6
Create Date: 2026-08-18
"""
from alembic import op
import sqlalchemy as sa


revision = "a18c6d9e4f21"
down_revision = "946b7d1225b6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("complaints", sa.Column("closed_at", sa.DateTime(), nullable=True))

    # Older code stored the close time in resolved_at for directly closed
    # complaints. Preserve the best available close timestamp for existing rows.
    op.execute(
        sa.text(
            """
            UPDATE complaints
            SET closed_at = resolved_at
            WHERE status = 'CLOSED' AND closed_at IS NULL
            """
        )
    )

    # If a CLOSED complaint never had a RESOLVED timeline transition, its old
    # resolved_at value was actually only a close timestamp. Remove that false
    # resolution so historical resolution-time reporting is not inflated.
    op.execute(
        sa.text(
            """
            UPDATE complaints
            SET resolved_at = NULL
            WHERE status = 'CLOSED'
              AND NOT EXISTS (
                  SELECT 1
                  FROM complaint_updates
                  WHERE complaint_updates.complaint_id = complaints.id
                    AND complaint_updates.status = 'RESOLVED'
              )
            """
        )
    )


def downgrade():
    op.drop_column("complaints", "closed_at")
