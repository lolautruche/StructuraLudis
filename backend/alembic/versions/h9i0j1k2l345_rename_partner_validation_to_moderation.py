"""Rename partner_validation_enabled to moderation_required (Issue #10).

This migration renames the column and inverts the logic:
- OLD: partner_validation_enabled=true meant partners can auto-validate
- NEW: moderation_required=false means sessions are auto-validated

Partner sessions are now ALWAYS auto-validated (no moderation needed).
The moderation_required flag only affects public session proposals.

Revision ID: h9i0j1k2l345
Revises: g8h9i0j1k234
Create Date: 2026-02-02 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h9i0j1k2l345'
down_revision: Union[str, None] = 'g8h9i0j1k234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column and invert values
    # partner_validation_enabled=true -> moderation_required=false
    # partner_validation_enabled=false -> moderation_required=true

    # Step 1: Add new column
    op.add_column(
        'zones',
        sa.Column(
            'moderation_required',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        )
    )

    # Step 2: Copy and invert values
    op.execute(
        "UPDATE zones SET moderation_required = NOT partner_validation_enabled"
    )

    # Step 3: Drop old column
    op.drop_column('zones', 'partner_validation_enabled')


def downgrade() -> None:
    # Reverse the process
    op.add_column(
        'zones',
        sa.Column(
            'partner_validation_enabled',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        )
    )

    op.execute(
        "UPDATE zones SET partner_validation_enabled = NOT moderation_required"
    )

    op.drop_column('zones', 'moderation_required')
