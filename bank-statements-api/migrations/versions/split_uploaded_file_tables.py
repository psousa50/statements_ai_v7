"""Split uploaded file and file analysis metadata tables

Revision ID: split_uploaded_file_tables
Revises: add_categories_table
Create Date: 2025-05-04 22:55:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "split_uploaded_file_tables"
down_revision = "add_categories_table"
branch_labels = None
depends_on = None


def upgrade():
    # Create uploaded_files table
    op.create_table(
        "uploaded_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # Create file_analysis_metadata table
    op.create_table(
        "file_analysis_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("uploaded_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_hash", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("column_mapping", postgresql.JSONB(), nullable=False),
        sa.Column("header_row_index", sa.Integer(), nullable=False),
        sa.Column("data_start_row_index", sa.Integer(), nullable=False),
        sa.Column("normalized_sample", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["uploaded_file_id"],
            ["uploaded_files.id"],
        ),
        sa.UniqueConstraint("file_hash"),
    )

    # Create index on file_hash for faster lookups
    op.create_index("ix_file_analysis_metadata_file_hash", "file_analysis_metadata", ["file_hash"])


def downgrade():
    op.drop_index("ix_file_analysis_metadata_file_hash", "file_analysis_metadata")
    op.drop_table("file_analysis_metadata")
    op.drop_table("uploaded_files")
