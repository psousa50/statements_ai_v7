"""rename_source_to_account

Revision ID: 86d7516d9eff
Revises: f87f1cf4813d
Create Date: 2025-06-21 10:24:10.633750

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "86d7516d9eff"
down_revision: Union[str, None] = "f87f1cf4813d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the sources table to accounts
    op.rename_table("sources", "accounts")

    op.alter_column("transactions", "source_id", new_column_name="account_id")
    op.alter_column("file_analysis_metadata", "source_id", new_column_name="account_id")
    op.alter_column("initial_balances", "source_id", new_column_name="account_id")

    # Update foreign key constraint names to reflect the new table name
    # Note: PostgreSQL will automatically update the foreign key references


def downgrade() -> None:
    # Reverse the changes
    op.alter_column("transactions", "account_id", new_column_name="source_id")
    op.alter_column("file_analysis_metadata", "account_id", new_column_name="source_id")
    op.alter_column("initial_balances", "account_id", new_column_name="source_id")

    # Rename the accounts table back to sources
    op.rename_table("accounts", "sources")
