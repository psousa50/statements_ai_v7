# Architecture

Personal finance app for uploading, parsing, and analysing bank statements with AI-powered categorisation.

## Tech Stack

Python 3.12 / FastAPI / SQLAlchemy 2.x / PostgreSQL | React 18 / TypeScript / Vite / MUI / TanStack Query | Gemini/Groq AI | Docker / GitHub Actions / Render / Cloudflare Pages / Neon

## Directory Structure

```
bank-statements-api/
├── app/
│   ├── api/
│   │   ├── routes/              # FastAPI route handlers per domain
│   │   ├── errors/              # Custom exception classes
│   │   └── schemas.py           # All Pydantic request/response models
│   ├── services/                # Business logic layer
│   │   ├── ai/                  # LLM-powered categorisation, counterparty, generation
│   │   ├── chat/                # Streaming chat with transaction insights
│   │   ├── schema_detection/    # Heuristic column mapping for uploads
│   │   └── statement_processing/# File parsing, normalisation, deduplication
│   ├── ports/
│   │   ├── repositories/        # Abstract repository interfaces (ABC)
│   │   └── categorizers/        # Abstract categoriser interface
│   ├── adapters/
│   │   └── repositories/        # SQLAlchemy repository implementations
│   ├── domain/
│   │   ├── models/              # SQLAlchemy ORM models (15 tables)
│   │   └── dto/                 # Data transfer objects
│   ├── ai/                      # LLM abstraction: Gemini, Groq, Noop clients
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env vars, secrets)
│   │   ├── database.py          # Engine, session factory, Base
│   │   ├── dependencies.py      # DI container (External + Internal)
│   │   └── auth/                # JWT, OAuth, password auth
│   └── common/                  # Text normalisation, JSON utilities
├── migrations/versions/         # Alembic migrations (20+)
└── tests/                       # pytest unit + integration tests

bank-statements-web/
├── src/
│   ├── pages/                   # Route components (15 pages)
│   ├── components/              # Feature-organised UI (layout, upload, charts, modals)
│   ├── services/hooks/          # TanStack Query hooks per domain
│   ├── api/                     # Typed API clients per entity + ApiContext
│   ├── auth/                    # AuthContext, ProtectedRoute, token refresh
│   ├── context/                 # ErrorContext, global error handler
│   ├── theme/                   # MUI theme (light/dark/system), ThemeContext
│   ├── types/                   # Domain TypeScript interfaces
│   └── utils/                   # Formatting, colour utilities
└── tests/                       # Vitest component tests

e2e/bank-statements-web/         # Playwright E2E tests (Chromium/Firefox/WebKit)
config/                          # settings.local.yaml, settings.prod.yaml
bin/                             # Shell scripts (dev, db, deploy, test)
```

## Data Flow

1. **Upload**: File → FileTypeDetector → StatementParser (CSV/Excel/OFX) → HeuristicSchemaDetector (column mapping) → TransactionNormalizer → deduplication → persist
2. **Categorisation**: Enhancement rules (exact/prefix/infix match with amount/date constraints) → LLM suggestions (batched) → manual override
3. **Query**: Route → Service → Repository (user_id filtered) → paginated response with running balances
4. **Chat**: User message → ChatService → LLM with transaction context → streamed SSE response

## Database Schema

| Table | Key Relationships |
|-------|------------------|
| `users` | Root entity; OAuth + password auth |
| `accounts` | Belongs to user; has currency; holds transactions |
| `transactions` | Belongs to account + statement; has category, counterparty_account, tags (M2M via `transaction_tags`) |
| `categories` | Hierarchical (max 2 levels via parent_id); has colour |
| `statements` | Belongs to account; stores raw file content |
| `enhancement_rules` | Pattern matching rules with AI suggestion fields |
| `tags` | M2M with transactions via junction table |
| `subscriptions` | One per user; tier (free/basic/pro) with Stripe integration |
| `subscription_usage` | Monthly counters for statements and AI calls |
| `filter_presets` | Saved filter configurations as JSONB |
| `file_analysis_metadata` | Cached schema detection results per file hash + account |
| `background_jobs` | Job queue with status tracking |
| `uploaded_files` | Raw file storage for processing |
| `refresh_tokens` | Hashed tokens for JWT refresh |

## API Surface

All routes under `/api/v1`, all require authentication.

| Domain | Endpoints | Key Operations |
|--------|-----------|---------------|
| Transactions | 11 | CRUD, bulk categorise/tag, category totals, time series, recurring patterns |
| Statements | 6 | Analyse (schema detect + preview), upload, preview-filter, preview-statistics |
| Categories | 7 | CRUD, CSV import, AI suggestions, generate from transactions |
| Accounts | 6 | CRUD, CSV import, initial balance |
| Enhancement Rules | 6 | CRUD, apply rule, preview matches, AI suggestions |
| Tags | 5 | CRUD, add/remove from transaction, bulk add |
| Auth | 7 | Register, login, OAuth (Google), refresh, logout, test-login |
| Chat | 1 | Streaming chat with financial insights |
| Filter Presets | 4 | CRUD for saved filters |
| Subscription | 2 | Get info, Stripe portal session |

## Configuration

| Layer | Mechanism |
|-------|-----------|
| Backend settings | Pydantic BaseSettings loading from `.env` (generated from `config/settings.*.yaml`) |
| Frontend settings | `VITE_*` env vars injected at build time |
| LLM provider | Auto-selected: E2E mode → Noop, else Groq (if key) → Gemini (if key) → Noop |
| Feature gates | Subscription tier limits checked via SubscriptionService |
| Env generation | `bin/generate-env-files.py` reads YAML config, writes `.env` files for root/api/web |

## Auth

- **Google OAuth 2.0** (primary) via Authlib
- **Email/password** (secondary) with bcrypt hashing
- **JWT access tokens** (HS256, 15 min) + **database-backed refresh tokens** (7 days)
- Both stored as httpOnly secure cookies; SameSite=none (HTTPS) or lax (local)
- Token refresh every 14 min on frontend via axios interceptor
- E2E bypass: `POST /auth/test-login` when `E2E_TEST_MODE=true`

## Key Patterns

- **Hexagonal architecture**: ports (interfaces) in `ports/`, adapters (implementations) in `adapters/`
- **DI container**: `ExternalDependencies` (session, LLM) → `InternalDependencies` (21 services wired to repos)
- **Multi-tenancy**: all repository queries auto-filter by `user_id`
- **Schema naming**: Pydantic `*Create`, `*Update`, `*Response`; SQLAlchemy models map to tables
- **Frontend layers**: Pages → Components → Hooks (TanStack Query) → API Clients → Context providers
- **State management**: server state in TanStack Query, auth/theme/errors in React Context, filters in URL params
- **Error handling**: global mutation cache → ErrorProvider → Toast/SubscriptionErrorDialog
- **CI/CD**: GitHub Actions with path-based filtering → unit tests → E2E (Docker) → deploy to Render + Cloudflare Pages
