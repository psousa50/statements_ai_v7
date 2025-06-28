"""add_transaction_counterparty_rules_table

Revision ID: 990e449651d8
Revises: 7da2fd4b37ee
Create Date: 2025-06-21 20:08:10.283819

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "990e449651d8"
down_revision: Union[str, None] = "7da2fd4b37ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create transaction_counterparty_rules table
    op.create_table(
        "transaction_counterparty_rules",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "normalized_description",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "counterparty_account_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "min_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "max_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.Enum(
                "MANUAL",
                "AI",
                name="counterpartyrulesource",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["counterparty_account_id"],
            ["accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_description"),
    )
    op.create_index(
        op.f("ix_transaction_counterparty_rules_normalized_description"),
        "transaction_counterparty_rules",
        ["normalized_description"],
        unique=False,
    )


def downgrade() -> None:
    # Drop the table and enum
    op.drop_index(
        op.f("ix_transaction_counterparty_rules_normalized_description"),
        table_name="transaction_counterparty_rules",
    )
    op.drop_table("transaction_counterparty_rules")
    op.execute("DROP TYPE IF EXISTS counterpartyrulesource")
