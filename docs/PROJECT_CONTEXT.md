# Project Context

## What This Is

Bank statement analyser - upload CSV/XLSX bank statements, parse transactions, categorise them (manually or via AI/rules), and analyse spending.

## Tech Stack

| Layer | Tech | Notes |
|-------|------|-------|
| Frontend | React + Vite + MUI | Port 5173 (dev) |
| Backend | FastAPI + SQLAlchemy | Port 8000 (dev) |
| Database | PostgreSQL 15 | Docker locally, Neon in prod |
| AI | Groq / Gemini | Groq preferred (better rate limits) |

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

## AI Integration

| Feature | Purpose | Status |
|---------|---------|--------|
| Schema Detection | Auto-detect column mappings in statements | Disabled (using heuristics) |
| Rule Category Suggestions | AI suggests categories for enhancement rules | ✅ Wired (Enhancement Rules page) |
| Rule Counterparty Suggestions | AI suggests counterparties for enhancement rules | ✅ Wired (Enhancement Rules page) |
| Transaction Categorisation | AI-powered category assignment per transaction | Implemented, not wired |
| Counterparty Identification | Detect inter-account transfers | Implemented, not wired |

**Providers** (in priority order):
1. Groq (`llama-3.3-70b-versatile`) - preferred, better rate limits
2. Google Gemini (`gemini-2.0-flash`) - fallback

**Config**: `GROQ_API_KEY` or `GEMINI_API_KEY` env var
**Key files**: `app/ai/` directory (groq_ai.py, gemini_ai.py, prompts.py, llm_client.py)

### Enhancement Rules

Rules are auto-generated during statement upload via heuristic normalisation (source: `AUTO`) or manually created (source: `MANUAL`).

When AI suggests a category/counterparty for a rule:
- `ai_suggested_category_id` / `ai_suggested_counterparty_id` stores the suggestion
- When applied, these remain set so we can show ✨ indicator for AI-set values
- Compare `ai_suggested_category_id === category_id` to detect AI-set categories

**AI Suggestion Targeting**: By default, AI suggestions target **unconfigured rules** (rules with no category AND no counterparty). You can also pass specific `rule_ids` to process any rules.

**Applying Rules to Transactions**: When a rule is applied to existing transactions, it only updates transactions with status:
- `UNCATEGORIZED` - no category assigned
- `RULE_BASED` - previously categorised by another rule (can be overwritten)
- `FAILURE` - failed previous categorisation

Transactions with `MANUAL` status are never overwritten by rules.

## Common Tasks

| Task | Command/Notes |
|------|---------------|
| Start everything | `pnpm start` |
| Run migrations | `pnpm db:migrate` |
| Copy local → Neon | Use `pg_dump` locally, `psql` to Neon connection string |
| Deploy | Automatic via GitHub Actions on push to main |
