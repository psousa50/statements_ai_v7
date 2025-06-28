"""add_ai_counterparty_identification_job_type

Revision ID: 7da2fd4b37ee
Revises: d1aac96406c0
Create Date: 2025-06-21 19:26:41.857722

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7da2fd4b37ee"
down_revision: Union[str, None] = "d1aac96406c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new enum value to the jobtype enum
    op.execute("ALTER TYPE jobtype ADD VALUE 'AI_COUNTERPARTY_IDENTIFICATION'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum, which is complex
    # For now, we'll leave this as a no-op
    pass
