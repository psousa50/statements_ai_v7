# Python Development Rules

## Strict Type Discipline (Python 3.10+ Recommended)

**MANDATORY**: Code must be type-annotated and validated using runtime tools like [`pydantic`](https://docs.pydantic.dev) or [`attrs`](https://www.attrs.org). Use `mypy` or [`pyright`](https://github.com/microsoft/pyright) for static checking.

## Type Safety Rules

### Absolute Prohibitions

- **No use of untyped functions or variables** – all public functions and methods must have type annotations.
- **Avoid `Any`** – use `object` or `Unpack[...]` if truly required.
- **No `# type: ignore`** without justification in comments.
- These rules apply to **all code** – production and tests.

### Typing Standards

- Use `dataclasses`, `pydantic.BaseModel`, or `attrs` for all structured data.
- Use `Literal`, `TypedDict`, and `NewType` for domain clarity and validation.
- Example: Domain-safe typing

```python
from typing import NewType

UserId = NewType("UserId", str)
PaymentAmount = NewType("PaymentAmount", float)
```

Avoid raw primitives like `str` or `float` for domain concepts.

## Schema-First Development with Pydantic

**CRITICAL PATTERN**: Define schemas using Pydantic or equivalent libraries. Derive logic and I/O from schemas.

```python
from pydantic import BaseModel, Field
from typing import Optional
import re

class AddressDetails(BaseModel):
    house_number: str
    house_name: Optional[str]
    address_line1: str = Field(..., min_length=1)
    address_line2: Optional[str]
    city: str = Field(..., min_length=1)
    postcode: str = Field(..., regex=r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$", description="UK-style postcode")

# Usage
def parse_address(data: dict) -> AddressDetails:
    return AddressDetails(**data)
```

### Schema Composition

```python
from datetime import datetime
from typing import Literal

class BaseEntity(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime

class Customer(BaseEntity):
    email: str
    tier: Literal["standard", "premium", "enterprise"]
    credit_limit: float
```

## Schema Usage in Tests – CRITICAL RULE

**NEVER redefine schemas inside test files.** Always import schemas from production modules.

```python
# ❌ WRONG - Redefining schema for tests
class Project(BaseModel):
    id: str
    workspace_id: str

# ✅ CORRECT - Import real schema
from app.schemas import Project

def get_mock_project(overrides: dict = {}) -> Project:
    base = {
        "id": "proj_123",
        "workspace_id": "ws_456",
        # more fields...
    }
    return Project(**{**base, **overrides})
```

### Why Schema Reuse Matters

- **Type Safety**: Tests fail if schema changes.
- **Consistency**: Same rules in prod and tests.
- **Maintainability**: DRY structure.
- **Resilience**: Prevent test drift.

## Typed Factory Pattern for Test Data

```python
def get_mock_payment_request(overrides: dict = {}) -> PostPaymentsRequest:
    base = {
        "card_account_id": "1234567890123456",
        "amount": 100.0,
        "source": "web",
        "last_name": "Doe",
        "dob": "1980-01-01",
        "brand": "Visa",
        # ...
    }
    return PostPaymentsRequest(**{**base, **overrides})
```

## Python Naming Conventions

- **Types / Classes**: `PascalCase`
- **Functions / Variables**: `snake_case`
- **Modules**: `snake_case.py`
- **Tests**: Place in `tests/`, named like `test_payment.py`, and use `pytest` or `unittest`.

## Typed Result Pattern for Error Handling

```python
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")

class Result(Generic[T, E]):
    def __init__(self, data: T = None, error: E = None):
        self.data = data
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None

# Example usage
def process_payment(payment: Payment) -> Result[ProcessedPayment, PaymentError]:
    if not is_valid(payment):
        return Result(error=PaymentError("Invalid payment"))
    return Result(data=execute(payment))
```

## Effective Use of `typing` Utilities

```python
from typing import TypedDict, Optional, Literal

class CreatePaymentOptions(TypedDict):
    amount: float
    currency: str
    card_id: str
    customer_id: str
    description: Optional[str]
    metadata: Optional[dict[str, object]]

class UpdatePaymentOptions(TypedDict, total=False):
    description: str
    metadata: dict[str, object]
```

## Strictness in Tests

**CRITICAL**: Type rules apply to test code too.

```python
# ❌ Wrong
mock_response = {"success": True}  # No type checking

# ✅ Correct
from app.types import ApiResponse

mock_response: ApiResponse = {
    "success": True,
    "data": get_mock_payment_data(),
    "timestamp": datetime.utcnow().isoformat()
}
```
