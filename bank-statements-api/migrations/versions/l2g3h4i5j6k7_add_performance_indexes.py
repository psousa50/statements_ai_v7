"""Add composite indexes for query performance

Revision ID: l2g3h4i5j6k7
Revises: k1f2g3h4i5j6
Create Date: 2024-12-31

"""

from typing import Sequence, Union

from alembic import op

revision: str = "l2g3h4i5j6k7"
down_revision: Union[str, None] = "k1f2g3h4i5j6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_transactions_user_id_date",
        "transactions",
        ["user_id", "date"],
    )
    op.create_index(
        "ix_transactions_user_id_category_id",
        "transactions",
        ["user_id", "category_id"],
    )
    op.create_index(
        "ix_transactions_account_id_date",
        "transactions",
        ["account_id", "date"],
    )
    op.create_index(
        "ix_categories_user_id_parent_id",
        "categories",
        ["user_id", "parent_id"],
    )
    op.create_index(
        "ix_initial_balances_account_id_balance_date",
        "initial_balances",
        ["account_id", "balance_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_initial_balances_account_id_balance_date", table_name="initial_balances")
    op.drop_index("ix_categories_user_id_parent_id", table_name="categories")
    op.drop_index("ix_transactions_account_id_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id_category_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id_date", table_name="transactions")
