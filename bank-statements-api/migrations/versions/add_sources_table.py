"""Add sources table and source_id to transactions

Revision ID: add_sources_table
Revises: add_file_id_to_transactions
Create Date: 2025-05-14 15:15:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_sources_table"
down_revision = "add_file_id_to_transactions"
branch_labels = None
depends_on = None


def upgrade():
    # Create sources table
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("name"),
    )

    # Add source_id column to transactions table
    op.add_column("transactions", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_transactions_source_id_sources",
        "transactions",
        "sources",
        ["source_id"],
        ["id"],
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint("fk_transactions_source_id_sources", "transactions", type_="foreignkey")

    # Drop source_id column
    op.drop_column("transactions", "source_id")

    # Drop sources table
    op.drop_table("sources")
