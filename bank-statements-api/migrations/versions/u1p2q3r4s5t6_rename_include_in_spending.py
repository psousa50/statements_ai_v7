"""Rename include_in_spending to exclude_from_spending and invert values

Revision ID: u1p2q3r4s5t6
Revises: t0o1p2q3r4s5
Create Date: 2026-05-22 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "u1p2q3r4s5t6"
down_revision: Union[str, None] = "s9n0o1p2q3r4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("exclude_from_spending", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute("UPDATE categories SET exclude_from_spending = NOT include_in_spending")
    op.drop_column("categories", "include_in_spending")


def downgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("include_in_spending", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.execute("UPDATE categories SET include_in_spending = NOT exclude_from_spending")
    op.drop_column("categories", "exclude_from_spending")
