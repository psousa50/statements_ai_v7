"""Add categories table and update transactions table

Revision ID: add_categories_table
Revises: bb529ca62bbf
Create Date: 2025-05-03 14:23:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_categories_table"
down_revision = "bb529ca62bbf"
branch_labels = None
depends_on = None


def upgrade():
    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add categorization_status enum type
    categorization_status = postgresql.ENUM(
        "UNCATEGORIZED", "CATEGORIZED", "FAILURE", name="categorizationstatus"
    )
    categorization_status.create(op.get_bind())

    # Add category_id and categorization_status columns to transactions table
    op.add_column(
        "transactions",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "categorization_status",
            sa.Enum(
                "UNCATEGORIZED", "CATEGORIZED", "FAILURE", name="categorizationstatus"
            ),
            nullable=False,
            server_default="UNCATEGORIZED",
        ),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint(
        "fk_transactions_category_id", "transactions", type_="foreignkey"
    )

    # Drop columns from transactions table
    op.drop_column("transactions", "categorization_status")
    op.drop_column("transactions", "category_id")

    # Drop categorization_status enum type
    categorization_status = postgresql.ENUM(
        "UNCATEGORIZED", "CATEGORIZED", "FAILURE", name="categorizationstatus"
    )
    categorization_status.drop(op.get_bind())

    # Drop categories table
    op.drop_table("categories")
