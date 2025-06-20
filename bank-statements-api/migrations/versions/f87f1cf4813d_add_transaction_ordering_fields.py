"""add_transaction_ordering_fields

Revision ID: f87f1cf4813d
Revises: 158b37c81cc1
Create Date: 2025-06-20 12:36:20.738158

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f87f1cf4813d"
down_revision: Union[str, None] = "158b37c81cc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create source_type enum type
    source_type = postgresql.ENUM("upload", "manual", name="sourcetype", create_type=False)
    source_type.create(op.get_bind())

    # Add new columns to transactions table
    op.add_column("transactions", sa.Column("row_index", sa.Integer(), nullable=True))
    op.add_column(
        "transactions",
        sa.Column("sort_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "transactions",
        sa.Column("source_type", source_type, nullable=False, server_default="upload"),
    )
    op.add_column(
        "transactions",
        sa.Column("manual_position_after", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint for manual_position_after
    op.create_foreign_key(
        "fk_transactions_manual_position_after",
        "transactions",
        "transactions",
        ["manual_position_after"],
        ["id"],
    )

    # Create index on sort_index for performance
    op.create_index(
        "ix_transactions_sort_index",
        "transactions",
        ["sort_index"],
    )

    # Create composite index for efficient ordering queries
    op.create_index(
        "ix_transactions_date_sort_index",
        "transactions",
        ["date", "sort_index"],
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_transactions_date_sort_index", table_name="transactions")
    op.drop_index("ix_transactions_sort_index", table_name="transactions")

    # Drop foreign key constraint
    op.drop_constraint("fk_transactions_manual_position_after", "transactions", type_="foreignkey")

    # Drop columns
    op.drop_column("transactions", "manual_position_after")
    op.drop_column("transactions", "source_type")
    op.drop_column("transactions", "sort_index")
    op.drop_column("transactions", "row_index")

    # Drop source_type enum type
    source_type = postgresql.ENUM("upload", "manual", name="sourcetype")
    source_type.drop(op.get_bind())
