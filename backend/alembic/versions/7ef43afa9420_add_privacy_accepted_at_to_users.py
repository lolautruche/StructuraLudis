"""Add privacy_accepted_at to users

Revision ID: 7ef43afa9420
Revises: acb21cf6f99d
Create Date: 2026-01-30 11:55:26.864835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7ef43afa9420'
down_revision: Union[str, Sequence[str], None] = 'acb21cf6f99d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('privacy_accepted_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'privacy_accepted_at')
