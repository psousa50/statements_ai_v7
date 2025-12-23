# Development Commands

API: port ${API_PORT:-8010} | UI: port 5173

## Backend (bank-statements-api/)
```bash
uv run python run.py          # Dev server
uv run pytest                 # Tests
uv run alembic upgrade head   # Migrations
uv run isort . && uv run black . && uv run ruff check .  # Lint/format
```

## Frontend (bank-statements-web/)
```bash
pnpm run dev                 # Dev server
pnpm run build               # Build
pnpm run test                # Tests
pnpm run lint                # Lint
```

## Test Database
```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:15432/bank_statements_test uv run alembic upgrade head
```

## Notes
- Hot reload enabled on both services
- Update tests when changing behaviour
