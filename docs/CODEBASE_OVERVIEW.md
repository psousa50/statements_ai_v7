# Codebase Overview - Bank Statement Analyzer

## 1. Overall Architecture

This is a **full-stack web application** for personal finance management, specifically designed to upload, parse, categorize, and analyze bank statements. The architecture follows a **modern three-tier design**:

- **Frontend**: React with TypeScript (Single Page Application)
- **Backend**: FastAPI with Python (RESTful API)
- **Database**: PostgreSQL 15 (Relational data store)

The application follows **Hexagonal Architecture** (Ports and Adapters) on the backend, providing clear separation between domain logic, application services, and infrastructure concerns.

## 2. Technology Stack

### Backend (Python/FastAPI)
- **Core Framework**: FastAPI 0.95+ with Uvicorn ASGI server
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0+ ORM
- **Migrations**: Alembic for database schema versioning
- **Data Processing**: pandas for CSV/Excel parsing, openpyxl for Excel files
- **AI Integration**: Google Gemini AI for schema detection and categorization
- **Validation**: Pydantic 2.7+ for data validation and settings
- **Testing**: pytest with pytest-cov (90%+ coverage target)
- **Code Quality**: ruff (linting), black (formatting), isort (import sorting)
- **Package Manager**: uv (modern Python package manager)

**Key Statistics**:
- 167 Python files across ~8,893 lines of code
- Uses modern Python 3.9+ features
- Type hints throughout for type safety

### Frontend (React/TypeScript)
- **Framework**: React 18.2 with TypeScript 4.9+
- **Build Tool**: Vite 6.3+ (fast development and builds)
- **UI Components**: Material-UI (MUI) 7.1+ and RSuite 5.82+
- **Routing**: React Router v7.6
- **HTTP Client**: Axios 1.3+
- **Charts**: Recharts 2.15+ for data visualization
- **Date Handling**: date-fns 3.6+
- **File Upload**: react-dropzone for drag-and-drop
- **Testing**: Vitest with Testing Library (85%+ coverage target)
- **Package Manager**: pnpm 10.10+

**Key Statistics**:
- 63 TypeScript/TSX files
- Component-based architecture with hooks
- No global state management library (uses React hooks and context)

### Infrastructure
- **Containerization**: Docker with docker-compose
- **CI/CD**: GitHub Actions (5 workflow files)
- **Development DB**: PostgreSQL on port 54321 (production), 15432 (test)
- **API Port**: 8010 (configurable)
- **Web Port**: 6173 (configurable)

## 3. Directory Structure

```
statements_ai_v7/
├── bank-statements-api/          # Backend FastAPI application
│   ├── app/
│   │   ├── adapters/             # Repository implementations (SQLAlchemy)
│   │   ├── ai/                   # LLM integration (Gemini AI)
│   │   ├── api/                  # HTTP routes and schemas
│   │   ├── common/               # Shared utilities (text normalization)
│   │   ├── core/                 # Config, database, dependencies
│   │   ├── domain/               # Domain models and DTOs
│   │   ├── ports/                # Repository interfaces
│   │   ├── services/             # Business logic services
│   │   ├── logging/              # Logging configuration
│   │   └── workers/              # Background job processing
│   ├── migrations/               # Alembic database migrations (11 files)
│   ├── tests/                    # Unit, integration, and API tests
│   └── scripts/                  # Utility scripts
│
├── bank-statements-web/          # Frontend React application
│   ├── src/
│   │   ├── api/                  # API clients and context providers
│   │   ├── components/           # Reusable UI components (27 files)
│   │   │   ├── layout/          # App layout components
│   │   │   └── upload/          # File upload workflow components
│   │   ├── pages/                # Page components (17 files)
│   │   ├── services/             # React hooks for data fetching
│   │   └── types/                # TypeScript type definitions
│   └── tests/                    # Frontend tests
│
├── config/                       # Centralized configuration YAML
├── docs/                         # Extensive documentation
│   ├── architecture/            # C4 diagrams and sequence diagrams
│   ├── features/                # Feature specifications and user stories
│   ├── guides/                  # Development guidelines
│   └── project-management/      # User stories and done items
│
├── e2e/                          # Playwright end-to-end tests
├── scripts/                      # Build and deployment scripts
├── .github/workflows/            # CI/CD pipeline definitions
└── docker-compose.yml            # Container orchestration
```

## 4. Backend Structure

### Domain Models (SQLAlchemy ORM)

**Core Entities**:

1. **Transaction** (`bank-statements-api/app/domain/transaction.py`)
   - Financial transactions with:
     - Basic fields: date, description, amount, normalized_description
     - Status tracking: categorization_status, counterparty_status
     - Ordering: row_index, sort_index
     - Source tracking: source_type (UPLOAD/MANUAL)
     - Relationships: category, account, counterparty_account, statement

