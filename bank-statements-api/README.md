# Bank Statement Analyzer API

Backend API for the Bank Statement Analyzer application.

## Features

- Transaction management (create, read, update, delete)
- RESTful API with FastAPI
- PostgreSQL database
- Hexagonal Architecture (Ports and Adapters)

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

## Project Structure

The project follows Hexagonal Architecture (Ports and Adapters):

- `app/domain/models/`: Domain models
- `app/ports/repositories/`: Repository interfaces (ports)
- `app/adapters/repositories/`: Repository implementations (adapters)
- `app/services/`: Application services (business logic)
- `app/api/`: API endpoints and schemas
- `app/core/`: Core configuration and utilities
