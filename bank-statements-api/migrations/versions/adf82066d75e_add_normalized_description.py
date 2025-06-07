"""add_normalized_description

Revision ID: adf82066d75e
Revises: remove_uploaded_file_id
Create Date: 2025-05-28 09:02:25.307308

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "adf82066d75e"
down_revision: Union[str, None] = "remove_uploaded_file_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add normalized_description column
    op.add_column("transactions", sa.Column("normalized_description", sa.String(), nullable=False))

    # Create index for normalized_description
    op.create_index(
        "ix_transactions_normalized_description",
        "transactions",
        ["normalized_description"],
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index("ix_transactions_normalized_description", table_name="transactions")

    # Drop column
    op.drop_column("transactions", "normalized_description")
