"""Add allow_public_proposals to zones

Revision ID: i0j1k2l3m456
Revises: h9i0j1k2l345
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i0j1k2l3m456'
down_revision: Union[str, None] = 'h9i0j1k2l345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add allow_public_proposals column to zones table
    # Default is False - only partners/organizers can create sessions by default
    op.add_column(
        'zones',
        sa.Column('allow_public_proposals', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('zones', 'allow_public_proposals')
