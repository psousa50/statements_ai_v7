---
name: database
description: Explains this project's database schema, models, and data patterns
---

# Database Guide

## Technology

- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.x (declarative base)
- **Migrations**: Alembic
- **Connection**: Synchronous sessions via `SessionLocal` factory

Database URL configured via `DATABASE_URL` environment variable.

## Schema Overview

### Core Domain Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts (OAuth + password auth) |
| `accounts` | Bank/financial accounts per user |
| `transactions` | Financial transactions with categorization |
| `categories` | Hierarchical category tree (self-referential) |
| `statements` | Uploaded statement files linked to accounts |

### Supporting Tables

| Table | Purpose |
|-------|---------|
| `enhancement_rules` | Pattern-matching rules for auto-categorization |
| `initial_balances` | Starting balance per account for running totals |
| `description_groups` | Group similar transaction descriptions |
| `description_group_members` | Members of description groups |
| `filter_presets` | Saved filter configurations |
| `saved_filters` | Temporary filter state (auto-expires) |

### Infrastructure Tables

| Table | Purpose |
|-------|---------|
| `uploaded_files` | Temporary file storage during upload |
| `file_analysis_metadata` | Cached column mappings per file hash |
| `background_jobs` | Async job tracking (currently placeholder) |
| `refresh_tokens` | JWT refresh token storage |

## Model Locations

All SQLAlchemy models: `/bank-statements-api/app/domain/models/`

Key files:
- `user.py` - User model with OAuth/password auth
- `account.py` - Financial accounts
- `transaction.py` - Core transaction model
- `category.py` - Self-referential category hierarchy
- `enhancement_rule.py` - Pattern matching rules
- `statement.py` - Statement file records

## Relationships

```
User (1) ----< (N) Account
User (1) ----< (N) Category
User (1) ----< (N) RefreshToken

Account (1) ----< (N) Transaction
Account (1) ----< (N) Statement
Account (1) ----< (N) InitialBalance

Statement (1) ----< (N) Transaction

Category (1) ----< (N) Transaction
Category (1) ----< (N) Category (self-ref: parent/subcategories)

Transaction (N) >---- (1) Account (counterparty_account_id - transfers)

EnhancementRule >---- Category (optional)
EnhancementRule >---- Account (counterparty, optional)
EnhancementRule >---- Category (ai_suggested, optional)
EnhancementRule >---- Account (ai_suggested_counterparty, optional)
```

## Multi-tenancy

All user-owned data filtered by `user_id`:
- Accounts, Categories, Transactions have `user_id` FK with CASCADE delete
- Repositories filter by `user_id` on all queries
- Pattern: `query.filter(Model.user_id == user_id)`

## Migrations

Location: `/bank-statements-api/migrations/versions/`

Commands (run from project root):
```bash
pnpm db:migrate        # Apply migrations to dev db
pnpm test:db:migrate   # Apply migrations to test db
```

Creating new migrations:
```bash
cd bank-statements-api
alembic revision -m "description_of_change"
```

Migration naming: `<hash>_<description>.py`

## Query Patterns

### Repository Pattern (Hexagonal Architecture)

- **Ports** (interfaces): `/app/ports/repositories/` - Abstract base classes
- **Adapters** (implementations): `/app/adapters/repositories/` - SQLAlchemy implementations

Example injection in routes:
```python
def get_transaction_repo(db: Session = Depends(get_db)):
    return SQLAlchemyTransactionRepository(db)
```

### Common Query Patterns

**Paginated queries with filters**:
```python
def get_paginated(self, user_id, page, page_size, **filters):
    query = self.db_session.query(Model).filter(Model.user_id == user_id)
    # Apply dynamic filters
    if filters.get('category_id'):
        query = query.filter(Model.category_id == filters['category_id'])
    # Get count + sum in single query
    total, total_amount = self.db_session.query(
        func.count(Model.id),
        func.sum(Model.amount)
    ).filter(...).one()
    # Paginate
    return query.offset((page-1) * page_size).limit(page_size).all()
```

**Batch operations with union_all**:
```python
# Count matching transactions for multiple rules in one query
subqueries = [
    session.query(literal(str(rule.id)), func.count(Transaction.id))
    .filter(...)
    for rule in rules
]
combined = union_all(*subqueries)
```

**Window functions for running balances**:
```python
running_sum = over(
    func.sum(Transaction.amount),
    partition_by=Transaction.account_id,
    order_by=[Transaction.date, Transaction.sort_index],
    rows=(None, 0)  # All rows up to current
)
```

## Adding New Models

1. Create model in `/app/domain/models/your_model.py`:
```python
from app.core.database import Base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

class YourModel(Base):
    __tablename__ = "your_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # ... fields
```

2. Export in `/app/domain/models/__init__.py`

3. Create port (interface) in `/app/ports/repositories/your_model.py`

4. Create adapter in `/app/adapters/repositories/your_model.py`

5. Generate migration:
```bash
cd bank-statements-api
alembic revision -m "add_your_models_table"
```

6. Implement upgrade/downgrade in migration file

## Key Conventions

- UUIDs for all primary keys (PostgreSQL UUID type)
- `created_at`, `updated_at` timestamps with timezone
- Decimal/Numeric(10,2) for monetary amounts
- JSONB for flexible schema fields (filter_data, progress, etc.)
- Enum types defined in Python, mapped via SQLAlchemy Enum
- Indexes on: `user_id`, `date`, `normalized_description`, foreign keys
- Unique constraints via `__table_args__`
