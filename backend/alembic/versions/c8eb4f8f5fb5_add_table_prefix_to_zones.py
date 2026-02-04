"""add_table_prefix_to_zones

Revision ID: c8eb4f8f5fb5
Revises: 803efb49faa4
Create Date: 2026-02-04 16:44:33.640694

Issue #93 - Add table_prefix field to zones for automatic table numbering.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8eb4f8f5fb5'
down_revision: Union[str, Sequence[str], None] = '803efb49faa4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add table_prefix field to zones (Issue #93)."""
    op.add_column('zones', sa.Column('table_prefix', sa.String(length=30), nullable=True))


def downgrade() -> None:
    """Remove table_prefix field from zones."""
    op.drop_column('zones', 'table_prefix')
