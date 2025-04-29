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

### Deployment (Planned)
- Docker - Containerization
- GitHub Actions - CI/CD
- Render - Cloud hosting platform

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
pip install -e .

# Initialize the database
python -m app.db_init

# Run the application
python run.py
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```

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
