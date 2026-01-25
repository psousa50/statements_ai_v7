---
name: build
description: Explains how to build, test, and develop this project
---

# Build & Development

## Prerequisites

- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Python >= 3.9
- uv (Python package manager)
- Docker and Docker Compose

## Installation

```bash
pnpm install              # Install all dependencies (web + e2e + api)
pnpm install:web          # Install web dependencies only
pnpm install:api          # Install API dependencies only (uses uv sync)
pnpm install:e2e          # Install E2E test dependencies
```

## Running Locally

```bash
pnpm start                # Start db + dev servers (API :8000, Web :5173)
pnpm dev                  # Dev servers only (assumes db running)
pnpm start:e2e            # Start with E2E_TEST_MODE=true for local auth bypass
pnpm stop                 # Stop dev servers
```

API runs on port 8000, web on port 5173. Hot reload enabled on both.

## Database

```bash
pnpm db:start             # Start db container + run migrations
pnpm db:up                # Start db container only
pnpm db:migrate           # Run migrations
pnpm db:rollback          # Rollback migrations
pnpm db:destroy           # Remove db container and volumes
pnpm db:sync:from-neon    # Sync from production (Neon) to local
pnpm db:sync:to-neon      # Sync from local to production
```

Test database (port 15432):

```bash
pnpm test:db:up           # Start test db
pnpm test:db:migrate      # Run migrations on test db
pnpm test:db:down         # Stop test db
```

## Testing

```bash
pnpm test                 # Run all tests (unit + integration + web)
pnpm test:unit            # Unit tests only (api + web)
pnpm test:api             # Backend tests (unit + integration)
pnpm test:api:unit        # Backend unit tests only
pnpm test:api:integration # Backend integration tests (requires test db)
pnpm test:web             # Frontend tests (vitest)
pnpm test:e2e             # E2E tests (Playwright)
pnpm test:e2e:ui          # E2E tests with UI
```

## Building

```bash
pnpm build                # Build web for production
pnpm build:web            # Same as above (vite build)
```

Output goes to `bank-statements-web/dist/`.

## Linting & Formatting

```bash
pnpm format               # Format all code
pnpm lint                 # Lint all code
pnpm lint:fix             # Lint and auto-fix
pnpm check                # Type check (web) + lint (api)
pnpm verify               # Format + lint + test (full validation)
```

Backend uses: ruff, black, isort
Frontend uses: eslint, prettier, typescript

## Environment Variables

Configuration via `settings.yaml` files. Key variables:

- `DATABASE_URL` - PostgreSQL connection string
- `TEST_DATABASE_URL` - Test database connection
- `VITE_API_URL` - API URL for frontend
- `E2E_TEST_MODE` - Enable test auth bypass

## Deployment

Backend: Render (via deploy hook)
Frontend: Cloudflare Pages

```bash
pnpm deploy:setup         # Sync secrets to GitHub + Render
```

CI/CD runs on push to main:
1. Detect changes (api/web)
2. Run backend tests (if api changed)
3. Run frontend tests (if web changed)
4. Run E2E tests
5. Deploy to production

## Docker

```bash
pnpm docker:up            # Start all services
pnpm docker:down          # Stop all services
pnpm docker:build         # Build images
```

## Common Tasks

```bash
pnpm reset                # Clean + reinstall dependencies
pnpm clean                # Remove build artifacts and caches
pnpm config:generate      # Generate env files from settings.yaml
```
