# Product Context

## Problem Statement

Home users often struggle to manage their finances effectively, leading to overspending and financial stress. They need a solution that helps them understand their spending habits and make informed decisions about their finances.

## Target Users

- Home users who want to take control of their finances
- People who regularly receive bank statements and want to analyze their spending patterns
- Users who want to categorize and track their expenses without manual data entry

## User Needs

- Easy upload and parsing of bank statements in various formats
- Automatic extraction of transaction data (date, description, amount)
- Ability to view and manage transactions in a clean, intuitive interface
- Categorization of transactions to understand spending patterns
- Visualization of spending by category and over time
- Export of categorized data for further analysis

## Key Features

- Automatic categorization of transactions
- Automatic column detection on uploaded bank statements
- Transaction management (add, view, update, delete)
- Data visualization and reporting
- Export functionality

## Current Implementation (Steel Thread)

The current steel thread implementation provides:

- A database schema for storing transactions
- A backend API for adding and listing transactions
- A frontend interface for viewing and adding transactions manually

This minimal implementation demonstrates the core functionality and architecture of the system, providing a foundation for future development.

## User Journey

### Current Steel Thread Journey

1. User accesses the application
2. User can view existing transactions in a table
3. User can add new transactions manually through a form

### Planned Full Journey

1. Users upload their bank statements
2. The application processes the statements and extracts transaction data
3. The application automatically categorizes transactions
4. Users can view, edit, and recategorize transactions as needed
5. Users can visualize their spending patterns through charts and reports
6. Users can export their categorized data for further analysis