2. **Category** (`bank-statements-api/app/domain/category.py`)
   - Hierarchical categorization system
   - Self-referential parent-child relationships
   - Used for organizing spending patterns

3. **Account** (`bank-statements-api/app/domain/account.py`)
   - Bank accounts
   - Tracks transactions as primary or counterparty
   - Has associated statements and initial balances

4. **Statement** (`bank-statements-api/app/domain/statement.py`)
   - Uploaded bank statement files
   - Stores original file content and metadata
   - Links to transactions and account
   - Tracks transaction counts and date ranges

5. **EnhancementRule** (`bank-statements-api/app/domain/enhancement_rule.py`)
   - Rule-based transaction enhancement
   - Pattern matching (EXACT, PREFIX, INFIX)
   - Optional constraints (amount, date ranges)
   - Auto-applies category and counterparty assignments
   - Source tracking (MANUAL/AI)

6. **UploadedFile** & **FileAnalysisMetadata**
   - Stores raw uploads
   - Caches analysis results for duplicate detection
   - Stores column mappings and row filters

7. **BackgroundJob**
   - Async job management
   - Tracks job status and progress
   - Supports retry logic

8. **InitialBalance**
   - Starting balances for accounts

### API Routes

**Main Endpoints**:

1. **Transactions** (`/transactions`)
   - GET: Paginated list with extensive filtering
   - POST: Create manual transaction with auto-enhancement
   - PUT: Update transaction
   - DELETE: Remove transaction
   - POST `/categorize`: Manual categorization
   - GET `/category-totals`: Aggregated spending data
   - POST `/bulk-update`: Batch categorization by description
   - POST `/preview-enhancement`: Preview rule matching

2. **Statements** (`/statements`)
   - POST `/analyze`: Analyze uploaded file (schema detection)
   - POST `/upload`: Process and import transactions
   - GET: List uploaded statements

3. **Categories** (`/categories`)
   - CRUD operations for hierarchical categories

4. **Accounts** (`/accounts`)
   - CRUD operations for bank accounts

5. **Enhancement Rules** (`/enhancement-rules`)
   - CRUD operations for categorization rules
   - GET `/matching-transactions`: Preview rule impact

### Business Logic Services

**Key Services** (`bank-statements-api/app/services/`):

1. **TransactionService**
   - Core transaction operations
   - Pagination with complex filtering
   - Running balance calculations
   - Auto-enhancement on creation
   - Category totals for charts

2. **StatementUploadService**
   - 4-step upload process
   - Parse statement file
   - Enhance transactions with rules
   - Save to database
   - Schedule background jobs

3. **StatementAnalyzerService**
   - File analysis
   - File type detection (CSV/XLSX)
   - Schema detection (heuristic or LLM-based)
   - Column mapping inference
   - Duplicate detection via file hashing
   - Row filtering suggestions

4. **TransactionEnhancer**
   - Pure rule application
   - Stateless rule matching
   - Precedence-based application (exact > prefix > infix)
   - First-match-wins strategy

5. **EnhancementRuleManagementService**
   - Rule CRUD with validation
   - Transaction matching queries

6. **CategoryService**
   - Hierarchical category management

7. **AccountService**
   - Account operations

8. **BackgroundJobService**
   - Async job orchestration

### Statement Processing Pipeline

The statement upload workflow:

```
1. FileUploadZone (Frontend) → 2. /analyze endpoint
   ↓
3. File Type Detection → 4. Schema Detection (Heuristic/LLM)
   ↓
5. Column Mapping UI → 6. Row Filters UI
   ↓
7. /upload endpoint → 8. Parse + Normalize
   ↓
9. Apply Enhancement Rules → 10. Save to DB
   ↓
11. Schedule Background Jobs (AI processing)
```

### Dependency Injection Pattern

The backend uses a sophisticated DI system (`bank-statements-api/app/core/dependencies.py`):
- **ExternalDependencies**: Database session, LLM client
- **InternalDependencies**: All application services and repositories
- Context manager pattern for proper cleanup
- FastAPI integration via `Depends()`

### Authentication/Authorization

**Current State**: No authentication implemented (planned for future)
- All endpoints are currently public
- Multi-tenancy not yet implemented
- Marked in PRD as "Excluded from MVP"

## 5. Frontend Structure

### Component Organization

**Pages** (Route-level components in `bank-statements-web/src/pages/`):
- **TransactionsPage** - Main transaction list with filters and pagination
- **TransactionCategorizationsPage** - Batch categorization interface
- **EnhancementRules** - Rule management interface
- **CategoriesPage** - Category hierarchy editor
- **AccountsPage** - Account management
- **ChartsPage** - Data visualization with charts
- **Statements** - Statement list and management
- **Upload** - Multi-step file upload workflow

