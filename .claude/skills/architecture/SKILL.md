---
name: architecture
description: Explains this project's architecture, components, and data flow
---

# Architecture

## Overview

Bank Statements AI - a personal finance application for analysing bank statements. Users upload bank statements (CSV/Excel), which are parsed, deduplicated, and stored. Transactions can be categorised manually or via AI-powered enhancement rules. The app provides charts, recurring expense analysis, and multi-account support.

## Stack

- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, MUI, TanStack Query, Recharts
- **AI**: Groq or Gemini LLM (configurable, with NoopLLM for testing)
- **Infra**: Docker Compose (local), Render (production), pnpm monorepo

## Architectural Pattern

Backend follows **Hexagonal Architecture** (Ports & Adapters):

```
app/
  ports/repositories/     # Abstract interfaces (ABC)
  adapters/repositories/  # SQLAlchemy implementations
  domain/models/          # SQLAlchemy ORM models
  domain/dto/             # Data transfer objects
  services/               # Business logic layer
  api/routes/             # FastAPI route handlers
  api/schemas.py          # Pydantic request/response schemas
  core/                   # Config, database, dependency injection
  ai/                     # LLM client abstraction layer
```

## Key Components

### Backend (`bank-statements-api/`)

| Layer | Purpose |
|-------|---------|
| `app/api/routes/` | HTTP endpoints, request validation, response serialization |
| `app/services/` | Business logic, orchestration, transaction handling |
| `app/adapters/repositories/` | Database access, SQL queries |
| `app/ports/repositories/` | Repository interfaces for dependency inversion |
| `app/domain/models/` | SQLAlchemy ORM entities |
| `app/ai/` | LLM abstraction (Groq/Gemini/Noop) |
| `app/core/dependencies.py` | Dependency injection container |

### Frontend (`bank-statements-web/`)

| Directory | Purpose |
|-----------|---------|
| `src/pages/` | Route-level components (Transactions, Charts, Upload, etc.) |
| `src/components/` | Reusable UI components |
| `src/api/` | API clients (one per domain entity) |
| `src/auth/` | AuthContext, ProtectedRoute |
| `src/theme/` | MUI theme configuration |
| `src/types/` | TypeScript interfaces |

## Data Flow

### Statement Upload Flow
1. User uploads CSV/Excel via `Upload.tsx`
2. `StatementClient.ts` POSTs to `/api/v1/statements/analyze`
3. `statement_analyzer_service.py` detects format, parses, normalizes
4. `statement_upload_service.py` deduplicates and persists
5. `TransactionRuleEnhancementService` applies matching rules

### Transaction Categorization Flow
1. Enhancement rules (pattern matching) auto-categorize on upload
2. Manual categorization via `TransactionTable.tsx` -> `CategorySelector`
3. AI suggestions via `LLMRuleCategorizer` (prompts in `ai/prompts.py`)

### API Request Flow
```
FastAPI Route -> Depends(provide_dependencies) -> InternalDependencies
             -> Service -> Repository -> Database
```

## Directory Structure

```
statements-ai-v7/
  bank-statements-api/       # Python FastAPI backend
    app/                     # Application code
    migrations/              # Alembic migrations
    tests/                   # pytest (unit, api, integration)
  bank-statements-web/       # React TypeScript frontend
    src/                     # Application code
    tests/                   # vitest tests
  e2e/                       # Playwright tests
  bin/                       # Shell scripts for dev/deploy
  config/                    # Environment configurations
  docker-compose.yml         # Local dev infrastructure
```

## Key Files

| File | Purpose |
|------|---------|
| `bank-statements-api/app/main.py` | FastAPI app entry point |
| `bank-statements-api/app/app.py` | Route registration |
| `bank-statements-api/app/core/dependencies.py` | DI container, service wiring |
| `bank-statements-api/app/core/config.py` | Settings from environment |
| `bank-statements-web/src/main.tsx` | React entry point |
| `bank-statements-web/src/App.tsx` | Router configuration |
| `package.json` | Monorepo scripts |
| `docker-compose.yml` | Local PostgreSQL, API, Web services |

## Domain Entities

- **Transaction**: Core entity (date, amount, description, category, account)
- **Category**: Hierarchical (parent_id), user-scoped
- **Account**: Bank accounts (name, currency)
- **EnhancementRule**: Pattern matching rules for auto-categorization
- **Statement**: Uploaded file metadata
- **User**: OAuth/password authentication

## Authentication

- OAuth 2.0 (Google, GitHub) via Authlib
- Password auth with bcrypt
- JWT access tokens (15min) + refresh tokens (stored in DB)
- Frontend: React Context (`AuthContext.tsx`) with automatic token refresh
- Backend: `require_current_user` dependency for protected routes

## Testing Strategy

- **Unit tests**: `tests/unit/`, `tests/api/`, `tests/services/`
- **Integration tests**: `tests/integration/` (requires test-db container)
- **Web tests**: `bank-statements-web/tests/` (vitest + testing-library)
- **E2E tests**: `e2e/` (Playwright)
