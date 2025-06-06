# API Contracts

This document provides a comprehensive REST API specification for the Bank Statement Analyzer application, covering all endpoints, request/response formats, and authentication logic.

## Base URL

All API endpoints are prefixed with `/api/v1`.

## Authentication

Authentication is not currently implemented but is planned for future releases. When implemented, it will use JWT (JSON Web Tokens) for authentication.

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

HTTP status codes:

- 400: Bad Request - Invalid input
- 401: Unauthorized - Authentication required
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource not found
- 409: Conflict - Resource already exists
- 422: Unprocessable Entity - Validation error
- 500: Internal Server Error - Server-side error

## API Resources

### Transactions

#### Get All Transactions

Retrieves a list of all transactions with optional filtering.

**Endpoint:** `GET /transactions`

**Query Parameters:**

- `category_id` (optional): Filter by category ID
- `status` (optional): Filter by categorization status (UNCATEGORIZED, CATEGORIZED, FAILURE)

**Response:** 200 OK

```json
{
  "transactions": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "date": "2025-05-15",
      "description": "Grocery Store Purchase",
      "amount": -45.67,
      "created_at": "2025-05-15T14:30:00Z",
      "category_id": "123e4567-e89b-12d3-a456-426614174001",
      "category": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "name": "Groceries",
        "parent_id": "123e4567-e89b-12d3-a456-426614174002"
      },
      "source_id": "123e4567-e89b-12d3-a456-426614174003",
      "source": {
        "id": "123e4567-e89b-12d3-a456-426614174003",
        "name": "Bank A"
      },
      "categorization_status": "CATEGORIZED"
    }
  ],
  "total": 1
}
```

#### Get Transaction by ID

Retrieves a specific transaction by its ID.

**Endpoint:** `GET /transactions/{transaction_id}`

**Path Parameters:**

- `transaction_id`: UUID of the transaction

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2025-05-15",
  "description": "Grocery Store Purchase",
  "amount": -45.67,
  "created_at": "2025-05-15T14:30:00Z",
  "category_id": "123e4567-e89b-12d3-a456-426614174001",
  "category": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Groceries",
    "parent_id": "123e4567-e89b-12d3-a456-426614174002"
  },
  "source_id": "123e4567-e89b-12d3-a456-426614174003",
  "source": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "name": "Bank A"
  },
  "categorization_status": "CATEGORIZED"
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Transaction with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### Create Transaction

Creates a new transaction.

**Endpoint:** `POST /transactions`

**Request Body:**

```json
{
  "date": "2025-05-15",
  "description": "Grocery Store Purchase",
  "amount": -45.67,
  "category_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Response:** 201 Created

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2025-05-15",
  "description": "Grocery Store Purchase",
  "amount": -45.67,
  "created_at": "2025-05-15T14:30:00Z",
  "category_id": "123e4567-e89b-12d3-a456-426614174001",
  "category": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Groceries",
    "parent_id": "123e4567-e89b-12d3-a456-426614174002"
  },
  "source_id": null,
  "source": null,
  "categorization_status": "CATEGORIZED"
}
```

#### Update Transaction

Updates an existing transaction.

**Endpoint:** `PUT /transactions/{transaction_id}`

**Path Parameters:**

- `transaction_id`: UUID of the transaction

**Request Body:**

