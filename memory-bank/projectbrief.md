
# Project Brief

## Project Name

Bank Statement Analyzer

## Project Description

A web application that allows users to upload bank statements in various formats (CSV, Excel). The system parses the files, extracts transaction data (date, description, amount), and stores it in a structured format for users to review, categorize, and export.

## Goals

- Allow users to upload bank statements in multiple formats.
- Accurately extract and store transaction data.
- Provide a clean UI for reviewing and categorizing transactions.
- Enable export of categorized data.
- Ensure reliability and scalability of the system.

## Scope

- **Included**:
  - Frontend built with React and Vite
  - Backend built with FastAPI
  - PostgreSQL for persistent storage
  - File parsing for CSV, Excel
  - Transaction categorization
  - Testing using Vitest, Playwright, and pytest
  - Deployment using Render and CI/CD via GitHub Actions

- **Excluded**:
  - Advanced ML-based categorization
  - Multi-currency or exchange rate handling
  - Direct bank integration (e.g., Plaid, Yodlee)

## Stakeholders

- **Product Owner** – Defines requirements and prioritizes features.
- **Developer(s)** – Build and maintain the system.
- **End Users** – Upload, view, categorize, and export transactions.
- **Operations/DevOps** – Manage deployment and infrastructure (Render, CI/CD).

## Success Criteria

- Users can successfully upload and parse at least 95% of valid statement files.
- Transactions are stored correctly and presented clearly in the UI.
- Categorization and export features function as expected.
- System remains responsive under normal usage.
- Automated tests pass consistently in CI pipeline.
