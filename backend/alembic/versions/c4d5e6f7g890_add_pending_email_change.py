"""Add pending email change fields to users

Revision ID: c4d5e6f7g890
Revises: b3d4e5f6a789
Create Date: 2026-02-01 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7g890'
down_revision: Union[str, Sequence[str], None] = 'b3d4e5f6a789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add pending email change columns
    op.add_column(
        'users',
        sa.Column('pending_email', sa.String(255), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('pending_email_token', sa.String(64), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('pending_email_sent_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'pending_email_sent_at')
    op.drop_column('users', 'pending_email_token')
    op.drop_column('users', 'pending_email')
