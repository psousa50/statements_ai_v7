"""
Revision ID: initial_migration
Revises: 
Create Date: 2025-05-24 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "initial_migration"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create categorization_status enum type
    categorization_status = postgresql.ENUM(
        "UNCATEGORIZED",
        "CATEGORIZED",
        "FAILURE",
        name="categorizationstatus",
        create_type=False,
    )
    categorization_status.create(op.get_bind())

    # Create sources table
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("name"),
    )

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

    # Create uploaded_files table
    op.create_table(
        "uploaded_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # Create file_analysis_metadata table
    op.create_table(
        "file_analysis_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("uploaded_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_hash", sa.Text(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),  # Changed to not nullable
        sa.Column("column_mapping", postgresql.JSONB(), nullable=False),
        sa.Column("header_row_index", sa.Integer(), nullable=False),
        sa.Column("data_start_row_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["uploaded_file_id"],
            ["uploaded_files.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.UniqueConstraint("file_hash"),
    )

    # Create index on file_hash for faster lookups
    op.create_index("ix_file_analysis_metadata_file_hash", "file_analysis_metadata", ["file_hash"])

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "categorization_status",
            categorization_status,
            nullable=False,
            server_default="UNCATEGORIZED",
        ),
        sa.Column("uploaded_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),  # Changed to not nullable
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_file_id"],
            ["uploaded_files.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_date"), "transactions", ["date"], unique=False)


def downgrade() -> None:
    # Drop all tables and enums in reverse order
    op.drop_index(op.f("ix_transactions_date"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_file_analysis_metadata_file_hash", "file_analysis_metadata")
    op.drop_table("file_analysis_metadata")
    op.drop_table("uploaded_files")
    op.drop_table("categories")
    op.drop_table("sources")

    # Drop categorization_status enum type
    categorization_status = postgresql.ENUM("UNCATEGORIZED", "CATEGORIZED", "FAILURE", name="categorizationstatus")
    categorization_status.drop(op.get_bind())
