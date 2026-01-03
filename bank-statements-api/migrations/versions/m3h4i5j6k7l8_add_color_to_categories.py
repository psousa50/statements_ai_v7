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
    "#a78bfa",
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#f472b6",
    "#22d3ee",
    "#fb7185",
    "#818cf8",
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
