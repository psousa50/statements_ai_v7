"""Rename AI source to AUTO in enhancement_rules - step 2: update values

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2024-12-26

"""

from alembic import op

revision = "i9d0e1f2g3h4"
down_revision = "h8c9d0e1f2g3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE enhancement_rules SET source = 'AUTO' WHERE source = 'AI'")


def downgrade() -> None:
    op.execute("UPDATE enhancement_rules SET source = 'AI' WHERE source = 'AUTO'")
