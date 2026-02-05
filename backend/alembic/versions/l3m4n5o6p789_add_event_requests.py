"""add_event_requests

Revision ID: l3m4n5o6p789
Revises: c8eb4f8f5fb5
Create Date: 2026-02-05 10:00:00.000000

Issue #92 - Self-service event creation.
Adds event_requests table for user-submitted event proposals.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'l3m4n5o6p789'
down_revision: Union[str, Sequence[str], None] = 'c8eb4f8f5fb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create event_requests table (Issue #92)."""
    op.create_table(
        'event_requests',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('requester_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),

        # Event details
        sa.Column('event_title', sa.String(length=255), nullable=False),
        sa.Column('event_slug', sa.String(length=100), nullable=False),
        sa.Column('event_description', sa.String(), nullable=True),
        sa.Column('event_start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_location_name', sa.String(length=255), nullable=True),
        sa.Column('event_city', sa.String(length=100), nullable=True),
        sa.Column('event_country_code', sa.String(length=2), nullable=True),
        sa.Column('event_region', sa.String(length=50), nullable=True),
        sa.Column('event_timezone', sa.String(length=50), nullable=False, server_default='Europe/Paris'),

        # Organization details
        sa.Column('organization_name', sa.String(length=255), nullable=False),
        sa.Column('organization_slug', sa.String(length=100), nullable=False),
        sa.Column('organization_contact_email', sa.String(length=255), nullable=True),
        sa.Column('organization_legal_number', sa.String(length=100), nullable=True),

        # Message from requester
        sa.Column('requester_message', sa.String(length=2000), nullable=True),

        # Review fields
        sa.Column('reviewed_by_id', UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_comment', sa.String(length=2000), nullable=True),

        # Result (filled upon approval)
        sa.Column('created_exhibition_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_organization_id', UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_exhibition_id'], ['exhibitions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_organization_id'], ['organizations.id'], ondelete='SET NULL'),
    )

    # Create indexes for common queries
    op.create_index('ix_event_requests_status', 'event_requests', ['status'])
    op.create_index('ix_event_requests_requester_id', 'event_requests', ['requester_id'])
    op.create_index('ix_event_requests_event_city', 'event_requests', ['event_city'])
    op.create_index('ix_event_requests_event_region', 'event_requests', ['event_region'])
    op.create_index('ix_event_requests_event_start_date', 'event_requests', ['event_start_date'])


def downgrade() -> None:
    """Remove event_requests table."""
    op.drop_index('ix_event_requests_event_start_date', table_name='event_requests')
    op.drop_index('ix_event_requests_event_region', table_name='event_requests')
    op.drop_index('ix_event_requests_event_city', table_name='event_requests')
    op.drop_index('ix_event_requests_requester_id', table_name='event_requests')
    op.drop_index('ix_event_requests_status', table_name='event_requests')
    op.drop_table('event_requests')
