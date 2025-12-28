"""Add user_id to transactions table

Revision ID: j0e1f2g3h4i5
Revises: i9d0e1f2g3h4
Create Date: 2024-12-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "j0e1f2g3h4i5"
down_revision: Union[str, None] = "i9d0e1f2g3h4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    op.add_column("transactions", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))

    conn.execute(
        sa.text(
            """
            UPDATE transactions t
            SET user_id = a.user_id
            FROM accounts a
            WHERE t.account_id = a.id
            """
        )
    )

    op.alter_column("transactions", "user_id", nullable=False)
    op.create_foreign_key("fk_transactions_user_id", "transactions", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_constraint("fk_transactions_user_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "user_id")
