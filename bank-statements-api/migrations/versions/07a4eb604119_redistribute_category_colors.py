"""redistribute_category_colors

Revision ID: 07a4eb604119
Revises: m3h4i5j6k7l8
Create Date: 2026-01-03 11:44:48.673342

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text

revision: str = "07a4eb604119"
down_revision: Union[str, None] = "m3h4i5j6k7l8"
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


def upgrade() -> None:
    connection = op.get_bind()
    parents = connection.execute(
        text("SELECT id FROM categories WHERE parent_id IS NULL ORDER BY name")
    ).fetchall()

    for i, (cat_id,) in enumerate(parents):
        color = PALETTE[i % len(PALETTE)]
        connection.execute(
            text("UPDATE categories SET color = :color WHERE id = :id"),
            {"color": color, "id": cat_id},
        )


def downgrade() -> None:
    pass
