# Active Context

## Current Focus

The current focus is on implementing a steel thread for the Bank Statement Analyzer project. The steel thread is a minimal implementation of the system that demonstrates the core functionality from end to end, including:

1. A PostgreSQL database with a table for transactions
2. A FastAPI backend API to add and list transactions
3. A React frontend to display transactions

This steel thread follows the architectural patterns and principles that will be used in the final product, particularly the Hexagonal Architecture (Ports and Adapters) pattern for the backend.

## Recent Changes

- Created the initial project structure for both backend and frontend
- Implemented the backend API with FastAPI following Hexagonal Architecture
- Implemented the frontend with React, TypeScript, and Vite
- Set up the database schema for transactions
- Implemented end-to-end testing with Playwright for the TransactionPage

## Next Steps

- Implement file upload and parsing functionality
- Add transaction categorization
- Implement data visualization
- Add user authentication
- Add export functionality
- Expand end-to-end testing coverage with additional Playwright tests

## Decisions

- Using Hexagonal Architecture (Ports and Adapters) for the backend to ensure clear separation of concerns and testability
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
- The steel thread approach allows us to validate the architecture and design patterns early in the development process
- A comprehensive CI/CD pipeline ensures consistent and reliable deployments
- Using different environments (test, dev, prod) allows for proper testing before production deployment
- End-to-end testing with Playwright provides confidence in the application's functionality from a user's perspective
- Using the API for test data setup and teardown makes end-to-end tests more reliable and faster than UI-only tests
