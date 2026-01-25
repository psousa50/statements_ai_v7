---
name: infrastructure
description: Explains this project's infrastructure, deployment, and DevOps setup
---

# Infrastructure Guide

## Architecture Overview

Monorepo with three main components:
- **bank-statements-api**: Python 3.10 FastAPI backend
- **bank-statements-web**: React/Vite frontend
- **e2e/bank-statements-web**: Playwright E2E tests

## Containerisation

### Local Development (docker-compose.yml)

Services:
- `db`: PostgreSQL 15 (port 54321)
- `test-db`: PostgreSQL 15 for tests (port 15432, profile: test)
- `api`: Python backend (port 8000)
- `web`: Node.js dev server (port 5173)

Key commands:
```bash
pnpm start          # Start db + dev servers
pnpm dev            # Dev servers only (assumes db running)
pnpm docker:up      # Full docker-compose stack
```

### Production Dockerfiles

**API** (`/bank-statements-api/Dockerfile`):
- Base: `python:3.10-slim`
- Uses `uv` for dependency management
- Exposes port 8000

**Web** (`/bank-statements-web/Dockerfile`):
- Multi-stage build: Node 18 Alpine -> Nginx Alpine
- Build arg: `VITE_API_URL`
- Exposes port 80

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/deploy.yml`)

Triggers on push to `main` branch.

**Jobs:**

1. **detect-changes**: Uses `dorny/paths-filter` to determine which services changed
2. **test-backend**: Runs if API changed
   - Spins up PostgreSQL service
   - Installs via `uv`
   - Runs: isort, black, ruff checks
   - Runs: alembic migrations + pytest
3. **test-frontend**: Runs if web changed
   - Installs via pnpm
   - Runs: TypeScript check, ESLint, Vitest
4. **e2e-tests**: Runs after unit tests pass
   - Uses docker-compose with `E2E_TEST_MODE=true`
   - Runs Playwright (Chromium only)
5. **deploy**: Runs if e2e passes AND `vars.DEPLOY_ENABLED == 'true'`
   - Triggers Render deploy hook (API)
   - Builds web with production `VITE_API_URL`
   - Deploys to Cloudflare Pages via Wrangler

## Deployment

### Backend: Render.com

Configuration in `/render.yaml`:
- Runtime: Python (free plan)
- Region: Frankfurt
- Auto-deploy: disabled (triggered via webhook)
- Build: `pip install uv && uv sync`
- Start: `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend: Cloudflare Pages

Deployed via `wrangler pages deploy` in CI.

### Database: Neon

PostgreSQL hosted on Neon (eu-central-1).
- Connection pooling enabled
- SSL required

## Environments

### Configuration Files

- `/config/settings.local.yaml`: Local development settings
- `/config/settings.prod.yaml`: Production settings (contains secrets - gitignored)

Both contain:
- `urls.api` / `urls.web`
- `database.url`
- `secrets.*` (API keys, OAuth credentials)
- `deployment.*` (Render/Cloudflare credentials)

### Environment Variables

Root `.env` sets local defaults:
```
API_PORT=8000
WEB_PORT=5173
DB_PORT=54321
```

### Deployment Setup Scripts

```bash
pnpm deploy:setup           # Sync settings.prod.yaml to GitHub secrets + Render
pnpm deploy:setup:github    # GitHub secrets only
pnpm deploy:setup:render    # Render env vars only
```

Scripts read from `/config/settings.prod.yaml` and:
- Set GitHub Actions secrets via `gh` CLI
- Set Render env vars via Render API

## Cloud Services

| Service | Purpose |
|---------|---------|
| Render.com | API hosting (Python backend) |
| Cloudflare Pages | Static frontend hosting |
| Neon | Managed PostgreSQL database |
| Google OAuth | Authentication |
| Gemini API | AI/ML features |

## Monitoring

No dedicated monitoring setup. Relies on:
- Render's built-in logging
- Cloudflare Pages analytics
- Application-level `/health` endpoint

## Key Files

| File | Purpose |
|------|---------|
| `/docker-compose.yml` | Local development orchestration |
| `/render.yaml` | Render.com service definition |
| `/.github/workflows/deploy.yml` | CI/CD pipeline |
| `/config/settings.prod.yaml` | Production configuration |
| `/bin/deploy-github-secrets.py` | Sync secrets to GitHub |
| `/bin/deploy-render-env.py` | Sync env vars to Render |
