# Technical Context

## Technology Stack

### Backend

- Python 3.8+
- FastAPI - Web framework for building APIs
- SQLAlchemy - ORM for database interactions
- Pydantic - Data validation and settings management
- PostgreSQL - Relational database
- Uvicorn - ASGI server for running FastAPI applications

### Frontend

- TypeScript - Typed JavaScript
- React - UI library
- Vite - Build tool and development server
- Axios - HTTP client for API requests
- date-fns - Date utility library

### Testing (Planned)

- pytest - Backend testing
- Vitest - Frontend unit testing
- Playwright - End-to-end testing

### Deployment

- Docker - Containerization
- GitHub Actions - CI/CD
- Fly.io - Cloud hosting platform for test and dev environments
- Render - Cloud hosting platform for production
- Neon - PostgreSQL database hosting for test and dev environments

## Development Environment

### Backend Requirements

- Python 3.8+
- PostgreSQL
- Poetry (optional, for dependency management)

### Frontend Requirements

- Node.js 14+
- npm or yarn

## Project Setup

### Backend Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
poetry install

# Initialize the database
python -m app.db_init

# Run the application
python run.py
```

### Frontend Setup

```bash
# Install dependencies
pnpm install

# Run the development server
pnpm run dev
```

### Docker Setup

```bash
# Build and run the backend
cd bank-statements-api
docker build -t bank-statements-api .
docker run -p 8000:8000 -e DATABASE_URL=your_database_url bank-statements-api

# Build and run the frontend
cd bank-statements-web
docker build -t bank-statements-web .
docker run -p 80:80 bank-statements-web
```

### CI/CD Setup

The project uses GitHub Actions for CI/CD. The following workflows are defined:

- CI: Runs unit tests for both backend and frontend
- Test Environment Deployment: Deploys the backend and frontend to Fly.io in test mode
- End-to-End Testing: Runs Playwright tests against the test environment
- Development Environment Deployment: Deploys the backend and frontend to Fly.io in dev mode
- Production Environment Deployment: Deploys the backend and frontend to Render in production mode

See `docs/architecture/ci-cd.md` for more details.

## API Endpoints

### Current Endpoints

- `GET /api/v1/transactions` - Get all transactions
- `POST /api/v1/transactions` - Create a new transaction
- `GET /api/v1/transactions/{transaction_id}` - Get a transaction by ID
- `PUT /api/v1/transactions/{transaction_id}` - Update a transaction
- `DELETE /api/v1/transactions/{transaction_id}` - Delete a transaction

### Planned Endpoints

- `POST /api/v1/upload` - Upload a bank statement
- `GET /api/v1/categories` - Get all categories
- `POST /api/v1/export` - Export transactions

## Database Schema

### Current Schema

- `transactions` table:
  - `id` (UUID, primary key)
  - `date` (Date)
  - `description` (String)
  - `amount` (Decimal)
  - `created_at` (DateTime)

### Planned Schema

- `users` table
- `statements` table
- `categories` table
- `transactions` table

## Code Style Guidelines

### Python

- Use poetry for dependency management
- Do not use imports in the middle of the file, always at the top
- Do not use monkeypatch, ever, use dependency injection instead

### General Principles

- Clear, descriptive naming
- Modular, maintainable structure
- Do not write comments
- Do not write doc strings
