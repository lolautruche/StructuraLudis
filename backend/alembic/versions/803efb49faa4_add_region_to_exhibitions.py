"""add_region_to_exhibitions

Revision ID: 803efb49faa4
Revises: k2l3m4n5o678
Create Date: 2026-02-04 11:26:17.907151

Issue #94 - Add region field for geographic filtering.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '803efb49faa4'
down_revision: Union[str, Sequence[str], None] = 'k2l3m4n5o678'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add region field to exhibitions for geographic filtering (Issue #94)."""
    op.add_column('exhibitions', sa.Column('region', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove region field from exhibitions."""
    op.drop_column('exhibitions', 'region')
