"""Add AI suggestion fields to enhancement_rules

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2025-12-26 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "enhancement_rules",
        sa.Column("ai_suggested_category_id", sa.UUID(), sa.ForeignKey("categories.id"), nullable=True),
    )
    op.add_column(
        "enhancement_rules",
        sa.Column("ai_category_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
    )
    op.add_column(
        "enhancement_rules",
        sa.Column("ai_suggested_counterparty_id", sa.UUID(), sa.ForeignKey("accounts.id"), nullable=True),
    )
    op.add_column(
        "enhancement_rules",
        sa.Column("ai_counterparty_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
    )
    op.add_column(
        "enhancement_rules",
        sa.Column("ai_processed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("enhancement_rules", "ai_processed_at")
    op.drop_column("enhancement_rules", "ai_counterparty_confidence")
    op.drop_column("enhancement_rules", "ai_suggested_counterparty_id")
    op.drop_column("enhancement_rules", "ai_category_confidence")
    op.drop_column("enhancement_rules", "ai_suggested_category_id")
