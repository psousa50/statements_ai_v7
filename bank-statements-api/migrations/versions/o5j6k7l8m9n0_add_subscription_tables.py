"""Add subscription tables and tier_override to users

Revision ID: o5j6k7l8m9n0
Revises: n4i5j6k7l8m9
Create Date: 2026-01-30 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "o5j6k7l8m9n0"
down_revision: Union[str, None] = "n4i5j6k7l8m9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    subscriptiontier = postgresql.ENUM("free", "basic", "pro", name="subscriptiontier", create_type=False)
    subscriptiontier.create(op.get_bind(), checkfirst=True)

    subscriptionstatus = postgresql.ENUM(
        "active", "cancelled", "past_due", "expired", name="subscriptionstatus", create_type=False
    )
    subscriptionstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tier", subscriptiontier, nullable=False, server_default="free"),
        sa.Column("status", subscriptionstatus, nullable=False, server_default="active"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])

    op.create_table(
        "subscription_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("statements_this_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("statements_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_calls_this_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_calls_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subscription_id"),
    )
    op.create_index("ix_subscription_usage_subscription_id", "subscription_usage", ["subscription_id"])

    op.add_column("users", sa.Column("tier_override", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "tier_override")

    op.drop_index("ix_subscription_usage_subscription_id", table_name="subscription_usage")
    op.drop_table("subscription_usage")

    op.drop_index("ix_subscriptions_stripe_customer_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    op.execute("DROP TYPE IF EXISTS subscriptiontier")
