# System Patterns

## Architecture

The application follows a service-oriented architecture, composed of a React frontend, a FastAPI backend, and a PostgreSQL database. The backend is responsible for receiving file uploads, parsing bank statements (CSV, Excel), and storing transaction data. The frontend communicates with the backend over RESTful APIs, allowing users to interact with their uploaded and processed data.

### Backend

The backend follows Hexagonal Architecture (Ports and Adapters):

- The router/controller depends only on an application service, not on infrastructure details.
- The application service implements the business logic and uses ports (interfaces) to interact with external systems like databases.
- The actual infrastructure code (database repositories) is implemented as adapters and injected via ports.
- The domain logic is isolated, testable, and independent of frameworks and infrastructure.
- There is clear separation of concerns across all layers.
- No database access or business logic in route handlers.
- Dependency injection is used for clean, idiomatic code.

### Frontend

The frontend follows a modular and production-ready architecture:

- No direct HTTP calls inside components (no fetch or axios inside useEffect)
- A typed API client layer (built with axios) wraps all HTTP requests
- Pages and components depend only on a clean interface to the API (e.g. TransactionsApi.getAll()), not on HTTP details
- Hooks expose business operations (e.g. useTransactions) and keep components clean
- There is clear separation between presentation, hooks, and data-fetching logic

## Key Components

### Backend (FastAPI)

- Transaction API (create, read, update, delete)
- Transaction storage and retrieval
- (Planned) File upload API
- (Planned) Statement parsing (CSV, Excel)
- (Planned) Categorization logic
- (Planned) Export endpoint
- (Planned) Authentication

### Frontend (React)

- Transaction form for adding new transactions
- Transaction table for displaying transactions
- (Planned) File upload interface
- (Planned) UI to categorize/edit/export transactions
- (Planned) Authentication

### Database (PostgreSQL)

- Transactions table
- (Planned) Users table
- (Planned) Uploaded statements table
- (Planned) Categories table

### Testing

- (Planned) Backend: pytest
- (Planned) Frontend: vitest (unit), Playwright (e2e)

### Deployment

- GitHub Actions for CI/CD
- Docker for containerization
- Run unit tests on containers
- Deploy the backend and frontend in test mode to Fly.io. Use a branched Neon database from a clean one.
- Run e2e tests (Playwright) on the deployed app in test
- Deploy the backend and frontend in dev mode to Fly.io Use a dev database in Neon
- Deploy the backend and frontend in prod mode to Render. Use a prod database in Render


## 📁 Project Structure

### Backend Structure

The actual implemented structure for the steel thread:

```text
bank-statements-api/
├── app/
│   ├── api/                  # FastAPI routers
│   │   ├── schemas.py        # Pydantic schemas
│   │   └── transactions.py   # Transaction endpoints
│   ├── core/                 # Core settings and startup logic
│   │   ├── config.py         # Configuration settings
│   │   └── database.py       # Database connection
│   ├── domain/               # Domain models
│   │   └── models/
│   │       └── transaction.py # Transaction model
│   ├── ports/                # Repository interfaces
│   │   └── repositories/
│   │       └── transaction.py # Transaction repository interface
│   ├── adapters/             # Repository implementations
│   │   └── repositories/
│   │       └── transaction.py # Transaction repository implementation
│   ├── services/             # Application services
│   │   └── transaction.py    # Transaction service
│   ├── db_init.py            # Database initialization
│   └── main.py               # FastAPI app instance
├── run.py                    # Script to run the application
├── pyproject.toml            # Dependencies
└── .env                      # Environment variables
```

### Frontend Structure

The actual implemented structure for the steel thread:

```text
bank-statements-web/
├── src/
│   ├── components/           # UI components
│   │   ├── TransactionForm.tsx # Form to add transactions
│   │   └── TransactionTable.tsx # Table to display transactions
│   ├── pages/                # Page components
│   │   └── Transactions.tsx  # Main transactions page
│   ├── services/             # API clients and hooks
│   │   ├── api/
│   │   │   └── transactions.ts # API client for transactions
│   │   └── hooks/
│   │       └── useTransactions.ts # Hook for transaction operations
│   ├── types/                # TypeScript types
│   │   └── Transaction.ts    # Transaction type definitions
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Entry point
│   ├── App.css               # Component styles
│   └── index.css             # Global styles
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── tsconfig.node.json        # TypeScript configuration for Node
└── package.json              # Dependencies
```

## Design Patterns

- **Hexagonal Architecture (Ports and Adapters)**: Clear separation between the core domain logic (services) and external interfaces (API, DB).
- **Service Layer**: Encapsulates business logic.
- **Repository Pattern**: Abstracts database operations to keep business logic decoupled from persistence concerns.
- **Dependency Injection**: Services and repositories are injected where needed.
- **React Hooks**: Custom hooks encapsulate business logic and state management.
- **API Client Layer**: Abstracts HTTP details from components.

## Data Flow

### Current Implementation (Steel Thread)

1. **User Adds Transaction**:
   - User fills out the transaction form in the frontend.
   - Frontend sends the transaction data to the backend API.
   - Backend validates and stores the transaction in the database.
   - Frontend refreshes the transaction list.

2. **User Views Transactions**:
   - Frontend fetches transactions from the backend API.
   - Backend retrieves transactions from the database.
   - Frontend displays transactions in a table.

### Planned Implementation

1. **User Uploads File**: File is sent from the frontend to the FastAPI backend.
2. **File Processing**:
   - Backend validates and stores the file temporarily.
   - Appropriate parser (CSV, Excel) extracts transaction data.
   - Transactions are normalized and saved to the database.
3. **User Interaction**:
   - Frontend fetches parsed transactions and displays them in a table.
   - User categorizes or edits transactions.
4. **Export**:
   - User can export data as CSV or JSON via an API call.
   - Backend generates and returns the export file.

## Critical Paths

- **Transaction Management**: Adding, viewing, updating, and deleting transactions.
- **File Upload and Parsing**: (Planned) Handling various formats and accurately extracting data.
- **Data Persistence**: Correctly storing and indexing transaction data for retrieval and categorization.
- **Categorization Flow**: (Planned) Providing a clean and intuitive way for users to review and categorize transactions.
- **Export Functionality**: (Planned) Reliable conversion of structured data into downloadable formats.
- **Testing and CI/CD**: (Planned) Ensure stability and confidence in changes through automated pipelines.
