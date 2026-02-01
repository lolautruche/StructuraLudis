"""Add password reset fields.

Revision ID: d5e6f7g8h901
Revises: c4d5e6f7g890
Create Date: 2025-01-31 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7g8h901'
down_revision: Union[str, None] = 'c4d5e6f7g890'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password reset fields to users table
    op.add_column('users', sa.Column('password_reset_token', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('password_reset_sent_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_reset_sent_at')
    op.drop_column('users', 'password_reset_token')
