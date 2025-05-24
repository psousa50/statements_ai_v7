"""Update file_analysis_metadata table

Revision ID: update_file_analysis_metadata
Revises: remove_normalized_sample
Create Date: 2025-05-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "update_file_analysis_metadata"
down_revision = "3a9f8c7d2e1b"
branch_labels = None
depends_on = None


def upgrade():
    # Remove file_type column from file_analysis_metadata table
    op.drop_column("file_analysis_metadata", "file_type")
    
    # Add source_id column to file_analysis_metadata table
    op.add_column("file_analysis_metadata", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    # Remove source_id column from file_analysis_metadata table
    op.drop_column("file_analysis_metadata", "source_id")
    
    # Add back file_type column to file_analysis_metadata table
    op.add_column("file_analysis_metadata", sa.Column("file_type", sa.String(), nullable=False, server_default="csv"))
    op.alter_column("file_analysis_metadata", "file_type", server_default=None)
