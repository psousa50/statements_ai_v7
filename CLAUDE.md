# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bank Statement Analyzer is a full-stack web application for importing, categorizing, and analyzing bank statements. It consists of a FastAPI backend (`bank-statements-api/`) and React frontend (`bank-statements-web/`) with PostgreSQL database.

## Development Commands

### Backend (Poetry)
```bash
cd bank-statements-api
poetry run python run.py                    # Start dev server (port 8000)
poetry run pytest                           # Run tests
poetry run pytest --cov                     # Run tests with coverage
poetry run alembic upgrade head             # Run migrations
poetry run ruff check .                     # Lint code
poetry run black . --line-length 160        # Format code
```

### Frontend (pnpm)
```bash
cd bank-statements-web
pnpm run dev                                 # Start dev server (port 5173)
pnpm run build                              # Build for production
pnpm run test                               # Run unit tests
pnpm run lint                               # Lint code
pnpm run format                             # Format with Prettier
```

### E2E Testing
```bash
cd e2e/bank-statements-web
pnpm test                                   # Run Playwright E2E tests
```

### Docker Development
```bash
docker-compose up                           # Start all services
docker-compose up db                        # Start only database
```

## Architecture

### Backend (Hexagonal Architecture)
- **Domain Models**: Core entities in `app/domain/models/`
- **Ports**: Repository interfaces in `app/ports/repositories/`
- **Adapters**: Repository implementations in `app/adapters/repositories/`
- **Services**: Business logic in `app/services/`
- **API Routes**: FastAPI endpoints in `app/api/routes/`
- **Background Jobs**: Async processing in `app/workers/`

### Frontend (Component Architecture)
- **Pages**: Route components in `src/pages/`
- **Components**: Reusable UI in `src/components/`
- **API Clients**: HTTP communication in `src/api/`
- **Hooks**: Business logic in `src/services/hooks/`
- **Types**: TypeScript definitions in `src/types/`

## Key Services

### Statement Processing Flow
1. **File Upload**: CSV/XLSX file detection and storage
2. **Schema Detection**: Heuristic/LLM-based column mapping
3. **Transaction Import**: Data normalization and deduplication
4. **Background Categorization**: AI-powered transaction categorization

### Transaction Categorization
- **Hierarchical Categories**: Parent-child relationships
- **Rule-Based**: Pattern matching for automatic categorization
- **LLM Integration**: Google Gemini AI for intelligent categorization
- **Batch Processing**: Bulk categorization operations

## Development Patterns

### Backend Patterns
- **Dependency Injection**: Use FastAPI's `Depends()` for clean DI
- **Repository Pattern**: Abstract data access via repository interfaces
- **Service Layer**: Encapsulate business logic in service classes
- **Background Jobs**: Use `BackgroundJobService` for async tasks

### Frontend Patterns
- **API Context**: Use `ApiContext` for centralized API client access
- **Custom Hooks**: Encapsulate data fetching and state management
- **Component Composition**: Build complex UIs from smaller components
- **Type Safety**: Maintain strict TypeScript types across API boundaries

## Testing Strategy

- **Backend**: 90%+ coverage with pytest, SQLAlchemy test fixtures
- **Frontend**: 85%+ coverage with vitest, component testing
- **Integration**: End-to-end workflow testing
- **E2E**: Critical user journeys with Playwright

## Database Schema

Core entities: `Transaction`, `Category`, `Account`, `UploadedFile`, `FileAnalysisMetadata`, `BackgroundJob`. Use Alembic for migrations.

## File Organization

When adding new features, follow existing patterns:
- Backend: Create service → repository interface → adapter implementation → API route → tests
- Frontend: Create component → hook → API client method → tests
- Maintain separation between domain logic and infrastructure concerns

## Notes

- During development, the backend is always running with hot reload, so changes are reflected immediately.
- When changing a behaviour, make sure you update the relevant tests to maintain coverage.
- use the same format for the code as the rest of the codebase.