"""Add enhancement_rules table

Revision ID: 348432665689
Revises: 990e449651d8
Create Date: 2025-06-25 19:32:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "348432665689"
down_revision: Union[str, None] = "990e449651d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums first, ignoring if they exist
    try:
        op.execute("CREATE TYPE matchtype AS ENUM ('exact', 'prefix', 'infix')")
    except Exception:
        pass  # Type already exists

    try:
        op.execute("CREATE TYPE enhancementrulesource AS ENUM ('MANUAL', 'AI')")
    except Exception:
        pass  # Type already exists

    # Create enhancement_rules table
    op.execute(
        """
        CREATE TABLE enhancement_rules (
            id UUID PRIMARY KEY,
            normalized_description_pattern VARCHAR NOT NULL,
            match_type matchtype NOT NULL,
            min_amount NUMERIC(10, 2),
            max_amount NUMERIC(10, 2),
            start_date DATE,
            end_date DATE,
            category_id UUID REFERENCES categories(id),
            counterparty_account_id UUID REFERENCES accounts(id),
            source enhancementrulesource NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """
    )

    # Create index on normalized_description_pattern for faster lookups
    op.create_index(
        "ix_enhancement_rules_normalized_description_pattern",
        "enhancement_rules",
        ["normalized_description_pattern"],
    )


def downgrade() -> None:
    # Drop the table and indexes
    op.drop_index(
        "ix_enhancement_rules_normalized_description_pattern",
        table_name="enhancement_rules",
    )
    op.drop_table("enhancement_rules")

    # Drop the enum types
    op.execute("DROP TYPE enhancementrulesource")
    op.execute("DROP TYPE matchtype")
