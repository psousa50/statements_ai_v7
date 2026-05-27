"""Add enhancement_rule_split_lines table

Revision ID: a7v8w9x0y1z2
Revises: z6u7v8w9x0y1
Create Date: 2026-05-27 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7v8w9x0y1z2"
down_revision: Union[str, None] = "z6u7v8w9x0y1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "enhancement_rule_split_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enhancement_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("is_remainder", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_enhancement_rule_split_lines_rule_id",
        "enhancement_rule_split_lines",
        ["rule_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_enhancement_rule_split_lines_rule_id", table_name="enhancement_rule_split_lines")
    op.drop_table("enhancement_rule_split_lines")
