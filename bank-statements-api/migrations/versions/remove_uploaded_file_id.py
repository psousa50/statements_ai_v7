"""Remove uploaded_file_id column from file_analysis_metadata

Revision ID: remove_uploaded_file_id
Revises: initial_migration
Create Date: 2025-05-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'remove_uploaded_file_id'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the foreign key constraint first
    op.drop_constraint('file_analysis_metadata_uploaded_file_id_fkey', 'file_analysis_metadata', type_='foreignkey')
    
    # Then drop the column
    op.drop_column('file_analysis_metadata', 'uploaded_file_id')


def downgrade():
    # Add the column back
    op.add_column('file_analysis_metadata', sa.Column('uploaded_file_id', postgresql.UUID(), nullable=True))
    
    # Add the foreign key constraint back
    op.create_foreign_key('file_analysis_metadata_uploaded_file_id_fkey', 'file_analysis_metadata', 'uploaded_files', ['uploaded_file_id'], ['id'])
    
    # Note: This is a lossy migration - when downgrading, the uploaded_file_id values will be NULL
