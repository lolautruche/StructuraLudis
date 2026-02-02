"""Add created_by_id to exhibitions table (Issue #99).

This migration adds the created_by_id column to track who created the exhibition.
This is used to identify the "main organizer" who cannot be removed by other organizers.

Revision ID: f7g8h9i0j123
Revises: e6f7g8h9i012
Create Date: 2026-02-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'f7g8h9i0j123'
down_revision: Union[str, None] = 'e6f7g8h9i012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_by_id column to exhibitions
    op.add_column(
        'exhibitions',
        sa.Column(
            'created_by_id',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        )
    )

    # Create index for lookups
    op.create_index(
        'ix_exhibitions_created_by_id',
        'exhibitions',
        ['created_by_id']
    )

    # Attempt to set created_by_id from UserExhibitionRole for existing exhibitions
    # The first ORGANIZER by created_at is considered the creator
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE exhibitions e
        SET created_by_id = (
            SELECT uer.user_id
            FROM user_exhibition_roles uer
            WHERE uer.exhibition_id = e.id
            AND uer.role = 'ORGANIZER'
            ORDER BY uer.created_at ASC
            LIMIT 1
        )
        WHERE e.created_by_id IS NULL
    """))


def downgrade() -> None:
    op.drop_index('ix_exhibitions_created_by_id', table_name='exhibitions')
    op.drop_column('exhibitions', 'created_by_id')
