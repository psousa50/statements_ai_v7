"""Initial schema migration

Revision ID: d1aac96406c0
Revises:
Create Date: 2025-06-21 18:40:18.676240

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1aac96406c0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enum types (SQLAlchemy will auto-create them)
    categorization_status_enum = postgresql.ENUM(
        "UNCATEGORIZED",
        "CATEGORIZED",
        "FAILURE",
        name="categorizationstatus",
    )
    counterparty_status_enum = postgresql.ENUM(
        "unprocessed",
        "inferred",
        "confirmed",
        name="counterpartystatus",
    )
    source_type_enum = postgresql.ENUM("upload", "manual", name="sourcetype")
    job_type_enum = postgresql.ENUM("AI_CATEGORIZATION", name="jobtype")
    job_status_enum = postgresql.ENUM(
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="jobstatus",
    )
    categorization_source_enum = postgresql.ENUM("MANUAL", "AI", name="categorizationsource")

    # Create accounts table
    op.create_table(
        "accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create categories table
    op.create_table(
        "categories",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create uploaded_files table
    op.create_table(
        "uploaded_files",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create statements table
    op.create_table(
        "statements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create background_jobs table
    op.create_table(
        "background_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("job_type", job_type_enum, nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column(
            "uploaded_file_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "progress",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["uploaded_file_id"],
            ["uploaded_files.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create initial_balances table
    op.create_table(
        "initial_balances",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("balance_date", sa.Date(), nullable=False),
        sa.Column(
            "balance_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id",
            "balance_date",
            name="uq_initial_balance_account_date",
        ),
    )

    # Create file_analysis_metadata table
    op.create_table(
        "file_analysis_metadata",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("file_hash", sa.Text(), nullable=False),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "column_mapping",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("header_row_index", sa.Integer(), nullable=False),
        sa.Column(
            "data_start_row_index",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_hash"),
    )

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column(
            "normalized_description",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "statement_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "counterparty_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "categorization_status",
            categorization_status_enum,
            nullable=False,
        ),
        sa.Column(
            "categorization_confidence",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
        sa.Column(
            "counterparty_status",
            counterparty_status_enum,
            nullable=False,
        ),
        sa.Column("row_index", sa.Integer(), nullable=True),
        sa.Column("sort_index", sa.Integer(), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column(
            "manual_position_after",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["counterparty_account_id"],
            ["accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["manual_position_after"],
            ["transactions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["statements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create transaction_categorization table
    op.create_table(
        "transaction_categorization",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "normalized_description",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "source",
            categorization_source_enum,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_description"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_transactions_date"),
        "transactions",
        ["date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_normalized_description"),
        "transactions",
        ["normalized_description"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transaction_categorization_normalized_description"),
        "transaction_categorization",
        ["normalized_description"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_analysis_metadata_file_hash"),
        "file_analysis_metadata",
        ["file_hash"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_file_analysis_metadata_file_hash"),
        table_name="file_analysis_metadata",
    )
    op.drop_index(
        op.f("ix_transaction_categorization_normalized_description"),
        table_name="transaction_categorization",
    )
    op.drop_index(
        op.f("ix_transactions_normalized_description"),
        table_name="transactions",
    )
    op.drop_index(
        op.f("ix_transactions_date"),
        table_name="transactions",
    )

    # Drop tables in reverse order
    op.drop_table("transaction_categorization")
    op.drop_table("transactions")
    op.drop_table("file_analysis_metadata")
    op.drop_table("initial_balances")
    op.drop_table("background_jobs")
    op.drop_table("statements")
    op.drop_table("uploaded_files")
    op.drop_table("categories")
    op.drop_table("accounts")

    # Drop enum types (SQLAlchemy will auto-drop them with tables)
