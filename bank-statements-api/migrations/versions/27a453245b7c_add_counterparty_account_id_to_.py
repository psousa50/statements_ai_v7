"""add_counterparty_account_id_to_transactions

Revision ID: 27a453245b7c
Revises: 86d7516d9eff
Create Date: 2025-06-21 16:08:38.523752

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "27a453245b7c"
down_revision: Union[str, None] = "86d7516d9eff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add counterparty_account_id column to transactions table
    op.add_column("transactions", sa.Column("counterparty_account_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_transactions_counterparty_account_id",
        "transactions",
        "accounts",
        ["counterparty_account_id"],
        ["id"],
    )

    # Add index for performance
    op.create_index(
        "ix_transactions_counterparty_account_id",
        "transactions",
        ["counterparty_account_id"],
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index("ix_transactions_counterparty_account_id", table_name="transactions")

    # Drop foreign key constraint
    op.drop_constraint("fk_transactions_counterparty_account_id", "transactions", type_="foreignkey")

    # Drop column
    op.drop_column("transactions", "counterparty_account_id")
