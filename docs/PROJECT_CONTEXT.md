# Project Context

## What This Is

Bank statement analyser - upload CSV/XLSX bank statements, parse transactions, categorise them (manually or via AI/rules), and analyse spending.

## Tech Stack

| Layer | Tech | Notes |
|-------|------|-------|
| Frontend | React + Vite + MUI | Port 5173 (dev) |
| Backend | FastAPI + SQLAlchemy | Port 8000 (dev) |
| Database | PostgreSQL 15 | Docker locally, Neon in prod |
| AI | Google Gemini | Schema detection + categorisation |

## Environments

### Local Development
- **DB**: Docker container on port `54321` (via `pnpm db:start`)
- **Test DB**: Port `15432` (via `pnpm test:db:up`)
- **Connection**: `postgresql://postgres:postgres@localhost:54321/bank_statements`

### Production
- **Frontend**: Cloudflare Pages
- **Backend**: Render
- **Database**: Neon (managed Postgres)
- **Connection**: Via `DATABASE_URL` env var on Render

## Key Entities

- **User** - OAuth (Google) authenticated users
- **Account** - Bank accounts
- **Statement** - Uploaded statement files
- **Transaction** - Individual transactions with categorisation
- **Category** - Hierarchical categories (parent/child)
- **EnhancementRule** - Pattern rules for auto-categorisation

## Common Tasks

| Task | Command/Notes |
|------|---------------|
| Start everything | `pnpm start` |
| Run migrations | `pnpm db:migrate` |
| Copy local → Neon | Use `pg_dump` locally, `psql` to Neon connection string |
| Deploy | Automatic via GitHub Actions on push to main |
