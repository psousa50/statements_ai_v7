# Technology Stack

This document outlines the technology choices for the Bank Statement Analyzer application across frontend, backend, database, and infrastructure components.

## Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Language | TypeScript | 4.9+ | Type-safe JavaScript development |
| Framework | React | 18.2+ | UI component library |
| Build Tool | Vite | 4.3+ | Fast development server and build tool |
| HTTP Client | Axios | 1.4+ | API communication |
| Date Handling | date-fns | 2.30+ | Date manipulation utilities |
| UI Framework | None (Custom CSS) | N/A | Custom styling for complete control |
| State Management | React Hooks | N/A | Local component state management |
| Testing | Vitest | 0.31+ | Unit testing framework |
| E2E Testing | Playwright | 1.34+ | End-to-end testing |
| Package Manager | pnpm | 8.6+ | Fast, disk space efficient package manager |

## Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Language | Python | 3.8+ | Backend development |
| Web Framework | FastAPI | 0.95+ | High-performance API framework |
| ASGI Server | Uvicorn | 0.22+ | ASGI server for FastAPI |
| ORM | SQLAlchemy | 2.0+ | Database interaction |
| Migrations | Alembic | 1.10+ | Database schema migrations |
| Validation | Pydantic | 1.10+ | Data validation and settings management |
| File Parsing | pandas | 2.0+ | Data manipulation and analysis |
| Testing | pytest | 7.3+ | Unit and integration testing |
| Dependency Management | Poetry | 1.4+ | Python dependency management |
| LLM Integration | Custom | N/A | Schema detection for bank statements |

## Database

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Database | PostgreSQL | 15+ | Relational database for persistent storage |
| Extensions | pgcrypto | N/A | UUID generation |
| Hosting (Dev/Test) | Neon | N/A | PostgreSQL database hosting |
| Hosting (Prod) | Render | N/A | PostgreSQL database hosting |

## Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Containerization | Docker | Application containerization |
| CI/CD | GitHub Actions | Continuous integration and deployment |
| Hosting (Dev/Test) | Fly.io | Cloud hosting platform |
| Hosting (Prod) | Render | Cloud hosting platform |
| Version Control | Git/GitHub | Source code management |
| Secrets Management | GitHub Secrets | Secure storage of credentials |

## Development Tools

| Tool | Purpose |
|------|---------|
| VS Code | Primary IDE |
| ESLint | JavaScript/TypeScript linting |
| Prettier | Code formatting |
| Ruff | Python linting |
| pytest-cov | Test coverage reporting |
| Docker Compose | Local development environment |
| pre-commit | Git hooks for code quality |

## Architecture Patterns

| Pattern | Implementation |
|---------|---------------|
| Hexagonal Architecture | Backend architecture with ports and adapters |
| Repository Pattern | Data access abstraction |
| Service Layer | Business logic encapsulation |
| Dependency Injection | Clean dependency management |
| React Hooks | Frontend business logic encapsulation |
| API Client Layer | HTTP abstraction in frontend |

## Testing Strategy

| Test Type | Tools | Coverage Target |
|-----------|-------|----------------|
| Backend Unit Tests | pytest | 90%+ |
| Frontend Unit Tests | Vitest | 85%+ |
| Integration Tests | pytest | Key integration points |
| E2E Tests | Playwright | Critical user journeys |
| CI Testing | GitHub Actions | Automated on every PR |

## Deployment Pipeline

| Stage | Environment | Platform | Database |
|-------|------------|----------|----------|
| CI | N/A | GitHub Actions | In-memory/Test container |
| Test | Test | Fly.io | Neon (branched) |
| Development | Dev | Fly.io | Neon (dev) |
| Production | Prod | Render | Render PostgreSQL |
