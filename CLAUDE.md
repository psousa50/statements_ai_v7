# Development Commands

api is running at 8010, ui at 6173

## Backend (Poetry)
```bash
cd bank-statements-api
poetry run python run.py                    # Start dev server (port 8000)
poetry run pytest                           # Run tests
poetry run pytest --cov                     # Run tests with coverage
poetry run alembic upgrade head             # Run migrations
peotry run isort .                          # Check code formatting
poetry run ruff check .                     # Lint code
poetry run black .                          # Format code
```

IMPORTANT: isort, black and ruff MUST run inside the bank-statements-api folder

## Frontend (pnpm)
```bash
cd bank-statements-web
pnpm run dev                                 # Start dev server (port 5173)
pnpm run build                              # Build for production
pnpm run test                               # Run unit tests
pnpm run lint                               # Lint code
pnpm run format                             # Format with Prettier
```

## E2E Testing
```bash
cd e2e/bank-statements-web
pnpm test                                   # Run Playwright E2E tests
```

## Docker Development
```bash
docker-compose up                           # Start all services
docker-compose up db                        # Start only database
```

## Notes

- During development, the backend is always running with hot reload, so changes are reflected immediately.
- When changing a behaviour, make sure you update the relevant tests to maintain coverage.
- use the same format for the code as the rest of the codebase.
- dont use prettier

## Development Database

- The test database is called bank-statements-test and it's running on port 15432
- To run migrations on the test database, use:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:15432/bank_statements_test alembic upgrade head   
```

**IMPORTANT**: Depending on the task, you may also need to refer to these guides:
- **General Code Development Rules** - `/docs/guides/development-guidelines.md`
- **TypeScript Development Rules** - `/docs/guides/typescript-development-rules.md`
- **Python Development Rules** - `/docs/guides/python-development-rules.md`
- **React Development Rules** - `/docs/guides/react-development-rules.md`
- **FastAPI Development Rules** - `/docs/guides/fastapi-development-rules.md`

```

Both the frontend and backend services are running in development mode with hot reloading enabled, ports 8010 and 6173, so changes are reflected immediately without needing to restart the server.
