"""Add an explicit maintenance trade field to users.

Revision ID: b42f8c31d7a0
Revises: a18c6d9e4f21
Create Date: 2026-08-18
"""
from alembic import op
import sqlalchemy as sa


revision = "b42f8c31d7a0"
down_revision = "a18c6d9e4f21"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("trade", sa.String(length=100), nullable=True))

    # Existing staff records used the building column as a trade field. Preserve
    # that information while moving future code to a dedicated column.
    op.execute(
        sa.text(
            """
            UPDATE users
            SET trade = building
            WHERE role = 'STAFF' AND trade IS NULL
            """
        )
    )


def downgrade():
    op.drop_column("users", "trade")
