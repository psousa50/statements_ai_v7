"""Add category_kind enum column and drop is_discretionary

Revision ID: x4s5t6u7v8w9
Revises: w3r4s5t6u7v8
Create Date: 2026-05-23 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "x4s5t6u7v8w9"
down_revision: Union[str, None] = "w3r4s5t6u7v8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE category_kind AS ENUM ('need', 'comfort', 'unplanned', 'want')")
    op.add_column(
        "categories",
        sa.Column(
            "kind",
            sa.Enum("need", "comfort", "unplanned", "want", name="category_kind"),
            nullable=False,
            server_default="need",
        ),
    )
    op.execute("UPDATE categories SET kind = 'comfort' WHERE is_discretionary = true")
    op.drop_column("categories", "is_discretionary")


def downgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("is_discretionary", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute("UPDATE categories SET is_discretionary = true WHERE kind IN ('comfort', 'want')")
    op.drop_column("categories", "kind")
    op.execute("DROP TYPE category_kind")
