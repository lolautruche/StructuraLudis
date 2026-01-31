"""Add email verification fields to users

Revision ID: b3d4e5f6a789
Revises: 7ef43afa9420
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3d4e5f6a789'
down_revision: Union[str, Sequence[str], None] = '7ef43afa9420'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add email verification columns
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'users',
        sa.Column('email_verification_token', sa.String(64), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Mark all existing users as verified (they registered before this feature)
    op.execute("UPDATE users SET email_verified = true")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'email_verification_sent_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
