# Bank Statement Analyzer

A web application for uploading, parsing, categorizing, and analyzing bank statements.

## Project Overview

This project is a comprehensive implementation of the Bank Statement Analyzer, providing end-to-end functionality for processing bank statements. It includes:

1. A PostgreSQL database with tables for transactions, categories, uploaded files, and file analysis metadata
2. A FastAPI backend API with statement processing architecture and transaction categorization
3. A React frontend with transaction management and file upload UI
4. End-to-end testing with Playwright
5. CI/CD pipeline with GitHub Actions

## Architecture

The project follows a service-oriented architecture with a clear separation of concerns:

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Backend

The backend follows Hexagonal Architecture (Ports and Adapters) pattern:

- Domain models define the core entities (transactions, categories, uploaded files, etc.)
- Repository ports define interfaces for data access
- Repository adapters implement these interfaces
- Application services contain business logic
- Statement processing architecture for parsing and normalizing bank statements
- Transaction categorization system with hierarchical categories
- API endpoints expose the functionality

### Frontend

The frontend follows a modular architecture:

- API client layer for backend communication
- React hooks for business logic
- Components for UI presentation
- File upload UI with drag-and-drop functionality
- Column mapping customization for uploaded files
- Transaction table with categorization
- Clear separation of concerns

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL

### Setup

1. Clone the repository
1. Set up the backend:

```bash
   cd bank-statements-api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
```

1. Create a PostgreSQL database:

```bash
   createdb bank_statements
```

1. Initialize the database:

```bash
   python -m app.db_init
```

1. Set up the frontend:

```bash
   cd ../bank-statements-web
   npm install
```

### Configuration

The project uses a centralized configuration system. All ports, URLs, and settings are managed from a single YAML file.

1. Copy the example configuration:

```bash
   cp config/settings.yaml.example config/settings.yaml
```

2. Edit `config/settings.yaml` to customise your configuration:

```yaml
   ports:
     api: 8010    # Backend API port
     web: 5173    # Frontend dev server port
     database: 54321  # PostgreSQL port
```

3. Generate environment files:

```bash
   python scripts/generate_env_files.py
```

   This creates `.env` files for the root, backend, and frontend with the correct settings.

4. Restart your services to apply the changes.

### Running the Application

1. Start the backend:

```bash
   cd bank-statements-api
   python run.py
```

1. Start the frontend:

```bash
   cd bank-statements-web
   npm run dev
```

1. Access the application at <http://localhost:5173>

### Database Backup and Restore

The project includes commands for backing up and restoring your PostgreSQL database.

**Creating a backup:**

```bash
pnpm db:backup
```

This creates a timestamped backup file in the `backups/` directory (e.g., `backups/bank_statements_20251025_143022.dump`). The backup uses PostgreSQL's custom format, which is compressed and supports parallel restore.

**Restoring from a backup:**

```bash
FILE=backups/bank_statements_20251025_143022.dump pnpm db:restore
```

**Important:** The restore command will drop existing tables before restoring, so make sure you have a current backup before running it.

## Project Structure

```bash
bank-statements-api/       # Backend API
├── app/
│   ├── ai/                # LLM integration for schema detection
│   ├── api/               # API endpoints
│   ├── core/              # Core configuration
│   ├── domain/            # Domain models
│   │   └── models/        # Transaction, Category, UploadedFile, etc.
│   ├── ports/             # Repository interfaces
│   │   ├── repositories/  # Data access interfaces
│   │   └── categorizers/  # Categorization interfaces
│   ├── adapters/          # Repository implementations
│   └── services/          # Application services
│       ├── transaction.py # Transaction service
│       ├── category.py    # Category service
│       ├── transaction_categorization.py # Categorization service
│       └── source.py      # Source service
├── migrations/            # Database migrations
└── tests/                 # Unit and integration tests

bank-statements-web/       # Frontend application
├── src/
│   ├── components/        # UI components
│   │   ├── TransactionForm.tsx  # Transaction form
│   │   ├── TransactionTable.tsx # Transaction table
│   │   └── upload/        # File upload components
│   │       ├── FileUploadZone.tsx    # Drag-and-drop upload
│   │       ├── ColumnMappingTable.tsx # Column mapping
│   │       └── SourceSelector.tsx    # Source selection
│   ├── pages/             # Page components
│   │   ├── Transactions.tsx # Transactions page
│   │   └── Upload.tsx     # Upload page
│   ├── services/          # API clients and hooks
│   │   ├── api/           # API clients
│   │   └── hooks/         # React hooks
│   └── types/             # TypeScript types
└── tests/                 # Unit and integration tests

e2e/                      # End-to-end tests
└── bank-statements-web/   # Playwright tests
```

## Key Features

### Statement Processing Architecture

- File type detection (CSV, XLSX)
- Statement parsing with pandas
- Schema detection using LLM
- Transaction normalization
- Deduplication via file hashing

### Transaction Categorization

- Hierarchical category system (parent-child relationships)
- Batch processing of uncategorized transactions
- API endpoint for triggering categorization

### File Upload UI

- Drag-and-drop file upload
- Column mapping customization
- Source selection
- Validation and analysis feedback

### Database Structure

- Transactions table with categorization
- Categories table with hierarchical structure
- UploadedFile table for raw file content
- FileAnalysisMetadata table for analysis results

## Future Enhancements

Planned enhancements include:

- Data visualization (charts and reports)
- User authentication
- Export functionality
- Automatic categorization using machine learning
- Transaction search and filtering
- Dashboard with financial insights
