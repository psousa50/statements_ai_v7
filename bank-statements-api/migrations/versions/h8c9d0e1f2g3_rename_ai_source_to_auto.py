"""Rename AI source to AUTO in enhancement_rules - step 1: add enum value

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2024-12-26

"""

from alembic import op

revision = "h8c9d0e1f2g3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE enhancementrulesource ADD VALUE IF NOT EXISTS 'AUTO'")


def downgrade() -> None:
    pass
