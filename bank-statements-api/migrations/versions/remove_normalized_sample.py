"""Remove normalized_sample column from file_analysis_metadata table

Revision ID: 3a9f8c7d2e1b
Revises: add_sources_table
Create Date: 2025-05-14 15:58:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3a9f8c7d2e1b"
down_revision = "add_sources_table"
branch_labels = None
depends_on = None


def upgrade():
    # First make the normalized_sample column nullable using SQL directly
    op.execute("ALTER TABLE file_analysis_metadata ALTER COLUMN normalized_sample DROP NOT NULL;")

    # Then remove the normalized_sample column from file_analysis_metadata table
    op.drop_column("file_analysis_metadata", "normalized_sample")


def downgrade():
    # Add back the normalized_sample column to file_analysis_metadata table
    op.add_column("file_analysis_metadata", sa.Column("normalized_sample", postgresql.JSONB(astext_type=sa.Text()), nullable=False))
