"""remove_counterparty_status_from_transactions

Revision ID: eb5629bab0d5
Revises: 068134e29474
Create Date: 2025-06-26 20:30:14.978361

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eb5629bab0d5"
down_revision: Union[str, None] = "068134e29474"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove counterparty_status column from transactions table
    op.drop_column("transactions", "counterparty_status")

    # Drop the counterpartystatus enum type
    op.execute("DROP TYPE IF EXISTS counterpartystatus")


def downgrade() -> None:
    # Recreate the counterpartystatus enum
    op.execute("CREATE TYPE counterpartystatus AS ENUM ('unprocessed', 'inferred', 'confirmed')")

    # Add back the counterparty_status column
    op.add_column(
        "transactions",
        sa.Column(
            "counterparty_status",
            sa.Enum(
                "unprocessed",
                "inferred",
                "confirmed",
                name="counterpartystatus",
            ),
            nullable=False,
            server_default="unprocessed",
        ),
    )
