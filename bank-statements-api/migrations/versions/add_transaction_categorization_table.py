"""add_transaction_categorization_table

Revision ID: bc4f2d9e1a8c
Revises: adf82066d75e
Create Date: 2025-01-03 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bc4f2d9e1a8c"
down_revision: Union[str, None] = "adf82066d75e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create categorization source enum type
    categorization_source = postgresql.ENUM("MANUAL", "AI", name="categorizationsource", create_type=False)
    categorization_source.create(op.get_bind())

    # Create transaction_categorization table
    op.create_table(
        "transaction_categorization",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_description", sa.String(), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", categorization_source, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_description"),
    )

    # Create index on normalized_description for performance
    op.create_index(
        "ix_transaction_categorization_normalized_description",
        "transaction_categorization",
        ["normalized_description"],
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index(
        "ix_transaction_categorization_normalized_description",
        table_name="transaction_categorization",
    )

    # Drop table
    op.drop_table("transaction_categorization")

    # Drop categorization source enum type
    categorization_source = postgresql.ENUM("MANUAL", "AI", name="categorizationsource")
    categorization_source.drop(op.get_bind())
