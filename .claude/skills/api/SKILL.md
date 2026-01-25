---
name: api
description: Explains this project's API structure, endpoints, and patterns
---

# API Guide

## Architecture

REST API built with FastAPI (Python). All routes prefixed with `/api/v1`.

### Key Files

- `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/main.py` - FastAPI app entry point, middleware setup
- `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/app.py` - Route registration
- `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/api/routes/` - Route handlers
- `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/api/schemas.py` - Pydantic request/response models
- `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/core/dependencies.py` - Dependency injection
- `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/core/config.py` - Settings from env vars

### Layered Architecture

```
Routes (app/api/routes/) -> Services (app/services/) -> Repositories (app/adapters/repositories/)
                                                     -> Domain Models (app/domain/models/)
```

## Endpoints

### Auth (`/api/v1/auth`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/google` | Initiate Google OAuth |
| GET | `/google/callback` | OAuth callback |
| POST | `/register` | Email/password registration |
| POST | `/login` | Email/password login |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Logout (revoke refresh token) |
| GET | `/me` | Get current user |
| POST | `/test-login` | E2E test login (only when `E2E_TEST_MODE=true`) |

### Transactions (`/api/v1/transactions`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `` | Create transaction |
| GET | `` | List transactions (paginated, filterable) |
| GET | `/export` | Export to CSV |
| GET | `/category-totals` | Aggregated totals by category |
| GET | `/category-time-series` | Time series data |
| GET | `/recurring-patterns` | Detect recurring expenses |
| POST | `/preview-enhancement` | Preview rule enhancement |
| PUT | `/bulk-update-category` | Bulk update by description |
| GET | `/count-similar` | Count similar transactions |
| GET | `/count-by-category` | Count by category |
| PUT | `/bulk-replace-category` | Replace category in bulk |
| GET | `/{transaction_id}` | Get single transaction |
| PUT | `/{transaction_id}` | Update transaction |
| DELETE | `/{transaction_id}` | Delete transaction |
| PUT | `/{transaction_id}/categorize` | Set category |
| PUT | `/{transaction_id}/mark-failure` | Mark categorisation failed |
| GET | `/categorization-jobs/{job_id}/status` | Background job status |

### Statements (`/api/v1/statements`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Upload and analyse statement file |
| POST | `/{uploaded_file_id}/preview-statistics` | Preview with filters |
| POST | `/upload` | Process and save statement |
| GET | `` | List all statements |
| DELETE | `/{statement_id}` | Delete statement and transactions |

### Categories (`/api/v1/categories`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `` | Create category |
| GET | `` | List all categories |
| GET | `/root` | List root categories only |
| GET | `/export` | Export to CSV |
| GET | `/{category_id}` | Get category |
| GET | `/{category_id}/subcategories` | Get subcategories |
| PUT | `/{category_id}` | Update category |
| DELETE | `/{category_id}` | Delete category |
| POST | `/upload` | Upload categories CSV |
| POST | `/ai/generate-suggestions` | AI suggest new categories |
| POST | `/ai/create-selected` | Create AI-suggested categories |

### Accounts (`/api/v1/accounts`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `` | Create account |
| GET | `` | List all accounts |
| GET | `/export` | Export to CSV |
| GET | `/{account_id}` | Get account |
| PUT | `/{account_id}` | Update account |
| DELETE | `/{account_id}` | Delete account |
| PUT | `/{account_id}/initial-balance` | Set initial balance |
| DELETE | `/{account_id}/initial-balance` | Delete initial balance |
| POST | `/upload` | Upload accounts CSV |

### Enhancement Rules (`/api/v1/enhancement-rules`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `` | List rules (paginated, filterable) |
| GET | `/stats` | Rule statistics |
| POST | `/cleanup-unused` | Delete unused rules |
| GET | `/{rule_id}/matching-transactions/count` | Count matching transactions |
| POST | `/preview/matching-transactions/count` | Preview rule match count |
| GET | `/{rule_id}` | Get rule |
| POST | `` | Create rule |
| PUT | `/{rule_id}` | Update rule |
| DELETE | `/{rule_id}` | Delete rule |
| POST | `/ai/suggest-categories` | AI suggest categories for rules |
| POST | `/ai/suggest-counterparties` | AI suggest counterparties |
| POST | `/{rule_id}/ai-suggestion/apply` | Apply AI suggestion |
| POST | `/{rule_id}/ai-suggestion/reject` | Reject AI suggestion |

### Other Endpoints
- **Description Groups** (`/api/v1/description-groups`) - Group similar descriptions
- **Saved Filters** (`/api/v1/saved-filters`) - Temporary saved transaction selections
- **Filter Presets** (`/api/v1/filter-presets`) - Named filter configurations

