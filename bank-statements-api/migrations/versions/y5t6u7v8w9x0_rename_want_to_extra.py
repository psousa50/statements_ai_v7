"""Rename category_kind enum value 'want' to 'extra'

Revision ID: y5t6u7v8w9x0
Revises: x4s5t6u7v8w9
Create Date: 2026-05-23 13:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "y5t6u7v8w9x0"
down_revision: Union[str, None] = "x4s5t6u7v8w9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE category_kind RENAME VALUE 'want' TO 'extra'")


def downgrade() -> None:
    op.execute("ALTER TYPE category_kind RENAME VALUE 'extra' TO 'want'")
