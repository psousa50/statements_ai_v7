"""add_background_jobs_table

Revision ID: 4032ce98a1c9
Revises: bc4f2d9e1a8c
Create Date: 2025-06-01 12:14:02.740676

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4032ce98a1c9"
down_revision: Union[str, None] = "bc4f2d9e1a8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create job_status enum type
    job_status = postgresql.ENUM(
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="jobstatus",
        create_type=False,
    )
    job_status.create(op.get_bind())

    # Create job_type enum type
    job_type = postgresql.ENUM("AI_CATEGORIZATION", name="jobtype", create_type=False)
    job_type.create(op.get_bind())

    # Create background_jobs table
    op.create_table(
        "background_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="PENDING"),
        sa.Column("uploaded_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("progress", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("result", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.ForeignKeyConstraint(
            ["uploaded_file_id"],
            ["uploaded_files.id"],
        ),
    )

    # Create indexes for better query performance
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])
    op.create_index("ix_background_jobs_job_type", "background_jobs", ["job_type"])
    op.create_index(
        "ix_background_jobs_uploaded_file_id", "background_jobs", ["uploaded_file_id"]
    )
    op.create_index("ix_background_jobs_created_at", "background_jobs", ["created_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_background_jobs_created_at", "background_jobs")
    op.drop_index("ix_background_jobs_uploaded_file_id", "background_jobs")
    op.drop_index("ix_background_jobs_job_type", "background_jobs")
    op.drop_index("ix_background_jobs_status", "background_jobs")

    # Drop background_jobs table
    op.drop_table("background_jobs")

    # Drop enum types
    job_type = postgresql.ENUM("AI_CATEGORIZATION", name="jobtype")
    job_type.drop(op.get_bind())

    job_status = postgresql.ENUM(
        "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED", name="jobstatus"
    )
    job_status.drop(op.get_bind())
