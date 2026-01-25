# Project: Bank Statements AI

## Overview
Personal finance application for uploading, parsing, and analysing bank statements with AI-powered transaction categorisation and insights.

## Tech Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL
- **Frontend:** React 18, TypeScript, Vite, MUI, TanStack Query
- **AI:** Gemini API (swappable via LLM abstraction)
- **Infrastructure:** Docker, GitHub Actions, Render (API), Cloudflare Pages (web), Neon (DB)

## Architecture
Monorepo with hexagonal architecture on the backend:
- `bank-statements-api/` - Python backend with ports/adapters pattern
- `bank-statements-web/` - React SPA
- `e2e/` - Playwright E2E tests

Backend layers: Routes → Services → Repositories (interfaces in `ports/`, implementations in `adapters/`)

## Directory Structure
```
bank-statements-api/
├── app/
│   ├── api/routes/       # FastAPI route handlers
│   ├── services/         # Business logic
│   ├── ports/repositories/   # Abstract repository interfaces
│   ├── adapters/repositories/ # SQLAlchemy implementations
│   ├── domain/models/    # SQLAlchemy models
│   └── ai/               # LLM abstraction layer
└── tests/                # pytest (unit + integration)

bank-statements-web/
├── src/
│   ├── pages/            # Route components
│   ├── components/       # Reusable UI
│   ├── services/hooks/   # TanStack Query hooks
│   └── api/              # API clients per domain
└── tests/                # Vitest component tests
```

## Development

Run all commands from root using pnpm.

### Quick Start
```bash
pnpm start              # Start db + dev servers (API :8000, Web :5173)
pnpm dev                # Dev servers only (assumes db running)
```

### Testing
```bash
pnpm test               # Run all tests
pnpm test:api           # Backend tests only
pnpm test:web           # Frontend tests only
pnpm test:e2e           # E2E tests (Playwright)
```

### Database
```bash
pnpm db:start           # Start db container + run migrations
pnpm db:migrate         # Run migrations only
pnpm test:db:up         # Start test db (port 15432)
pnpm test:db:migrate    # Migrate test db
```

### Linting & Formatting
```bash
pnpm format             # Format all code
pnpm lint               # Lint all code
pnpm lint:fix           # Lint and fix
pnpm check              # Type check (web) + lint (api)
pnpm verify             # Format + lint + test
```

### Deployment
```bash
pnpm deploy:setup       # Sync prod config to GitHub/Render
```

- Hot reload enabled on both services
- Update tests when changing behaviour

## Key Patterns

**Backend:**
- Repository pattern with interface/implementation split
- Dependency injection via `InternalDependencies` container
- Multi-tenant: all queries filtered by `user_id`
- Pydantic schemas: `*Create`, `*Update`, `*Response` naming

**Frontend:**
- API client per domain entity
- TanStack Query for server state, React Context for auth/theme
- URL search params for filter persistence
- Debounced inputs before API calls

**Testing:**
- Backend: pytest with `MagicMock(spec=Repository)` for unit tests
- Integration: real PostgreSQL on port 15432
- Frontend: Vitest with `createMockApiClient` factory
- E2E: `testLogin()` helper bypasses OAuth

## Key Files
- `bank-statements-api/app/core/dependencies.py` - DI container wiring
- `bank-statements-api/app/api/schemas.py` - All Pydantic models
- `bank-statements-web/src/api/` - API client implementations
- `config/settings.local.yaml` / `settings.prod.yaml` - Environment config

## Local Auth Bypass

For Chrome MCP / automation, the app must be running with `E2E_TEST_MODE=true`.

1. Navigate to the app (e.g., `http://localhost:5173`)
2. Call the test-login endpoint
3. Reload the page (required for React auth state to sync)

```javascript
await fetch('/api/v1/auth/test-login', { method: 'POST', credentials: 'include' });
location.reload();
```

This creates a test user (`e2e-test@example.com`) and sets auth cookies without requiring Google OAuth.
