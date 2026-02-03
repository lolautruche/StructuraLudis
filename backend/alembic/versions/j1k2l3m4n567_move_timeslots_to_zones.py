"""Move time slots from exhibition to zone level (Issue #105)

Revision ID: j1k2l3m4n567
Revises: i0j1k2l3m456
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "j1k2l3m4n567"
down_revision: Union[str, None] = "i0j1k2l3m456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add zone_id column (nullable initially)
    op.add_column(
        "time_slots",
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_time_slots_zone_id",
        "time_slots",
        "zones",
        ["zone_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2. Drop the old exhibition_id FK and column
    op.drop_constraint("time_slots_exhibition_id_fkey", "time_slots", type_="foreignkey")
    op.drop_column("time_slots", "exhibition_id")

    # 3. Make zone_id non-nullable
    op.alter_column("time_slots", "zone_id", nullable=False)


def downgrade() -> None:
    # 1. Add exhibition_id column back (nullable initially)
    op.add_column(
        "time_slots",
        sa.Column("exhibition_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "time_slots_exhibition_id_fkey",
        "time_slots",
        "exhibitions",
        ["exhibition_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2. Drop the zone_id FK and column
    op.drop_constraint("fk_time_slots_zone_id", "time_slots", type_="foreignkey")
    op.drop_column("time_slots", "zone_id")

    # 3. Make exhibition_id non-nullable
    op.alter_column("time_slots", "exhibition_id", nullable=False)
