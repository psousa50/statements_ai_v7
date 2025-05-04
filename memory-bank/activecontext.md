# Active Context

## Current Focus

The current focus is on implementing the Statement Processing Architecture for the Bank Statement Analyzer project. This architecture enables the system to:

1. Accept file uploads (CSV, XLSX)
2. Parse and normalize data into a standard schema
3. Categorize and persist transactions
4. Avoid redundant processing of similar files via hashing

We have implemented the complete architecture following a bottom-up approach and Test-Driven Development (TDD) principles.

## Recent Changes

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

- Integrate the Statement Processing Architecture with the API endpoints
- Implement file upload UI in the frontend
- Add transaction categorization
- Implement data visualization
- Add user authentication
- Add export functionality
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
