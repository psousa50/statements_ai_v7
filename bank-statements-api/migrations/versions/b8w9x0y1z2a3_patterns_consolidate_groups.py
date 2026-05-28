"""Migrate enhancement rules to multi-pattern model, consolidate description groups

Revision ID: b8w9x0y1z2a3
Revises: a7v8w9x0y1z2
Create Date: 2026-05-28 10:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8w9x0y1z2a3"
down_revision: Union[str, None] = "a7v8w9x0y1z2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "enhancement_rule_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enhancement_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("normalized_description", sa.String(), nullable=False),
        sa.Column(
            "match_type",
            postgresql.ENUM("exact", "prefix", "infix", name="matchtype", create_type=False),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_enhancement_rule_patterns_rule_id", "enhancement_rule_patterns", ["rule_id"])
    op.create_index(
        "ix_enhancement_rule_patterns_normalized_description",
        "enhancement_rule_patterns",
        ["normalized_description"],
    )
    op.create_unique_constraint(
        "uq_enhancement_rule_patterns_rule_description",
        "enhancement_rule_patterns",
        ["rule_id", "normalized_description"],
    )

    op.execute(
        """
        INSERT INTO enhancement_rule_patterns (id, rule_id, normalized_description, match_type, sort_order)
        SELECT gen_random_uuid(), id, normalized_description_pattern, match_type, 0
        FROM enhancement_rules
        """
    )

    bind = op.get_bind()
    _consolidate_description_groups(bind)

    op.drop_table("description_group_members")
    op.drop_table("description_groups")

    op.drop_column("enhancement_rules", "normalized_description_pattern")
    op.drop_column("enhancement_rules", "match_type")


def _consolidate_description_groups(bind) -> None:
    groups = bind.execute(sa.text("SELECT id, user_id FROM description_groups")).fetchall()

    for group_id, user_id in groups:
        members = bind.execute(
            sa.text("SELECT normalized_description FROM description_group_members WHERE group_id = :group_id"),
            {"group_id": group_id},
        ).fetchall()
        descriptions = [row[0] for row in members]
        if not descriptions:
            continue

        rules = bind.execute(
            sa.text(
                """
                SELECT DISTINCT er.id, er.category_id, er.counterparty_account_id, er.source, er.created_at
                FROM enhancement_rules er
                JOIN enhancement_rule_patterns erp ON erp.rule_id = er.id
                WHERE er.user_id = :user_id AND erp.normalized_description = ANY(:descriptions)
                """
            ),
            {"user_id": user_id, "descriptions": descriptions},
        ).fetchall()

        if not rules:
            # No rule covers any of these descriptions; create a single MANUAL rule owning all of them.
            new_rule_id = uuid4()
            bind.execute(
                sa.text(
                    """
                    INSERT INTO enhancement_rules (id, user_id, source, created_at, updated_at)
                    VALUES (:id, :user_id, 'MANUAL', now(), now())
                    """
                ),
                {"id": new_rule_id, "user_id": user_id},
            )
            for idx, description in enumerate(descriptions):
                bind.execute(
                    sa.text(
                        """
                        INSERT INTO enhancement_rule_patterns (id, rule_id, normalized_description, match_type, sort_order)
                        VALUES (:id, :rule_id, :description, 'exact', :sort_order)
                        """
                    ),
                    {"id": uuid4(), "rule_id": new_rule_id, "description": description, "sort_order": idx},
                )
            continue

        winner = _pick_winner(rules)
        loser_ids = [row[0] for row in rules if row[0] != winner]

        if loser_ids:
            # Drop loser patterns whose description already exists on the winner — keep one row per description.
            bind.execute(
                sa.text(
                    """
                    DELETE FROM enhancement_rule_patterns
                    WHERE rule_id = ANY(:losers)
                      AND normalized_description IN (
                          SELECT normalized_description FROM enhancement_rule_patterns WHERE rule_id = :winner
                      )
                    """
                ),
                {"winner": winner, "losers": loser_ids},
            )
            bind.execute(
                sa.text("UPDATE enhancement_rule_patterns SET rule_id = :winner WHERE rule_id = ANY(:losers)"),
                {"winner": winner, "losers": loser_ids},
            )
            bind.execute(
                sa.text("DELETE FROM enhancement_rules WHERE id = ANY(:losers)"),
                {"losers": loser_ids},
            )

        # Ensure every group member description is present as a pattern of the winner.
        existing = bind.execute(
            sa.text("SELECT normalized_description FROM enhancement_rule_patterns WHERE rule_id = :rule_id"),
            {"rule_id": winner},
        ).fetchall()
        existing_set = {row[0] for row in existing}
        next_sort = len(existing_set)
        for description in descriptions:
            if description in existing_set:
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO enhancement_rule_patterns (id, rule_id, normalized_description, match_type, sort_order)
                    VALUES (:id, :rule_id, :description, 'exact', :sort_order)
                    """
                ),
                {"id": uuid4(), "rule_id": winner, "description": description, "sort_order": next_sort},
            )
            next_sort += 1


def _pick_winner(rules) -> object:
    def score(row):
        _id, category_id, counterparty_account_id, source, created_at = row
        configured = category_id is not None or counterparty_account_id is not None
        manual = source == "MANUAL"
        return (configured, manual, created_at is None, -(created_at.timestamp() if created_at else 0))

    sorted_rules = sorted(rules, key=score, reverse=True)
    return sorted_rules[0][0]


def downgrade() -> None:
    op.add_column(
        "enhancement_rules",
        sa.Column("normalized_description_pattern", sa.String(), nullable=True),
    )
    op.add_column(
        "enhancement_rules",
        sa.Column(
            "match_type",
            postgresql.ENUM("exact", "prefix", "infix", name="matchtype", create_type=False),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE enhancement_rules er
        SET normalized_description_pattern = erp.normalized_description,
            match_type = erp.match_type
        FROM (
            SELECT DISTINCT ON (rule_id) rule_id, normalized_description, match_type
            FROM enhancement_rule_patterns
            ORDER BY rule_id, sort_order ASC
        ) erp
        WHERE er.id = erp.rule_id
        """
    )

    op.alter_column("enhancement_rules", "normalized_description_pattern", nullable=False)
    op.alter_column("enhancement_rules", "match_type", nullable=False)

    op.create_table(
        "description_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_description_groups_user_id", "description_groups", ["user_id"])

    op.create_table(
        "description_group_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("description_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("normalized_description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_description_group_members_group_id", "description_group_members", ["group_id"])
    op.create_index(
        "ix_description_group_members_normalized_description",
        "description_group_members",
        ["normalized_description"],
    )

    op.drop_index("ix_enhancement_rule_patterns_normalized_description", table_name="enhancement_rule_patterns")
    op.drop_index("ix_enhancement_rule_patterns_rule_id", table_name="enhancement_rule_patterns")
    op.drop_table("enhancement_rule_patterns")