**Reusable Components** (`bank-statements-web/src/components/`):
- **TransactionTable** - Sortable, filterable transaction grid
- **TransactionFilters** - Complex filtering UI with debouncing
- **TransactionModal** - Create/edit transaction form
- **CategorySelector** - Hierarchical category picker
- **EnhancementRuleTable** - Rule list with actions
- **EnhancementRuleModal** - Rule creation/editing
- **Pagination** - Reusable pagination controls
- **Toast** - Notification system

**Upload Workflow Components** (8 specialized components):
- **FileUploadZone** - Drag-and-drop file selector
- **ColumnMappingTable** - Map file columns to fields
- **AccountSelector** - Choose target account
- **RowFilterPanel** - Define row exclusion rules
- **FilterConditionRow** - Individual filter condition
- **AnalysisSummary** - File analysis preview
- **ValidationMessages** - Error/warning display
- **UploadFooter** - Step navigation

### State Management

**No global state library** - uses:
- React hooks (`useState`, `useEffect`, `useCallback`)
- Custom hooks for data fetching (`useTransactions`, `useCategories`, `useAccounts`)
- Context API for API clients (`ApiContext`, `RouterSafeApiProvider`)
- URL search params for filter persistence

### API Client Layer

Well-structured API abstraction (`bank-statements-web/src/api/`):
- **Separate clients per domain**: TransactionClient, CategoryClient, AccountClient, StatementClient, EnhancementRuleClient
- **Type-safe interfaces** defined in TypeScript
- **Centralised error handling**
- **Environment-aware base URL** (`VITE_API_URL`)

### Routing Structure

React Router v7 with nested routes:
```
/ (AppLayout)
├── /transactions (default)
├── /categorizations
├── /enhancement-rules
├── /categories
├── /accounts
├── /charts
├── /statements
└── /upload
```

## 6. Key Features

### 1. Statement Upload & Processing
- Drag-and-drop file upload (CSV, XLSX)
- Automatic schema detection using heuristics or LLM
- Flexible column mapping customisation
- Row filtering to exclude header/footer rows
- Duplicate detection via file hash comparison
- Transaction normalisation with pandas
- Date range and summary statistics

### 2. Transaction Management
- Comprehensive CRUD operations
- Manual transaction creation with auto-enhancement
- Smart ordering (row_index and sort_index)
- Running balance calculation per account
- Multi-field filtering: date range, amount, description, category, status, account
- Sorting by multiple fields
- Pagination with configurable page sizes
- Search with case-insensitive description matching

### 3. Rule-Based Enhancement System
- Pattern matching with three types:
  - EXACT: Full description match
  - PREFIX: Starts with pattern
  - INFIX: Contains pattern
- Optional constraints: amount ranges, date ranges
- Auto-assignment: category and counterparty account
- Preview mode: See rule impact before applying
- Manual and AI-generated rules
- Rule precedence (exact > prefix > infix)
- Bulk updates for existing transactions

### 4. Categorisation System
- Hierarchical categories (parent-child)
- Multiple categorisation sources:
  - UNCATEGORIZED: Not yet processed
  - RULE_BASED: Auto-assigned by rules
  - MANUAL: User-assigned
  - FAILURE: Categorisation failed
- Batch categorisation interface
- Category totals for spending analysis

### 5. Account Management
- Multiple accounts support
- Transfer tracking (counterparty_account)
- Initial balances for accurate running totals
- Account-specific filtering

### 6. Data Visualization
- Charts page with Recharts
- Category-based spending breakdown
- Trend analysis over time
- Filtered chart data matching transaction filters

