"""Add user_id to accounts, categories, enhancement_rules, description_groups

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-22 10:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    conn = op.get_bind()

    existing_user = conn.execute(sa.text("SELECT id FROM users WHERE id = :id"), {"id": DEFAULT_USER_ID}).fetchone()

    if not existing_user:
        conn.execute(
            sa.text(
                """
                INSERT INTO users (id, email, name, oauth_provider, oauth_id, created_at, updated_at)
                VALUES (:id, :email, :name, :oauth_provider, :oauth_id, NOW(), NOW())
            """
            ),
            {
                "id": DEFAULT_USER_ID,
                "email": "default@system.local",
                "name": "Default User",
                "oauth_provider": "system",
                "oauth_id": "default",
            },
        )

    op.add_column("accounts", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    conn.execute(sa.text(f"UPDATE accounts SET user_id = '{DEFAULT_USER_ID}' WHERE user_id IS NULL"))
    op.alter_column("accounts", "user_id", nullable=False)
    op.create_foreign_key("fk_accounts_user_id", "accounts", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])
    op.drop_constraint("accounts_name_key", "accounts", type_="unique")
    op.create_unique_constraint("uq_accounts_user_name", "accounts", ["user_id", "name"])

    op.add_column("categories", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    conn.execute(sa.text(f"UPDATE categories SET user_id = '{DEFAULT_USER_ID}' WHERE user_id IS NULL"))
    op.alter_column("categories", "user_id", nullable=False)
    op.create_foreign_key("fk_categories_user_id", "categories", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.add_column("enhancement_rules", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    conn.execute(sa.text(f"UPDATE enhancement_rules SET user_id = '{DEFAULT_USER_ID}' WHERE user_id IS NULL"))
    op.alter_column("enhancement_rules", "user_id", nullable=False)
    op.create_foreign_key("fk_enhancement_rules_user_id", "enhancement_rules", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_enhancement_rules_user_id", "enhancement_rules", ["user_id"])

    op.add_column("description_groups", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    conn.execute(sa.text(f"UPDATE description_groups SET user_id = '{DEFAULT_USER_ID}' WHERE user_id IS NULL"))
    op.alter_column("description_groups", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_description_groups_user_id", "description_groups", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_description_groups_user_id", "description_groups", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_description_groups_user_id", table_name="description_groups")
    op.drop_constraint("fk_description_groups_user_id", "description_groups", type_="foreignkey")
    op.drop_column("description_groups", "user_id")

    op.drop_index("ix_enhancement_rules_user_id", table_name="enhancement_rules")
    op.drop_constraint("fk_enhancement_rules_user_id", "enhancement_rules", type_="foreignkey")
    op.drop_column("enhancement_rules", "user_id")

    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_constraint("fk_categories_user_id", "categories", type_="foreignkey")
    op.drop_column("categories", "user_id")

    op.drop_constraint("uq_accounts_user_name", "accounts", type_="unique")
    op.create_unique_constraint("accounts_name_key", "accounts", ["name"])
    op.drop_index("ix_accounts_user_id", table_name="accounts")
    op.drop_constraint("fk_accounts_user_id", "accounts", type_="foreignkey")
    op.drop_column("accounts", "user_id")
