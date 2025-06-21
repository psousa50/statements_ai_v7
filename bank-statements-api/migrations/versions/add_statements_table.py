"""Add statements table and update transactions

Revision ID: add_statements_table  
Revises: 9465bd6edd1c
Create Date: 2025-06-21 17:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_statements_table"
down_revision: Union[str, None] = "9465bd6edd1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create statements table
    op.create_table(
        "statements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add statement_id column to transactions table
    op.add_column("transactions", sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_transactions_statement_id", "transactions", "statements", ["statement_id"], ["id"])


def downgrade() -> None:
    # Remove statement_id column and foreign key from transactions
    op.drop_constraint("fk_transactions_statement_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "statement_id")

    # Drop statements table
    op.drop_table("statements")
