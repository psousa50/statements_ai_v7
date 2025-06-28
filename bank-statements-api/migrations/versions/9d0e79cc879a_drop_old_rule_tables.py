"""drop_old_rule_tables

Revision ID: 9d0e79cc879a
Revises: 348432665689
Create Date: 2025-06-25 19:32:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d0e79cc879a"
down_revision: Union[str, None] = "348432665689"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop indexes first
    op.drop_index(
        "ix_transaction_counterparty_rules_normalized_description",
        table_name="transaction_counterparty_rules",
    )
    op.drop_index(
        "ix_transaction_categorization_normalized_description",
        table_name="transaction_categorization",
    )

    # Drop tables
    op.drop_table("transaction_counterparty_rules")
    op.drop_table("transaction_categorization")

    # Drop enum types that are no longer needed
    op.execute("DROP TYPE IF EXISTS counterpartyrulesource")
    op.execute("DROP TYPE IF EXISTS categorizationsource")


def downgrade() -> None:
    # Recreate enum types
    op.execute("CREATE TYPE categorizationsource AS ENUM ('MANUAL', 'AI')")
    op.execute("CREATE TYPE counterpartyrulesource AS ENUM ('MANUAL', 'AI')")

    # Recreate transaction_categorization table
    op.execute(
        """
        CREATE TABLE transaction_categorization (
            id UUID PRIMARY KEY,
            normalized_description VARCHAR NOT NULL,
            category_id UUID NOT NULL REFERENCES categories(id),
            source categorizationsource NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CONSTRAINT uq_transaction_categorization_normalized_description UNIQUE (normalized_description)
        )
    """
    )

    # Recreate transaction_counterparty_rules table
    op.execute(
        """
        CREATE TABLE transaction_counterparty_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            normalized_description VARCHAR NOT NULL,
            counterparty_account_id UUID NOT NULL REFERENCES accounts(id),
            min_amount NUMERIC(10, 2),
            max_amount NUMERIC(10, 2),
            source counterpartyrulesource NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CONSTRAINT uq_transaction_counterparty_rules_normalized_description UNIQUE (normalized_description)
        )
    """
    )

    # Recreate indexes
    op.create_index(
        "ix_transaction_categorization_normalized_description",
        "transaction_categorization",
        ["normalized_description"],
    )
    op.create_index(
        "ix_transaction_counterparty_rules_normalized_description",
        "transaction_counterparty_rules",
        ["normalized_description"],
    )
