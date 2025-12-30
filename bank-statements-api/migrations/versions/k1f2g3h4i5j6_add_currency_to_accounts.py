"""Add currency to accounts table

Revision ID: k1f2g3h4i5j6
Revises: j0e1f2g3h4i5
Create Date: 2024-12-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k1f2g3h4i5j6"
down_revision: Union[str, None] = "j0e1f2g3h4i5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("currency", sa.String(3), nullable=True))
    op.execute("UPDATE accounts SET currency = 'EUR' WHERE currency IS NULL")
    op.alter_column("accounts", "currency", nullable=False, server_default="EUR")


def downgrade() -> None:
    op.drop_column("accounts", "currency")
