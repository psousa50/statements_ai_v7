"""add_categorization_confidence_to_transactions

Revision ID: 8de22f0bf3aa
Revises: 4032ce98a1c9
Create Date: 2025-06-01 17:21:09.765265

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8de22f0bf3aa"
down_revision: Union[str, None] = "4032ce98a1c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add categorization_confidence column to transactions table
    op.add_column(
        "transactions",
        sa.Column("categorization_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
    )


def downgrade() -> None:
    # Remove categorization_confidence column from transactions table
    op.drop_column("transactions", "categorization_confidence")
