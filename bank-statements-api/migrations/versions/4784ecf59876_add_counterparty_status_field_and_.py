"""Add counterparty_status field and update categorization enum

Revision ID: 4784ecf59876
Revises: eb5629bab0d5
Create Date: 2025-06-27 22:43:00.519955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4784ecf59876"
down_revision: Union[str, None] = "eb5629bab0d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the CounterpartyStatus enum
    counterparty_status_enum = sa.Enum("UNPROCESSED", "RULE_BASED", "MANUAL", "FAILURE", name="counterpartystatus")
    counterparty_status_enum.create(op.get_bind(), checkfirst=True)

    # Add the counterparty_status column to transactions
    op.add_column(
        "transactions", sa.Column("counterparty_status", counterparty_status_enum, nullable=False, server_default="UNPROCESSED")
    )

    # Add new enum values to CategorizationStatus enum outside of transaction
    # Note: This needs to be done outside a transaction block in PostgreSQL
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE categorizationstatus ADD VALUE 'RULE_BASED'")
        op.execute("ALTER TYPE categorizationstatus ADD VALUE 'MANUAL'")

    # Update existing CATEGORIZED entries to RULE_BASED (assuming they were system-assigned)
    op.execute("UPDATE transactions SET categorization_status = 'RULE_BASED' WHERE categorization_status = 'CATEGORIZED'")


def downgrade() -> None:
    # Remove the counterparty_status column
    op.drop_column("transactions", "counterparty_status")

    # Drop the CounterpartyStatus enum
    op.execute("DROP TYPE IF EXISTS counterpartystatus")

    # Revert categorization status changes back to CATEGORIZED
    op.execute(
        "UPDATE transactions SET categorization_status = 'CATEGORIZED' WHERE categorization_status IN ('RULE_BASED', 'MANUAL')"
    )
