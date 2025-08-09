"""add transaction count and date range to statements

Revision ID: 628b19f5990c
Revises: 4784ecf59876
Create Date: 2025-07-09 19:51:54.682078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "628b19f5990c"
down_revision: Union[str, None] = "4784ecf59876"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("statements", sa.Column("transaction_count", sa.Integer(), nullable=True))
    op.add_column("statements", sa.Column("date_from", sa.Date(), nullable=True))
    op.add_column("statements", sa.Column("date_to", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("statements", "date_to")
    op.drop_column("statements", "date_from")
    op.drop_column("statements", "transaction_count")
