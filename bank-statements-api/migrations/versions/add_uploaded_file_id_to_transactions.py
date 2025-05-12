"""Add uploaded_file_id to transactions table

Revision ID: add_file_id_to_transactions
Revises: split_uploaded_file_tables
Create Date: 2025-05-12 15:05:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_file_id_to_transactions"
down_revision = "split_uploaded_file_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Add uploaded_file_id column to transactions table
    op.add_column(
        "transactions",
        sa.Column("uploaded_file_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        "fk_transactions_uploaded_file_id_uploaded_files",
        "transactions",
        "uploaded_files",
        ["uploaded_file_id"],
        ["id"],
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint(
        "fk_transactions_uploaded_file_id_uploaded_files",
        "transactions",
        type_="foreignkey"
    )
    
    # Drop uploaded_file_id column
    op.drop_column("transactions", "uploaded_file_id")
