"""Add user_exhibition_roles table for event-scoped roles (Issue #99).

This migration:
1. Creates the user_exhibition_roles table
2. Migrates existing ORGANIZER users to have exhibition roles
3. Migrates existing PARTNER users based on zone delegations
4. Updates migrated users to global_role='USER'
5. Adds 'ADMIN' to the global_role values

Revision ID: e6f7g8h9i012
Revises: d5e6f7g8h901
Create Date: 2026-02-01 10:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'e6f7g8h9i012'
down_revision: Union[str, None] = 'd5e6f7g8h901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create user_exhibition_roles table
    op.create_table(
        'user_exhibition_roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('exhibition_id', UUID(as_uuid=True), sa.ForeignKey('exhibitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('zone_ids', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
        sa.UniqueConstraint('user_id', 'exhibition_id', name='uq_user_exhibition_role'),
    )

    # Create indexes for common queries
    op.create_index('ix_user_exhibition_roles_user_id', 'user_exhibition_roles', ['user_id'])
    op.create_index('ix_user_exhibition_roles_exhibition_id', 'user_exhibition_roles', ['exhibition_id'])

    # 2. Migrate existing ORGANIZER users
    # For each ORGANIZER, create exhibition roles for all exhibitions in organizations they belong to
    conn = op.get_bind()

    # Find ORGANIZER users and their organizations via group membership
    organizer_data = conn.execute(sa.text("""
        SELECT DISTINCT u.id as user_id, e.id as exhibition_id
        FROM users u
        JOIN user_group_memberships ugm ON ugm.user_id = u.id
        JOIN user_groups ug ON ug.id = ugm.user_group_id
        JOIN exhibitions e ON e.organization_id = ug.organization_id
        WHERE u.global_role = 'ORGANIZER'
    """)).fetchall()

    for row in organizer_data:
        conn.execute(
            sa.text("""
                INSERT INTO user_exhibition_roles (id, user_id, exhibition_id, role, created_at)
                VALUES (:id, :user_id, :exhibition_id, 'ORGANIZER', NOW())
                ON CONFLICT (user_id, exhibition_id) DO NOTHING
            """),
            {"id": str(uuid4()), "user_id": str(row.user_id), "exhibition_id": str(row.exhibition_id)}
        )

    # 3. Migrate existing PARTNER users based on zone delegations
    # For each zone with delegated_to_group_id, find group members and create PARTNER roles
    partner_data = conn.execute(sa.text("""
        SELECT DISTINCT
            u.id as user_id,
            z.exhibition_id,
            array_agg(z.id::text) as zone_ids
        FROM users u
        JOIN user_group_memberships ugm ON ugm.user_id = u.id
        JOIN zones z ON z.delegated_to_group_id = ugm.user_group_id
        WHERE u.global_role = 'PARTNER'
        AND ugm.group_role IN ('OWNER', 'ADMIN')
        GROUP BY u.id, z.exhibition_id
    """)).fetchall()

    for row in partner_data:
        zone_ids_json = row.zone_ids if row.zone_ids else None
        conn.execute(
            sa.text("""
                INSERT INTO user_exhibition_roles (id, user_id, exhibition_id, role, zone_ids, created_at)
                VALUES (:id, :user_id, :exhibition_id, 'PARTNER', :zone_ids, NOW())
                ON CONFLICT (user_id, exhibition_id) DO NOTHING
            """),
            {
                "id": str(uuid4()),
                "user_id": str(row.user_id),
                "exhibition_id": str(row.exhibition_id),
                "zone_ids": zone_ids_json
            }
        )

    # 4. Update migrated users to global_role='USER'
    conn.execute(sa.text("""
        UPDATE users
        SET global_role = 'USER'
        WHERE global_role IN ('ORGANIZER', 'PARTNER')
    """))

    # Note: We don't remove ORGANIZER/PARTNER from the enum as PostgreSQL
    # doesn't support removing enum values easily. They will simply not be used.
    # The code only allows SUPER_ADMIN, ADMIN, USER now.


def downgrade() -> None:
    # Warning: This downgrade will lose exhibition role assignments!
    # It attempts to restore global roles but may not be perfect.

    conn = op.get_bind()

    # Restore ORGANIZER role to users who had it (best effort)
    conn.execute(sa.text("""
        UPDATE users u
        SET global_role = 'ORGANIZER'
        WHERE EXISTS (
            SELECT 1 FROM user_exhibition_roles uer
            WHERE uer.user_id = u.id AND uer.role = 'ORGANIZER'
        )
        AND u.global_role = 'USER'
    """))

    # Restore PARTNER role to users who had it (if not already ORGANIZER)
    conn.execute(sa.text("""
        UPDATE users u
        SET global_role = 'PARTNER'
        WHERE EXISTS (
            SELECT 1 FROM user_exhibition_roles uer
            WHERE uer.user_id = u.id AND uer.role = 'PARTNER'
        )
        AND u.global_role = 'USER'
    """))

    # Drop indexes and table
    op.drop_index('ix_user_exhibition_roles_exhibition_id', table_name='user_exhibition_roles')
    op.drop_index('ix_user_exhibition_roles_user_id', table_name='user_exhibition_roles')
    op.drop_table('user_exhibition_roles')
