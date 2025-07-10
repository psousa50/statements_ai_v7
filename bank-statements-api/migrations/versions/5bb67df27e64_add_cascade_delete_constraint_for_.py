"""add cascade delete constraint for statement transactions

Revision ID: 5bb67df27e64
Revises: 628b19f5990c
Create Date: 2025-07-09 20:14:41.822303

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5bb67df27e64'
down_revision: Union[str, None] = '628b19f5990c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing foreign key constraint
    op.drop_constraint('transactions_statement_id_fkey', 'transactions', type_='foreignkey')
    
    # Add the new foreign key constraint with CASCADE DELETE
    op.create_foreign_key(
        'transactions_statement_id_fkey',  # constraint name
        'transactions',                     # source table
        'statements',                       # target table
        ['statement_id'],                   # source columns
        ['id'],                            # target columns
        ondelete='CASCADE'                 # CASCADE on delete
    )


def downgrade() -> None:
    # Drop the cascade constraint
    op.drop_constraint('transactions_statement_id_fkey', 'transactions', type_='foreignkey')
    
    # Restore the original constraint without cascade
    op.create_foreign_key(
        'transactions_statement_id_fkey',
        'transactions',
        'statements',
        ['statement_id'],
        ['id']
    )
