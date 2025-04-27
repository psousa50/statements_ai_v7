
# System Patterns

## Architecture

The application follows a service-oriented architecture, composed of a React frontend, a FastAPI backend, and a PostgreSQL database. The backend is responsible for receiving file uploads, parsing bank statements (CSV, Excel), and storing transaction data. The frontend communicates with the backend over RESTful APIs, allowing users to interact with their uploaded and processed data.

### Backend

Please structure the code using Hexagonal Architecture (Ports and Adapters):

- The router/controller should depend only on an application service, not on infrastructure details.
- The application service should implement the business logic and use ports (interfaces) to interact with external systems like databases or message brokers.
- The actual infrastructure code (e.g., database repositories) should be implemented as adapters and injected via ports.
- The domain logic should be isolated, testable, and independent of frameworks and infrastructure.
- Follow separation of concerns across all layers.
- No database access or business logic in route handlers.
- Favor dependency injection and clean, idiomatic code.

### Frontend

Please follow a modular and production-ready architecture for the frontend:

- No direct HTTP calls inside components (e.g. no fetch or axios inside useEffect)
- Use a typed API client layer (e.g. built with axios or fetch) that wraps all HTTP requests
- The API client should be injected via context, using something like a React Provider, hoist-non-react-statics, or hoax
- Pages and components should depend only on a clean interface to the API (e.g. BankStatementApi.getList()), not on HTTP details
- The client should be mockable and testable, to enable UI tests without needing a real backend
- Use hooks to expose business operations (e.g. useBankStatements) and keep components clean
- Maintain separation between presentation, hooks, and data-fetching logic

## Key Components

### Backend (FastAPI)

- File upload API
- Statement parsing (CSV, Excel)
- Transaction storage and retrieval
- Categorization logic (manual, possibly rule-based)
- Export endpoint (CSV or JSON)
- Authentication (JWT or session-based)

### Frontend (React)

- File upload interface (drag-and-drop + file selector)
- Table view for extracted transactions
- UI to categorize/edit/export transactions
- Authentication (if needed)

### Database (PostgreSQL)

- Users
- Uploaded statements
- Transactions
- Categories

### Testing

- **Backend:** pytest
- **Frontend:** vitest (unit), Playwright (e2e)

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

```text
bank-statements-api/
├── app/
│   ├── api/                  # FastAPI routers
│   │   ├── upload.py
│   │   ├── transactions.py
│   │   └── export.py
│   ├── core/                 # Core settings and startup logic
│   │   ├── config.py
│   │   └── security.py
│   ├── db/                   # DB models and session
│   │   ├── base.py
│   │   ├── models/
│   │   └── schemas/
│   ├── services/             # Business logic (parse files, categorize, etc.)
│   ├── tasks/                # Background tasks (optional)
│   ├── utils/                # File parsers (CSV/XLSX)
│   └── main.py               # FastAPI app instance
├── tests/
│   ├── unit/
│   └── integration/
├── alembic/                  # DB migrations
├── pyproject.toml
└── Dockerfile
```

### Frontend Structure

```text
bank-statements-web/
├── public/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/            # API clients
│   ├── types/
│   ├── utils/
│   └── App.tsx
├── tests/
│   ├── unit/
├── vite.config.ts
├── package.json
└── Dockerfile

e2e/
│   └── bank-statements-web/
│       ├── tests/
│       ├── playwright.config.ts
│       └── package.json
```

## Design Patterns

- **Hexagonal Architecture (Ports and Adapters)**: Clear separation between the core domain logic (services) and external interfaces (API, DB, file parsers).
- **Service Layer**: Encapsulates business logic such as categorization and parsing.
- **Repository Pattern**: Abstracts database operations to keep business logic decoupled from persistence concerns.

## Data Flow

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

- **File Upload and Parsing**: Ensures the system can handle various formats and accurately extract data.
- **Data Persistence**: Correctly storing and indexing transaction data for retrieval and categorization.
- **Categorization Flow**: Providing a clean and intuitive way for users to review and categorize transactions.
- **Export Functionality**: Reliable conversion of structured data into downloadable formats.
- **Testing and CI/CD**: Ensure stability and confidence in changes through automated pipelines.
