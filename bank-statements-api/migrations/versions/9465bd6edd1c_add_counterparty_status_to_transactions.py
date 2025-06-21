"""add_counterparty_status_to_transactions

Revision ID: 9465bd6edd1c
Revises: 27a453245b7c
Create Date: 2025-06-21 17:32:17.636797

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9465bd6edd1c"
down_revision: Union[str, None] = "27a453245b7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the counterparty_status enum
    counterparty_status_enum = postgresql.ENUM("unprocessed", "inferred", "confirmed", name="counterpartystatus")
    counterparty_status_enum.create(op.get_bind())

    # Add the counterparty_status column to the transactions table
    op.add_column(
        "transactions",
        sa.Column(
            "counterparty_status",
            counterparty_status_enum,
            nullable=False,
            server_default="unprocessed",
        ),
    )


def downgrade() -> None:
    # Remove the counterparty_status column
    op.drop_column("transactions", "counterparty_status")

    # Drop the enum
    counterparty_status_enum = postgresql.ENUM("unprocessed", "inferred", "confirmed", name="counterpartystatus")
    counterparty_status_enum.drop(op.get_bind())
