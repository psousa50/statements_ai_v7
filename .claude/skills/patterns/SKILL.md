---
name: patterns
description: Explains coding patterns and conventions used in this project
---

# Code Patterns

## Architecture

Monorepo with two applications:
- `bank-statements-api/` - Python FastAPI backend
- `bank-statements-web/` - React TypeScript frontend

### Backend: Hexagonal Architecture (Ports & Adapters)

```
app/
  domain/models/     - SQLAlchemy ORM models (entities)
  domain/dto/        - Data transfer objects
  ports/repositories/ - Abstract repository interfaces (ABC)
  adapters/repositories/ - SQLAlchemy implementations
  services/          - Business logic (application services)
  api/routes/        - FastAPI route handlers
  api/schemas.py     - Pydantic request/response models
```

Key principle: Services depend on port interfaces, not concrete adapters.

### Frontend: Feature-Based Organisation

```
src/
  api/          - API client classes (one per domain)
  auth/         - Authentication context and components
  components/   - Reusable UI components
  pages/        - Route-level components
  services/hooks/ - React Query hooks
  types/        - TypeScript interfaces
  utils/        - Helper functions
```

## Naming Conventions

### Backend (Python)

| Element | Convention | Example |
|---------|-----------|---------|
| Files | snake_case | `transaction.py`, `enhancement_rule.py` |
| Classes | PascalCase | `TransactionService`, `SQLAlchemyTransactionRepository` |
| Functions/Methods | snake_case | `get_by_id`, `create_transaction` |
| Variables | snake_case | `user_id`, `category_ids` |
| Enums | PascalCase class, UPPER_CASE values | `CategorizationStatus.UNCATEGORIZED` |
| Repository Adapters | `SQLAlchemy{Entity}Repository` | `SQLAlchemyTransactionRepository` |
| Port Interfaces | `{Entity}Repository` | `TransactionRepository` |

### Frontend (TypeScript)

| Element | Convention | Example |
|---------|-----------|---------|
| Files - Components | PascalCase | `TransactionTable.tsx`, `CategorySelector.tsx` |
| Files - API Clients | PascalCase with `Client` suffix | `TransactionClient.ts` |
| Files - Hooks | camelCase with `use` prefix | `useTransactions.ts` |
| Files - Types | PascalCase | `Transaction.ts` |
| Files - CSS | Same as component | `TransactionsPage.css` |
| React Components | PascalCase | `TransactionTable`, `CategorySelector` |
| Hooks | camelCase with `use` prefix | `useTransactions`, `useCategories` |
| Interfaces | PascalCase | `TransactionFilters`, `CategoryTotal` |
| API methods | camelCase | `getAll`, `countSimilar` |

## Design Patterns

### Repository Pattern (Backend)

Abstract interface in `ports/`:
```python
class TransactionRepository(ABC):
    @abstractmethod
    def get_by_id(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        pass
```

Concrete implementation in `adapters/`:
```python
class SQLAlchemyTransactionRepository(TransactionRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_id(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        return self.db_session.query(Transaction).filter(...).first()
```

### Service Layer (Backend)

Services contain business logic, depend on repository interfaces:
```python
class TransactionService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        initial_balance_repository: InitialBalanceRepository,
        ...
    ):
        self.transaction_repository = transaction_repository
```

### Dependency Injection (Backend)

`InternalDependencies` container built in `core/dependencies.py`:
- Creates all repositories and services
- Injected via FastAPI's `Depends()`
- Context manager handles DB session lifecycle

### API Client Pattern (Frontend)

Each domain has a dedicated client class:
```typescript
export interface TransactionClient {
  getAll(filters?: TransactionFilters): Promise<TransactionListResponse>
  create(data: TransactionCreate): Promise<Transaction>
  ...
}

export const createTransactionClient = (api: AxiosInstance): TransactionClient => ({
  getAll: async (filters) => { ... },
  create: async (data) => { ... },
})
```

### Custom Hooks (Frontend)

Data fetching via custom hooks with React Query:
```typescript
export const useTransactions = () => {
  const api = useApi()
  const queryClient = useQueryClient()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  ...
}
```

## Error Handling

### Backend

- HTTPException for API errors with appropriate status codes
- Validation via Pydantic schemas
- No try/catch around expected failures - let FastAPI handle

### Frontend

- try/catch in hooks, set error state
- Display errors via Toast component
- Axios interceptor for 401 handling (auto-refresh token)

## State Management (Frontend)

- React Query for server state caching and invalidation
- React Context for global state (auth, theme)
- URL search params for filter state (persisted in URL)
- Local component state for UI interactions

Query key pattern:
```typescript
export const TRANSACTION_QUERY_KEYS = {
  all: ['transactions'] as const,
  list: (filters?: TransactionFilters) => ['transactions', 'list', filters] as const,
}
```

## API Patterns

### Request/Response Schemas (Backend)

Pydantic models with `model_config = ConfigDict(from_attributes=True)`:
```python
class TransactionResponse(BaseModel):
    id: UUID
    date: date
    description: str
    ...
    model_config = ConfigDict(from_attributes=True)
```

### Route Registration

Routes registered via function that takes the FastAPI app:
```python
def register_transaction_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/transactions", tags=["transactions"])
    ...
```

### Filter Parameters

Consistent filter parameter names across frontend and backend:
- `page`, `page_size` for pagination
- `start_date`, `end_date` for date ranges
- `category_ids` (comma-separated in URL)
- `sort_field`, `sort_direction`
- `exclude_transfers`, `exclude_uncategorized` (boolean flags)

## Testing Patterns

### Backend

- pytest with fixtures in `conftest.py`
- Mock repositories using `MagicMock(spec=Repository)`
- Test structure: `tests/unit/services/`, `tests/integration/`
- Test file naming: `test_{module}.py`

### Frontend

- Vitest for unit tests
- Tests in `tests/` directory

## Code Style

- No comments unless absolutely necessary
- Methods return early on error conditions
- Descriptive variable/function names over comments
- Enums inherit from `str, Enum` for JSON serialisation
- Optional parameters use `Optional[T] = None`
- UUID fields use `UUID(as_uuid=True)` in SQLAlchemy

## CSS Conventions

- One CSS file per page/component
- CSS custom properties for theming
- Class naming: kebab-case (`.transaction-table`, `.filter-row`)
- Responsive breakpoints in CSS