## Authentication

### Method
Cookie-based JWT authentication with refresh tokens.

### Flow
1. User authenticates via OAuth or email/password
2. Server sets `access_token` (15 min) and `refresh_token` (7 days) cookies
3. Cookies are `httponly`, `secure` (if HTTPS), `samesite=lax|none`
4. Access token decoded from cookie on each request

### Protecting Routes
```python
from app.api.routes.auth import require_current_user

@router.get("/protected")
def protected_endpoint(
    current_user: User = Depends(require_current_user),
):
    # current_user guaranteed to be authenticated
```

### Key Functions (`/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/api/routes/auth.py`)
- `require_current_user` - Dependency, raises 401 if not authenticated
- `get_current_user_from_cookie` - Returns User or None
- `_set_auth_cookies` / `_clear_auth_cookies` - Cookie management

## Request/Response Patterns

### Pydantic Schemas
All request/response models in `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/api/schemas.py`.

```python
class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[UUID] = None
    color: Optional[str] = None

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    color: Optional[str] = None
    parent_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
```

### Naming Conventions
- `*Create` - POST request body
- `*Update` - PUT request body
- `*Response` - Response body
- `*ListResponse` - Paginated list response

### Pagination Pattern
```python
class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

Query parameters: `page` (1-based), `page_size` (default 20, max 100)

### List Responses
Non-paginated lists use:
```python
class CategoryListResponse(BaseModel):
    categories: Sequence[CategoryResponse]
    total: int
```

## Error Handling

### HTTP Exceptions
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Category with ID {category_id} not found",
)
```

### Standard Error Codes
| Code | Usage |
|------|-------|
| 400 | Bad request, validation error |
| 401 | Not authenticated |
| 403 | Forbidden (e.g., test endpoint in prod) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate name) |
| 422 | Validation error (automatic from Pydantic) |
| 500 | Server error |

### Pattern
```python
@router.post("")
def create_resource(data: CreateRequest, ...):
    try:
        # business logic
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

## Adding New Endpoints

### 1. Create/Update Schemas
Add Pydantic models to `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/api/schemas.py`:
```python
class NewResourceCreate(BaseModel):
    name: str
    ...

class NewResourceResponse(BaseModel):
    id: UUID
    name: str
    ...
    model_config = ConfigDict(from_attributes=True)
```

### 2. Create Route File
Create `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/api/routes/new_resource.py`:
```python
from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.routes.auth import require_current_user
from app.api.schemas import NewResourceCreate, NewResourceResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User


def register_new_resource_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/new-resources", tags=["new-resources"])

    @router.post(
        "",
        response_model=NewResourceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_new_resource(
        data: NewResourceCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        resource = internal.new_resource_service.create(
            user_id=current_user.id,
            name=data.name,
        )
        return resource

    @router.get("", response_model=NewResourceListResponse)
    def list_new_resources(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        resources = internal.new_resource_service.get_all(current_user.id)
        return NewResourceListResponse(resources=resources, total=len(resources))

    app.include_router(router, prefix=settings.API_V1_STR)
```

### 3. Register Routes
Update `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/app.py`:
```python
from app.api.routes.new_resource import register_new_resource_routes

def register_app_routes(app, provide_dependencies):
    # ... existing routes ...
    register_new_resource_routes(app, provide_dependencies)
```

### 4. Add Dependencies (if needed)
Update `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/core/dependencies.py`:
- Add repository/service to `InternalDependencies` class
- Instantiate in `build_internal_dependencies()`

## Middleware

Configured in `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/main.py`:

1. **Request timing** - Logs request duration
2. **SessionMiddleware** - For OAuth state
3. **CORSMiddleware** - Cross-origin requests from frontend

## Background Jobs

For long-running operations (e.g., AI categorisation):

1. Create job via `BackgroundJobService`
2. Return job ID to client
3. Client polls `/transactions/categorization-jobs/{job_id}/status`
4. Job processor runs async via FastAPI `BackgroundTasks`

## Environment Variables

Key settings in `/Users/pedrosousa/Work/Personal/Code/statements-ai-v7/bank-statements-api/app/core/config.py`:
- `DATABASE_URL` - PostgreSQL connection
- `API_BASE_URL` / `WEB_BASE_URL` - For OAuth redirects
- `JWT_SECRET_KEY` - Token signing
- `GOOGLE_OAUTH_CLIENT_ID/SECRET` - OAuth credentials
- `GEMINI_API_KEY` / `GROQ_API_KEY` - LLM providers
- `E2E_TEST_MODE` - Enables test login endpoint
