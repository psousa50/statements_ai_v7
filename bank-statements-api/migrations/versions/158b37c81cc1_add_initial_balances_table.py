"""add_initial_balances_table

Revision ID: 158b37c81cc1
Revises: 8de22f0bf3aa
Create Date: 2025-06-19 17:47:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "158b37c81cc1"
down_revision: Union[str, None] = "8de22f0bf3aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create initial_balances table
    op.create_table(
        "initial_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance_date", sa.Date(), nullable=False),
        sa.Column("balance_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="initial_balances_source_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="initial_balances_pkey"),
        sa.UniqueConstraint("source_id", "balance_date", name="uq_initial_balance_source_date"),
    )


def downgrade() -> None:
    # Drop initial_balances table
    op.drop_table("initial_balances")
