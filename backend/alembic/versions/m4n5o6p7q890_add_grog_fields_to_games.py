"""add_grog_fields_to_games

Revision ID: m4n5o6p7q890
Revises: l3m4n5o6p789
Create Date: 2026-02-05 10:00:00.000000

Issue #55 - Add GROG external database sync fields to games table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = 'm4n5o6p7q890'
down_revision: Union[str, Sequence[str], None] = 'l3m4n5o6p789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add GROG fields to games table (#55)."""
    op.add_column('games', sa.Column('external_provider', sa.String(length=50), nullable=True))
    op.add_column('games', sa.Column('external_url', sa.String(length=500), nullable=True))
    op.add_column('games', sa.Column('cover_image_url', sa.String(length=500), nullable=True))
    op.add_column('games', sa.Column('themes', ARRAY(sa.String()), nullable=True))
    op.add_column('games', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True))

    # Create composite index for external provider lookups
    op.create_index(
        'ix_games_external_provider_id',
        'games',
        ['external_provider', 'external_provider_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove GROG fields from games table."""
    op.drop_index('ix_games_external_provider_id', table_name='games')
    op.drop_column('games', 'last_synced_at')
    op.drop_column('games', 'themes')
    op.drop_column('games', 'cover_image_url')
    op.drop_column('games', 'external_url')
    op.drop_column('games', 'external_provider')
