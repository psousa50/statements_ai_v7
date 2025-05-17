"""Add file_type column to uploaded_files table

Revision ID: add_file_type_to_uploaded_files
Revises: add_sources_table
Create Date: 2025-05-17 10:46:05.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_file_type_to_uploaded_files"
down_revision = "3a9f8c7d2e1b"
branch_labels = None
depends_on = None


def upgrade():
    # Add file_type column to uploaded_files table
    op.add_column("uploaded_files", sa.Column("file_type", sa.String(), nullable=True))


def downgrade():
    # Drop file_type column from uploaded_files table
    op.drop_column("uploaded_files", "file_type")
