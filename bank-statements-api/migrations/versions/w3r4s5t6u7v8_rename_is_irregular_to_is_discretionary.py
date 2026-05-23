"""Rename is_irregular to is_discretionary

Revision ID: w3r4s5t6u7v8
Revises: v2q3r4s5t6u7
Create Date: 2026-05-22 17:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "w3r4s5t6u7v8"
down_revision: Union[str, None] = "v2q3r4s5t6u7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("categories", "is_irregular", new_column_name="is_discretionary")


def downgrade() -> None:
    op.alter_column("categories", "is_discretionary", new_column_name="is_irregular")
