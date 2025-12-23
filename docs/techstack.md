# Tech Stack

## Frontend

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool |
| Material-UI (MUI) | Component library |
| React Router | Routing |
| Recharts | Data visualisation |
| Axios | HTTP client |
| date-fns | Date utilities |

## Backend

| Technology | Purpose |
|------------|---------|
| Python 3.10+ | Runtime |
| FastAPI | Web framework |
| SQLAlchemy 2.0 | ORM |
| Alembic | Database migrations |
| Pydantic | Data validation |
| uv | Package manager |
| Uvicorn | ASGI server |

## AI/ML

| Technology | Purpose |
|------------|---------|
| Google Gemini | Transaction categorisation, schema detection |

## Database

| Technology | Purpose |
|------------|---------|
| PostgreSQL 15 | Primary database |
| Neon (prod) | Serverless PostgreSQL hosting |

## Infrastructure

| Service | Purpose | Cost |
|---------|---------|------|
| Cloudflare Pages | Frontend hosting | Free |
| Render | Backend hosting | Free (750 hrs/month) |
| Neon | Database hosting | Free (0.5GB) |
| GitHub Actions | CI/CD | Free |

## Development Tools

| Tool | Purpose |
|------|---------|
| pnpm | Monorepo package manager |
| Docker Compose | Local development environment |
| Playwright | E2E testing |
| Vitest | Frontend unit testing |
| pytest | Backend testing |
| Ruff | Python linting |
| Black | Python formatting |
| isort | Python import sorting |

## Project Structure

```
statements-ai-v7/
├── bank-statements-api/     # FastAPI backend
├── bank-statements-web/     # React frontend
├── e2e/                     # Playwright E2E tests
├── config/                  # Configuration files
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
└── .github/workflows/       # CI/CD pipelines
```
