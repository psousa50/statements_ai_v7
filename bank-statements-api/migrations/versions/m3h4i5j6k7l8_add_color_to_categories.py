"""Add color column to categories

Revision ID: m3h4i5j6k7l8
Revises: l2g3h4i5j6k7
Create Date: 2025-01-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

revision: str = "m3h4i5j6k7l8"
down_revision: Union[str, None] = "l2g3h4i5j6k7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PALETTE = [
    "#ef4444",
    "#f97316",
    "#eab308",
    "#22c55e",
    "#14b8a6",
    "#06b6d4",
    "#3b82f6",
    "#8b5cf6",
    "#d946ef",
    "#ec4899",
    "#f43f5e",
    "#84cc16",
]


def _hash_uuid(uuid_str: str) -> int:
    return sum(ord(c) for c in uuid_str)


def upgrade() -> None:
    op.add_column("categories", sa.Column("color", sa.String(7), nullable=True))

    connection = op.get_bind()
    parents = connection.execute(text("SELECT id FROM categories WHERE parent_id IS NULL")).fetchall()

    for (cat_id,) in parents:
        color_index = _hash_uuid(str(cat_id)) % len(PALETTE)
        color = PALETTE[color_index]
        connection.execute(
            text("UPDATE categories SET color = :color WHERE id = :id"),
            {"color": color, "id": cat_id},
        )


def downgrade() -> None:
    op.drop_column("categories", "color")
