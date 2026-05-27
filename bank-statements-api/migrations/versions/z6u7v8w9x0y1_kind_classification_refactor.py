"""Rename existing kind to priority, add new structural kind and is_regular

Revision ID: z6u7v8w9x0y1
Revises: y5t6u7v8w9x0
Create Date: 2026-05-25 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "z6u7v8w9x0y1"
down_revision: Union[str, None] = "y5t6u7v8w9x0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE category_kind RENAME TO category_priority")
    op.alter_column("categories", "kind", new_column_name="priority")

    op.execute("CREATE TYPE category_kind AS ENUM ('expense', 'income', 'transfer', 'reimbursable')")
    op.add_column(
        "categories",
        sa.Column(
            "kind",
            sa.Enum("expense", "income", "transfer", "reimbursable", name="category_kind"),
            nullable=False,
            server_default="expense",
        ),
    )
    op.execute("UPDATE categories SET kind = 'transfer' WHERE exclude_from_spending = true")

    op.drop_column("categories", "exclude_from_spending")

    op.add_column(
        "categories",
        sa.Column("is_regular", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("categories", "is_regular")

    op.add_column(
        "categories",
        sa.Column("exclude_from_spending", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute("UPDATE categories SET exclude_from_spending = true WHERE kind IN ('transfer', 'reimbursable')")

    op.drop_column("categories", "kind")
    op.execute("DROP TYPE category_kind")

    op.alter_column("categories", "priority", new_column_name="kind")
    op.execute("ALTER TYPE category_priority RENAME TO category_kind")