```json
{
  "date": "2025-05-15",
  "description": "Updated Grocery Store Purchase",
  "amount": -50.00,
  "category_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2025-05-15",
  "description": "Updated Grocery Store Purchase",
  "amount": -50.00,
  "created_at": "2025-05-15T14:30:00Z",
  "category_id": "123e4567-e89b-12d3-a456-426614174001",
  "category": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Groceries",
    "parent_id": "123e4567-e89b-12d3-a456-426614174002"
  },
  "source_id": null,
  "source": null,
  "categorization_status": "CATEGORIZED"
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Transaction with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### Delete Transaction

Deletes a transaction.

**Endpoint:** `DELETE /transactions/{transaction_id}`

**Path Parameters:**

- `transaction_id`: UUID of the transaction

**Response:** 204 No Content

**Error Response:** 404 Not Found

```json
{
  "detail": "Transaction with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### Categorize Transaction

Categorizes a transaction.

**Endpoint:** `PUT /transactions/{transaction_id}/categorize`

**Path Parameters:**

- `transaction_id`: UUID of the transaction

**Query Parameters:**

- `category_id` (optional): UUID of the category (if null, removes categorization)

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2025-05-15",
  "description": "Grocery Store Purchase",
  "amount": -45.67,
  "created_at": "2025-05-15T14:30:00Z",
  "category_id": "123e4567-e89b-12d3-a456-426614174001",
  "category": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Groceries",
    "parent_id": "123e4567-e89b-12d3-a456-426614174002"
  },
  "source_id": null,
  "source": null,
  "categorization_status": "CATEGORIZED"
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Transaction with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### Mark Categorization Failure

Marks a transaction as having failed categorization.

**Endpoint:** `PUT /transactions/{transaction_id}/mark-failure`

**Path Parameters:**

- `transaction_id`: UUID of the transaction

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2025-05-15",
  "description": "Grocery Store Purchase",
  "amount": -45.67,
  "created_at": "2025-05-15T14:30:00Z",
  "category_id": null,
  "category": null,
  "source_id": null,
  "source": null,
  "categorization_status": "FAILURE"
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Transaction with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### Categorize Transactions Batch

Categorizes a batch of uncategorized transactions.

**Endpoint:** `POST /transactions/categorize-batch`

**Query Parameters:**

- `batch_size` (optional, default=10): Number of transactions to process (min=1, max=100)

**Response:** 200 OK

```json
{
  "categorized_count": 5,
  "success": true,
  "message": "Successfully categorized 5 transactions"
}
```

### Categories

#### Get All Categories

Retrieves a list of all categories.

**Endpoint:** `GET /categories`

**Response:** 200 OK

```json
{
  "categories": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Groceries",
      "parent_id": "123e4567-e89b-12d3-a456-426614174002"
    }
  ],
  "total": 1
}
```

#### Get Root Categories

Retrieves a list of all root categories (categories without a parent).

**Endpoint:** `GET /categories/root`

**Response:** 200 OK

```json
{
  "categories": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "Expenses",
      "parent_id": null
    }
  ],
  "total": 1
}
```

#### Get Category by ID

Retrieves a specific category by its ID.

**Endpoint:** `GET /categories/{category_id}`

**Path Parameters:**

- `category_id`: UUID of the category

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Groceries",
  "parent_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Category with ID 123e4567-e89b-12d3-a456-426614174001 not found"
}
```

#### Get Subcategories

Retrieves all subcategories for a given parent category.

**Endpoint:** `GET /categories/{category_id}/subcategories`

**Path Parameters:**

- `category_id`: UUID of the parent category

**Response:** 200 OK

```json
{
  "categories": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Groceries",
      "parent_id": "123e4567-e89b-12d3-a456-426614174002"
    }
  ],
  "total": 1
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Category with ID 123e4567-e89b-12d3-a456-426614174002 not found"
}
```

#### Create Category

Creates a new category.

**Endpoint:** `POST /categories`

**Request Body:**

```json
{
  "name": "Groceries",
  "parent_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Response:** 201 Created

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Groceries",
  "parent_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Error Response:** 400 Bad Request

```json
{
  "detail": "Parent category with ID 123e4567-e89b-12d3-a456-426614174002 not found"
}
```

#### Update Category

Updates an existing category.

**Endpoint:** `PUT /categories/{category_id}`

**Path Parameters:**

- `category_id`: UUID of the category

**Request Body:**

```json
{
  "name": "Food & Groceries",
  "parent_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Food & Groceries",
  "parent_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Error Responses:**

- 404 Not Found

```json
{
  "detail": "Category with ID 123e4567-e89b-12d3-a456-426614174001 not found"
}
```

- 400 Bad Request

```json
{
  "detail": "Cannot set a category as its own ancestor"
}
```

#### Delete Category

Deletes a category.

**Endpoint:** `DELETE /categories/{category_id}`

**Path Parameters:**

- `category_id`: UUID of the category

**Response:** 204 No Content

**Error Responses:**

- 404 Not Found

```json
{
  "detail": "Category with ID 123e4567-e89b-12d3-a456-426614174001 not found"
}
```

- 400 Bad Request

```json
{
  "detail": "Cannot delete category with associated transactions or subcategories"
}
```

### Sources

#### Get All Sources

Retrieves a list of all sources.

**Endpoint:** `GET /sources`

**Response:** 200 OK

```json
{
  "sources": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "name": "Bank A"
    }
  ],
  "total": 1
}
```

#### Get Source by ID

Retrieves a specific source by its ID.

**Endpoint:** `GET /sources/{source_id}`

**Path Parameters:**

- `source_id`: UUID of the source

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "Bank A"
}
```