### 7. Background Job System
- Async processing for long-running tasks
- Job status tracking (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- Progress reporting
- Retry logic for failed jobs
- Immediate processing option for better UX

## 7. Testing Approach

### Backend Tests (`bank-statements-api/tests/`)

**Test Structure**:
- **Unit Tests** (`tests/unit/`):
  - Domain model tests
  - Service logic tests (pure functions)
  - Schema detection tests
  - Text normalisation tests
  - Transaction enhancement tests
  - Statement processing tests

- **Integration Tests** (`tests/integration/`):
  - Repository tests with real PostgreSQL
  - Database interaction tests

- **API Tests** (`tests/api/`):
  - Endpoint integration tests
  - Request/response validation

**Test Database**:
- Separate test PostgreSQL on port 15432
- Real database (no sqlite/in-memory)
- Migrations run before tests

**Coverage Target**: 90%+ for backend

### Frontend Tests (`bank-statements-web/tests/`)

- Unit tests with Vitest
- Component tests with Testing Library
- Coverage target: 85%+

### E2E Tests (`e2e/`)

- Playwright for end-to-end testing
- Tests critical user journeys
- Currently no tests (noted in CLAUDE.md)

## 8. Configuration & Infrastructure

### Centralised Configuration
- YAML-based settings (`config/settings.yaml`)
- Environment file generation via scripts
- Port configuration: API (8010), Web (6173), DB (54321)
- Environment variables for secrets (GOOGLE_API_KEY)

### Database Management
- Alembic migrations (11 migration files)
- Backup/restore scripts via pnpm
- Development and test databases
- Docker Compose for local development

### CI/CD Pipeline (GitHub Actions)

**5 Workflow Files**:
1. **1.ci.yml** - Continuous integration (tests, linting)
2. **1.deploy-test.yml** - Deploy to test environment
3. **2.e2e-tests.yml** - Run Playwright tests
4. **3.deploy-dev.yml** - Deploy to development
5. **4.deploy-prod.yml** - Production deployment

**Deployment Platforms**:
- Development/Test: Fly.io
- Production: Render
- Database: Neon (dev/test), Render PostgreSQL (prod)

### Development Workflow
- Hot reloading enabled for both frontend and backend
- Development status: Both services running (ports 8010, 6173)
- Code quality tools: ESLint, Prettier (frontend), ruff, black, isort (backend)

## 9. Notable Patterns & Design Decisions

### 1. Hexagonal Architecture (Backend)
- Clear separation: Domain → Ports → Adapters → Services → API
- Repository pattern for data access abstraction
- Dependency injection for testability
- Pure service layer for business logic

### 2. Schema-First Development
- Pydantic schemas define API contracts
- TypeScript types derived from API
- Shared understanding between frontend and backend

### 3. Text Normalisation Strategy
- All transaction descriptions are normalised
- Stored in `normalized_description` field
- Used for rule matching and deduplication
- Case-insensitive, whitespace-normalised

### 4. Transaction Ordering System
Two-tier ordering:
- **row_index**: Original position in file
- **sort_index**: User-controllable order
- Enables manual transaction insertion at specific positions

### 5. File Hash Caching
- SHA-256 hash of file type + dataframe shape
- Stores column mappings and row filters
- Enables "smart" re-upload of same file
- Prevents duplicate imports

### 6. Debounced Search
- Local state for input fields
- Debounced updates to filter state
- Prevents excessive API calls

### 7. URL-Based Filter Persistence
- Filters stored in URL search params
- Enables bookmarkable filtered views
- Shareable links to specific transaction views

### 8. Enhancement Rule Preview
- Preview mode shows what rules would match
- Helps users understand rule impact before saving
- Counts affected transactions

### 9. Running Balance Calculation
- Calculated on-demand (not stored)
- Requires account-specific filtering
- Uses initial balances as starting point
- Sorted by date and creation time

### 10. Filter Composition
Complex filtering system:
- Multiple filter types composable
- Rule-based filtering overrides others
- Exclude transfers/uncategorised toggles
- Transaction type (all/debit/credit)

## 10. Development Guidelines

From `docs/guides/development-guidelines.md`:

**Core Principles**:
- Test behaviour, not implementation
- Strong typing (no `any` types)
- Immutable data (no mutations)
- Pure functions preferred
- Self-documenting code (no comments)
- BDD scenarios (Given-When-Then)
- Schema-first development
- Named parameters over positional
- Real databases in tests (no in-memory)

**Code Style**:
- Maximum 2 levels of nesting
- Functional methods (map, filter, reduce)
- Factory functions for test data
- Never redefine schemas in tests

## 11. Project Status

### Completed Phases
- Phase 1: Steel thread with basic transactions ✅
- Phase 2: Statement processing architecture ✅
- Phase 3: File upload UI ✅
- Phase 4: Transaction categorisation system ✅

### Recent Features
- Enhancement rule system with preview
- Rule-based categorisation
- Manual transaction creation with auto-enhancement
- Exclude uncategorised filter
- Undo toast for category removal
- Transaction ordering system

### Planned Phases
- Phase 5: Data visualisation (partially complete - Charts page exists)
- Phase 6: User authentication
- Phase 7: Export functionality and advanced features

### Known Issues
- Search is case-sensitive (issue noted in docs)
- Alert dialogue improvements needed
- No E2E tests yet

## Summary

This is a **well-architected, production-ready personal finance application** with:
- Clean separation of concerns (Hexagonal Architecture)
- Strong typing throughout (TypeScript + Pydantic)
- Comprehensive testing strategy
- Sophisticated rule-based transaction enhancement
- Flexible statement upload workflow
- Modern development practices (DI, functional patterns, schema-first)
- Good documentation (architecture diagrams, user stories, guidelines)
- CI/CD pipeline in place

The codebase shows evidence of thoughtful design, with approximately **167 Python files** in the backend and **63 TypeScript files** in the frontend, totalling a substantial but well-organised codebase. The application successfully handles the complex domain of bank statement processing with an elegant combination of rule-based and AI-assisted approaches.
