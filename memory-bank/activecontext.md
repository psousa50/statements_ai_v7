# Active Context

## Current Focus

The current focus is on enhancing the Bank Statement Analyzer project with transaction categorization and file upload capabilities. The system now enables:

1. Accept file uploads (CSV, XLSX) through an intuitive UI interface
2. Parse and normalize data into a standard schema
3. Categorize and persist transactions both automatically and manually
4. Avoid redundant processing of similar files via hashing
5. Organize transactions with a hierarchical category system

We have implemented these features following a bottom-up approach and Test-Driven Development (TDD) principles.

## Recent Changes

- Implemented transaction categorization system
  - Created Category domain model with hierarchical structure (parent-child relationships)
  - Implemented CategoryRepository interface and implementation
  - Created CategoryService for managing categories (CRUD operations)
  - Implemented TransactionCategorizer interface for categorizing transactions
  - Created TransactionCategorizationService for batch processing of uncategorized transactions
  - Added API endpoint for triggering batch categorization
  - Added database migration for the categories table
  - Created comprehensive tests for all categorization components

- Implemented file upload UI in the frontend
  - Created Upload page with multi-step workflow
  - Implemented FileUploadZone component with drag-and-drop functionality
  - Added ColumnMappingTable for customizing column mappings
  - Created SourceSelector for selecting the bank/source of statements
  - Added validation messages to guide users through the upload process
  - Implemented AnalysisSummary to show file analysis results
  - Created UploadFooter with finalize and cancel actions
  - Added navigation to transactions page after successful upload

- Implemented separation of UploadedFile and FileAnalysisMetadata tables
  - Created new domain models for UploadedFile (raw file content) and FileAnalysisMetadata (analysis data)
  - Implemented repository interfaces and implementations for both models
  - Updated StatementAnalyzerService to save only to UploadedFile table and check FileAnalysisMetadata by hash
  - Updated StatementPersistenceService to retrieve file content from UploadedFile and save metadata to FileAnalysisMetadata
  - Added database migration for the new tables
  - Updated dependency injection configuration
  - Fixed all tests to work with the new architecture
  - Updated datetime handling to use timezone-aware methods (datetime.now(timezone.utc)) instead of deprecated datetime.utcnow()
  - Ensured all tests pass without warnings, confirming the implementation works as expected

- Implemented the Statement Processing Architecture with the following components:
  - StatementFileTypeDetector - Detects file types (CSV, XLSX)
  - StatementParser - Parses file content into DataFrames
  - SchemaDetector - Uses LLM to detect column mappings
  - TransactionNormalizer - Normalizes transaction data
  - StatementAnalyzerService - Analyzes files and handles deduplication
  - StatementPersistenceService - Persists transactions to the database
- Created comprehensive test coverage for all components
- Followed project guidelines with no comments/docstrings and clear naming

## Next Steps

- Implement data visualization (charts and reports)
- Add user authentication
- Add export functionality
- Implement automatic categorization using machine learning
- Add transaction search and filtering
- Create dashboard with financial insights
- Expand end-to-end testing coverage with additional Playwright tests

## Decisions

- Using Hexagonal Architecture (Ports and Adapters) for the backend to ensure clear separation of concerns and testability
- Using TDD for all new features, writing tests before implementation
- Using dependency injection for testability and maintainability
- Using an LLM-based approach for schema detection to handle various bank statement formats
- Using file hashing for deduplication to avoid processing the same file multiple times
- Using React hooks for business logic in the frontend to keep components clean
- Using a typed API client layer to abstract HTTP details from components
- Using PostgreSQL for persistent storage with SQLAlchemy as the ORM
- Using GitHub Actions for CI/CD pipeline
- Using Docker for containerization
- Using Fly.io for test and dev environments
- Using Render for production environment
- Using Neon for database hosting in test and dev environments

## Insights

- The Hexagonal Architecture provides a clean way to separate business logic from infrastructure concerns
- Using repository interfaces (ports) and implementations (adapters) makes the code more testable and maintainable
- TDD ensures high-quality code with comprehensive test coverage
- The bottom-up approach to implementing complex architectures ensures solid foundations
- Using an LLM for schema detection provides flexibility to handle various bank statement formats
- File hashing for deduplication improves system efficiency
- The steel thread approach allows us to validate the architecture and design patterns early in the development process
- A comprehensive CI/CD pipeline ensures consistent and reliable deployments
- Using different environments (test, dev, prod) allows for proper testing before production deployment
- End-to-end testing with Playwright provides confidence in the application's functionality from a user's perspective
- Using the API for test data setup and teardown makes end-to-end tests more reliable and faster than UI-only tests
- A multi-step workflow for file uploads with clear validation messages improves user experience
- Separating file storage from analysis metadata improves system architecture and performance
- Batch processing for transaction categorization allows for efficient handling of large datasets
- A hierarchical category system provides flexibility for detailed financial analysis
- The combination of automatic and manual categorization gives users the best of both worlds
