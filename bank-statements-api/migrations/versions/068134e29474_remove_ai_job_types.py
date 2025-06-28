"""remove_ai_job_types

Revision ID: 068134e29474
Revises: 9d0e79cc879a
Create Date: 2025-06-26 20:04:42.205802

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "068134e29474"
down_revision: Union[str, None] = "9d0e79cc879a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Delete any existing background jobs with these types before removing enum values
    op.execute("DELETE FROM background_jobs WHERE job_type IN ('AI_CATEGORIZATION', 'AI_COUNTERPARTY_IDENTIFICATION')")

    # Since we're removing all job types, we'll drop the background_jobs table entirely
    # but keep it for future use with a placeholder enum
    op.execute("DROP TABLE IF EXISTS background_jobs")
    op.execute("DROP TYPE IF EXISTS jobtype")
    op.execute("CREATE TYPE jobtype AS ENUM ('PLACEHOLDER')")

    # Recreate empty background_jobs table structure for future use
    op.execute(
        """
        CREATE TABLE background_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_type jobtype NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            uploaded_file_id UUID REFERENCES uploaded_files(id),
            progress JSONB NOT NULL DEFAULT '{}',
            result JSONB NOT NULL DEFAULT '{}',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            retry_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3
        )
    """
    )


def downgrade() -> None:
    # Recreate the enum with the AI job types
    op.execute("ALTER TYPE jobtype RENAME TO jobtype_old")
    op.execute("CREATE TYPE jobtype AS ENUM ('AI_CATEGORIZATION', 'AI_COUNTERPARTY_IDENTIFICATION')")
    op.execute("ALTER TABLE background_jobs ALTER COLUMN job_type TYPE jobtype USING job_type::text::jobtype")
    op.execute("DROP TYPE jobtype_old")
