# FastAPI-Specific Development Rules

## Routing and Dependency Design

- Use `APIRouter` for all route groups. Avoid placing routes directly in the main app.
- Group routes by domain or feature:

```python
# app/routes/user.py
router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: str):
    ...
```

- Register routers in `main.py` or a centralized `router.py`:

```python
# app/main.py
app.include_router(user_router, prefix="/api")
```

- Use **FastAPI's dependency injection system** for shared logic and services (e.g., `get_current_user`, DB session, settings).

## Request/Response Models

- Always use Pydantic models for request bodies, query parameters, and responses.
- Define separate models for:
  - Request input
  - Response output
  - Internal logic

```python
class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
```

- Use `response_model` explicitly:

```python
@router.post("/users", response_model=UserResponse)
def create_user(data: CreateUserRequest):
    ...
```

## Status Codes and HTTP Semantics

- Always return the correct HTTP status codes:
  - `200 OK` for read
  - `201 Created` for post
  - `204 No Content` for deletes
  - `400`, `404`, `422`, etc. for errors

- Use `status.HTTP_*` constants:

```python
from fastapi import status

return JSONResponse(content=data, status_code=status.HTTP_201_CREATED)
```

## Error Handling

- Define reusable exception classes that inherit from `HTTPException`.

```python
from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, detail="Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
```

- Catch and handle exceptions globally using `app.exception_handler()` for logging or custom formatting.

## Middleware and Lifespan

- Use `@app.middleware("http")` for cross-cutting concerns like logging, request IDs, etc.
- Use `@asynccontextmanager` with `lifespan` for startup/shutdown hooks instead of legacy `@app.on_event`.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
```

## Dependency Injection Best Practices

- Inject reusable resources (e.g., DB sessions) using FastAPI dependencies.
- Don't open DB connections or external services manually inside route functions.

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- Inject using `Depends`:

```python
@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    ...
```

## Settings and Configuration

- Use `pydantic.BaseSettings` to load `.env` variables into a typed config object.
- Do not rely on `os.environ` directly throughout the code.

```python
class AppSettings(BaseSettings):
    database_url: str
    debug: bool = False

    class Config:
        env_file = ".env"
```

- Load config once and inject via dependencies or module-level constants.

## Authentication and Authorization

- Use FastAPI dependencies (`Depends`) for authentication logic.
- Return `401 Unauthorized` or `403 Forbidden` explicitly based on context.
- JWT is preferred for token auth; use libraries like `python-jose`.

## Response Modeling

- Prefer structured responses even for errors. Define a shared `ErrorResponse` model.
- Do not return raw dicts or lists for complex endpoints.

```python
class ErrorResponse(BaseModel):
    detail: str

@app.exception_handler(HTTPException)
def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail).dict()
    )
```

## Testing FastAPI Apps

- Use `httpx.AsyncClient` with FastAPI `TestClient` to test routes.
- Always test via the real HTTP interface:

```python
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post("/api/users", json={"name": "Alice", "email": "alice@example.com"})
        assert response.status_code == 201
```

- Use fixtures for setup (e.g., `test_app`, `mock_db`).
- Prefer `pytest-asyncio` for async support.

## Project Structure Guidelines

```
app/
├── api/              # Route modules grouped by domain
├── core/             # Config, app creation, middleware
├── models/           # Pydantic and DB models
├── services/         # Business logic
├── db/               # Database setup and migrations
├── tests/
└── main.py           # App entry point
```

## Async Best Practices

- Always use async endpoints unless sync is required for a blocking library.
- Use `asyncpg`, `databases`, or `SQLModel` for async-friendly DB access.
- Avoid mixing sync I/O and async handlers to prevent blocking the event loop.
