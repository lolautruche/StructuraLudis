"""Add exhibition registrations (Issue #77)

Revision ID: k2l3m4n5o678
Revises: j1k2l3m4n567
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'k2l3m4n5o678'
down_revision: Union[str, None] = 'j1k2l3m4n567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add requires_registration on exhibitions
    op.add_column(
        'exhibitions',
        sa.Column(
            'requires_registration',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    # 2. Create the exhibition_registrations table
    op.create_table(
        'exhibition_registrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exhibition_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'registered_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['exhibition_id'],
            ['exhibitions.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'exhibition_id',
            name='uq_user_exhibition_registration'
        ),
    )
    op.create_index(
        'ix_exhibition_registrations_exhibition_id',
        'exhibition_registrations',
        ['exhibition_id']
    )


def downgrade() -> None:
    op.drop_index(
        'ix_exhibition_registrations_exhibition_id',
        table_name='exhibition_registrations'
    )
    op.drop_table('exhibition_registrations')
    op.drop_column('exhibitions', 'requires_registration')
