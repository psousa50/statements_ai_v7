# Bank Statement Analyzer API

Backend API for the Bank Statement Analyzer application.

## Features

- Transaction management (create, read, update, delete)
- Statement processing architecture for parsing bank statements
- Transaction categorization with hierarchical categories
- File upload and analysis
- RESTful API with FastAPI
- PostgreSQL database
- Hexagonal Architecture (Ports and Adapters)
- LLM integration for schema detection

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -e .
   ```
4. Create a PostgreSQL database:
   ```
   createdb bank_statements
   ```
5. Initialize the database:
   ```
   python -m app.db_init
   ```

## Running the API

```
python run.py
```

The API will be available at http://localhost:8000.

## API Documentation

Once the API is running, you can access the Swagger documentation at:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## Key Components

### Statement Processing Architecture

The Statement Processing Architecture consists of several components that work together to process bank statements:

1. **StatementFileTypeDetector**: Detects file types (CSV, XLSX)
2. **StatementParser**: Parses file content into DataFrames
3. **SchemaDetector**: Uses LLM to detect column mappings
4. **TransactionNormalizer**: Normalizes transaction data
5. **StatementAnalyzerService**: Analyzes files and handles deduplication
6. **StatementPersistenceService**: Persists transactions to the database

### Transaction Categorization

The Transaction Categorization system includes:

1. **Category Model**: Hierarchical structure with parent-child relationships
2. **CategoryRepository**: Interface and implementation for category data access
3. **CategoryService**: Business logic for category management
4. **TransactionCategorizer**: Interface for categorizing transactions
5. **TransactionCategorizationService**: Batch processing of uncategorized transactions

### Database Schema

The database schema includes the following tables:

1. **transactions**: Stores transaction data with categorization
2. **categories**: Stores categories with hierarchical structure
3. **uploaded_files**: Stores raw file content
4. **file_analysis_metadata**: Stores analysis results with file hash for deduplication
5. **sources**: Stores information about transaction sources (banks)

## Project Structure

The project follows Hexagonal Architecture (Ports and Adapters):

- `app/domain/models/`: Domain models (Transaction, Category, UploadedFile, FileAnalysisMetadata)
- `app/ports/repositories/`: Repository interfaces (ports)
- `app/ports/categorizers/`: Categorization interfaces
- `app/adapters/repositories/`: Repository implementations (adapters)
- `app/services/`: Application services (business logic)
  - `transaction.py`: Transaction management
  - `category.py`: Category management
  - `transaction_categorization.py`: Transaction categorization
  - `source.py`: Source management
- `app/ai/`: LLM integration for schema detection
- `app/api/`: API endpoints and schemas
- `app/core/`: Core configuration and utilities
