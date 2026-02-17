"""Add tags and transaction_tags tables

Revision ID: p6k7l8m9n0o1
Revises: o5j6k7l8m9n0
Create Date: 2026-02-17 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "p6k7l8m9n0o1"
down_revision: Union[str, None] = "o5j6k7l8m9n0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])
    op.execute("CREATE UNIQUE INDEX uq_tags_user_id_lower_name ON tags (user_id, LOWER(name))")

    op.create_table(
        "transaction_tags",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("transaction_id", "tag_id"),
    )
    op.create_index(
        "ix_transaction_tags_transaction_id",
        "transaction_tags",
        ["transaction_id"],
    )
    op.create_index(
        "ix_transaction_tags_tag_id",
        "transaction_tags",
        ["tag_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_transaction_tags_tag_id", table_name="transaction_tags")
    op.drop_index("ix_transaction_tags_transaction_id", table_name="transaction_tags")
    op.drop_table("transaction_tags")

    op.execute("DROP INDEX IF EXISTS uq_tags_user_id_lower_name")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_table("tags")
