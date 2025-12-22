"""Change file_hash unique constraint to composite (file_hash, account_id)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-12-22 16:50:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("file_analysis_metadata_file_hash_key", "file_analysis_metadata", type_="unique")
    op.create_unique_constraint(
        "file_analysis_metadata_file_hash_account_id_key",
        "file_analysis_metadata",
        ["file_hash", "account_id"],
    )


def downgrade() -> None:
    op.drop_constraint("file_analysis_metadata_file_hash_account_id_key", "file_analysis_metadata", type_="unique")
    op.create_unique_constraint("file_analysis_metadata_file_hash_key", "file_analysis_metadata", ["file_hash"])