**Error Response:** 404 Not Found

```json
{
  "detail": "Source with ID 123e4567-e89b-12d3-a456-426614174003 not found"
}
```

#### Create Source

Creates a new source.

**Endpoint:** `POST /sources`

**Request Body:**

```json
{
  "name": "Bank A"
}
```

**Response:** 201 Created

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "Bank A"
}
```

**Error Response:** 409 Conflict

```json
{
  "detail": "Source with name 'Bank A' already exists"
}
```

#### Update Source

Updates an existing source.

**Endpoint:** `PUT /sources/{source_id}`

**Path Parameters:**

- `source_id`: UUID of the source

**Request Body:**

```json
{
  "name": "Bank A - Checking"
}
```

**Response:** 200 OK

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "Bank A - Checking"
}
```

**Error Responses:**

- 404 Not Found

```json
{
  "detail": "Source with ID 123e4567-e89b-12d3-a456-426614174003 not found"
}
```

- 409 Conflict

```json
{
  "detail": "Source with name 'Bank A - Checking' already exists"
}
```

#### Delete Source

Deletes a source.

**Endpoint:** `DELETE /sources/{source_id}`

**Path Parameters:**

- `source_id`: UUID of the source

**Response:** 204 No Content

**Error Response:** 404 Not Found

```json
{
  "detail": "Source with ID 123e4567-e89b-12d3-a456-426614174003 not found"
}
```

### Statements

#### Analyze Statement

Analyzes a bank statement file to detect its structure.

**Endpoint:** `POST /statements/analyze`

**Request Body:** `multipart/form-data`

- `file`: The bank statement file (CSV or XLSX)

**Response:** 200 OK

```json
{
  "uploaded_file_id": "123e4567-e89b-12d3-a456-426614174004",
  "file_type": "csv",
  "column_mapping": {
    "date": "Transaction Date",
    "description": "Description",
    "amount": "Amount"
  },
  "header_row_index": 0,
  "data_start_row_index": 1,
  "preview_data": [
    {
      "Transaction Date": "2025-05-15",
      "Description": "Grocery Store Purchase",
      "Amount": "-45.67"
    }
  ],
  "is_duplicate": false
}
```

**Error Response:** 400 Bad Request

```json
{
  "detail": "Error analyzing file: Unsupported file format"
}
```

#### Upload Statement

Uploads a bank statement for processing and persistence.

**Endpoint:** `POST /statements/upload`

**Request Body:**

```json
{
  "source_id": "123e4567-e89b-12d3-a456-426614174003",
  "uploaded_file_id": "123e4567-e89b-12d3-a456-426614174004",
  "column_mapping": {
    "date": "Transaction Date",
    "description": "Description",
    "amount": "Amount"
  },
  "header_row_index": 0,
  "data_start_row_index": 1
}
```

**Response:** 200 OK

```json
{
  "uploaded_file_id": "123e4567-e89b-12d3-a456-426614174004",
  "transactions_saved": 10,
  "success": true,
  "message": "Successfully saved 10 transactions"
}
```

**Error Response:** 400 Bad Request

```json
{
  "detail": "Error processing statement: Invalid column mapping"
}
```
