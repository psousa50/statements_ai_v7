# Bank Statement Analyzer

A web application for uploading, parsing, and analyzing bank statements.

## Project Overview

This project is a steel thread implementation of the Bank Statement Analyzer, demonstrating the core functionality of the system from end to end. It includes:

1. A PostgreSQL database with a table for transactions
2. A FastAPI backend API to add and list transactions
3. A React frontend to display transactions

## Architecture

The project follows a service-oriented architecture with a clear separation of concerns:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Backend

The backend follows Hexagonal Architecture (Ports and Adapters) pattern:

- Domain models define the core entities
- Repository ports define interfaces for data access
- Repository adapters implement these interfaces
- Application services contain business logic
- API endpoints expose the functionality

### Frontend

The frontend follows a modular architecture:

- API client layer for backend communication
- React hooks for business logic
- Components for UI presentation
- Clear separation of concerns

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL

### Setup

1. Clone the repository
2. Set up the backend:
   ```
   cd bank-statements-api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```
3. Create a PostgreSQL database:
   ```
   createdb bank_statements
   ```
4. Initialize the database:
   ```
   python -m app.db_init
   ```
5. Set up the frontend:
   ```
   cd ../bank-statements-web
   npm install
   ```

### Running the Application

1. Start the backend:
   ```
   cd bank-statements-api
   python run.py
   ```
2. Start the frontend:
   ```
   cd bank-statements-web
   npm run dev
   ```
3. Access the application at http://localhost:5173

## Project Structure

```
bank-statements-api/       # Backend API
├── app/
│   ├── api/               # API endpoints
│   ├── core/              # Core configuration
│   ├── domain/            # Domain models
│   ├── ports/             # Repository interfaces
│   ├── adapters/          # Repository implementations
│   └── services/          # Application services
└── ...

bank-statements-web/       # Frontend application
├── src/
│   ├── components/        # UI components
│   ├── pages/             # Page components
│   ├── services/          # API clients and hooks
│   └── types/             # TypeScript types
└── ...
```

## Future Enhancements

This steel thread implementation can be extended with:

- File upload and parsing functionality
- Transaction categorization
- Data visualization
- User authentication
- Export functionality
