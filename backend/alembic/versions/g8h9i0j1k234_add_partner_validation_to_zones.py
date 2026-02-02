"""Add partner_validation_enabled to zones table (Issue #10).

This migration adds the partner_validation_enabled column to zones.
When enabled, partners managing this zone can validate sessions themselves
instead of requiring organizer approval.

Revision ID: g8h9i0j1k234
Revises: f7g8h9i0j123
Create Date: 2026-02-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g8h9i0j1k234'
down_revision: Union[str, None] = 'f7g8h9i0j123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add partner_validation_enabled column to zones
    # Default is False - organizers must validate sessions
    op.add_column(
        'zones',
        sa.Column(
            'partner_validation_enabled',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        )
    )


def downgrade() -> None:
    op.drop_column('zones', 'partner_validation_enabled')
