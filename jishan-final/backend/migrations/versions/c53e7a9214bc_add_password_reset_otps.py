"""Add one-time password-reset verification codes.

Revision ID: c53e7a9214bc
Revises: b42f8c31d7a0
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa


revision = "c53e7a9214bc"
down_revision = "b42f8c31d7a0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_reset_otps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_password_reset_otps_user_id",
        "password_reset_otps",
        ["user_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_password_reset_otps_user_id",
        table_name="password_reset_otps",
    )
    op.drop_table("password_reset_otps")
