# Dependency Injection Pattern in Bank Statements API

This document explains the dependency injection pattern used in the Bank Statements API.

## Overview

The application uses a container-based dependency injection pattern that separates:

1. **External Dependencies**: Components that interact with the outside world (databases, APIs, etc.)
2. **Internal Dependencies**: Business logic components (services, repositories) that depend on external ones

This approach provides several benefits:
- Clear separation of concerns
- Easier testing with mocks
- Support for different configurations (test, dev, prod)
- Clean architecture and maintainability

## Implementation

### Dependency Containers

We use two container classes to organize dependencies:

```python
class ExternalDependencies:
    """Container for external dependencies like database connections, external APIs, etc."""
    
    def __init__(self, db_factory):
        self._db_factory = db_factory
        self._db = None
    
    @property
    def db(self) -> Session:
        """Get the database session."""
        if self._db is None:
            self._db = self._db_factory()
        return self._db
    
    def cleanup(self):
        """Clean up resources."""
        if self._db is not None:
            self._db.close()
            self._db = None


class InternalDependencies:
    """Container for internal dependencies like services, repositories, etc."""
    
    def __init__(self, transaction_service: TransactionService):
        self.transaction_service = transaction_service
```

### Building Dependencies

Dependencies are built in a central place:

```python
def build_external_dependencies() -> ExternalDependencies:
    """Build external dependencies for the application."""
    return ExternalDependencies(db_factory=get_db_session)


def build_internal_dependencies(external: ExternalDependencies) -> InternalDependencies:
    """Build internal dependencies using external dependencies."""
    transaction_repo = SQLAlchemyTransactionRepository(external.db)
    transaction_service = TransactionService(transaction_repo)
    return InternalDependencies(transaction_service=transaction_service)
```

### Route Registration

Routes are registered with internal dependencies:

```python
def register_transaction_routes(app: FastAPI, internal: InternalDependencies):
    """Register transaction routes with the FastAPI app."""
    router = APIRouter(prefix="/transactions", tags=["transactions"])

    @router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
    def create_transaction(transaction_data: TransactionCreate):
        """Create a new transaction"""
        transaction = internal.transaction_service.create_transaction(
            transaction_date=transaction_data.date,
            description=transaction_data.description,
            amount=transaction_data.amount,
        )
        return transaction
    
    # ... other route handlers ...

    app.include_router(router, prefix=settings.API_V1_STR)
```

### Application Setup

The application is set up with dependencies:

```python
# Build dependencies
external = build_external_dependencies()
internal = build_internal_dependencies(external)

# Register cleanup function to be called on application shutdown
atexit.register(external.cleanup)

# Register routes with dependency injection
register_transaction_routes(app, internal)
```

## Testing

Testing is simplified with this pattern. You can easily mock services:

```python
@pytest.fixture
def test_app(mock_transaction_service):
    """Create a test app with mocked dependencies."""
    app = FastAPI()
    internal = InternalDependencies(transaction_service=mock_transaction_service)
    register_transaction_routes(app, internal)
    return app
```

No monkeypatching is needed, and tests are more reliable.

## Benefits

| Feature                          | Traditional Depends | Container-based DI |
|----------------------------------|---------------------|---------------------|
| Easy to test                    | ❌ No                | ✅ Yes              |
| Requires monkeypatch            | ✅ Often             | ❌ Never            |
| Modular dependency separation   | ❌ No                | ✅ Yes              |
| Supports environment config     | ⚠️ Limited           | ✅ Fully            |
| Encourages clean architecture   | ❌ No                | ✅ Yes              |

## Resource Management

The pattern includes proper resource management:

```python
@contextmanager
def get_dependencies() -> Iterator[tuple[ExternalDependencies, InternalDependencies]]:
    """
    Context manager for getting dependencies.
    
    This ensures proper cleanup of resources when they're no longer needed.
    
    Yields:
        A tuple of (external_dependencies, internal_dependencies)
    """
    external = build_external_dependencies()
    internal = build_internal_dependencies(external)
    try:
        yield external, internal
    finally:
        external.cleanup()
```

This ensures that resources like database connections are properly closed when they're no longer needed.
