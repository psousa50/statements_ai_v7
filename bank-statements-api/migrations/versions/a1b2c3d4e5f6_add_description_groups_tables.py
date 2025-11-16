"""Add description_groups tables

Revision ID: a1b2c3d4e5f6
Revises: dc07aa0a9f15
Create Date: 2025-11-15 11:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "dc07aa0a9f15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "description_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "description_group_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["description_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_description_group_members_group_id",
        "description_group_members",
        ["group_id"],
    )
    op.create_index(
        "ix_description_group_members_normalized_description",
        "description_group_members",
        ["normalized_description"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_description_group_members_normalized_description",
        table_name="description_group_members",
    )
    op.drop_index(
        "ix_description_group_members_group_id",
        table_name="description_group_members",
    )
    op.drop_table("description_group_members")
    op.drop_table("description_groups")
