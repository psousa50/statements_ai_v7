# TypeScript Development Rules

## Strict Mode Requirements

## Type Safety Rules

### Absolute Prohibitions

- **No `any` types** - ever. Use `unknown` if type is truly unknown
- **No type assertions** (`as SomeType`) unless absolutely necessary with clear justification
- **No `@ts-ignore`** or `@ts-expect-error` without explicit explanation
- These rules apply to both production AND test code

### Type Definition Standards

- **Prefer `type` over `interface`** in all cases
- Use explicit typing where it aids clarity, but leverage inference where appropriate
- Utilize utility types effectively (`Pick`, `Omit`, `Partial`, `Required`, etc.)
- Create domain-specific branded types for type safety:

```typescript
// Good - Branded types for domain safety
type UserId = string & { readonly brand: unique symbol };
type PaymentAmount = number & { readonly brand: unique symbol };

// Avoid - Generic primitive types
type UserId = string;
type PaymentAmount = number;
```

## Schema-First Development with Zod

**CRITICAL PATTERN**: Always define schemas first, then derive types:

```typescript
import { z } from "zod";

// Define schemas first - these provide runtime validation
const AddressDetailsSchema = z.object({
  houseNumber: z.string(),
  houseName: z.string().optional(),
  addressLine1: z.string().min(1),
  addressLine2: z.string().optional(),
  city: z.string().min(1),
  postcode: z.string().regex(/^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$/i),
});

// Derive types from schemas
type AddressDetails = z.infer<typeof AddressDetailsSchema>;

// Use schemas at runtime boundaries
export const parsePaymentRequest = (data: unknown): PostPaymentsRequestV3 => {
  return PostPaymentsRequestV3Schema.parse(data);
};
```

### Schema Composition Patterns

```typescript
// Base schema composition
const BaseEntitySchema = z.object({
  id: z.string().uuid(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

const CustomerSchema = BaseEntitySchema.extend({
  email: z.string().email(),
  tier: z.enum(["standard", "premium", "enterprise"]),
  creditLimit: z.number().positive(),
});

type Customer = z.infer<typeof CustomerSchema>;
```

## Schema Usage in Tests - CRITICAL RULE

**NEVER redefine schemas in test files**. Tests must use real schemas from shared modules:

```typescript
// ❌ WRONG - Defining schemas in test files
const ProjectSchema = z.object({
  id: z.string(),
  workspaceId: z.string(),
  // ... redefined schema
});

// ✅ CORRECT - Import schemas from shared location
import { ProjectSchema, type Project } from "@your-org/schemas";

// ✅ CORRECT - Test factories using real schemas
const getMockProject = (overrides?: Partial<Project>): Project => {
  const baseProject = {
    id: "proj_123",
    workspaceId: "ws_456",
    // ... complete mock data
  };

  const projectData = { ...baseProject, ...overrides };

  // Validate against real schema to catch type mismatches
  return ProjectSchema.parse(projectData);
};
```

### Why Schema Reuse Matters

- **Type Safety**: Ensures tests use the same types as production code
- **Consistency**: Changes to schemas automatically propagate to tests
- **Maintainability**: Single source of truth for data structures
- **Prevents Drift**: Tests can't accidentally diverge from real schemas

## Test Data Factory Pattern

Use typed factory functions with optional overrides:

```typescript
const getMockPaymentPostPaymentRequest = (
  overrides?: Partial<PostPaymentsRequestV3>
): PostPaymentsRequestV3 => {
  return {
    CardAccountId: "1234567890123456",
    Amount: 100,
    Source: "Web",
    AccountStatus: "Normal",
    LastName: "Doe",
    DateOfBirth: "1980-01-01",
    PayingCardDetails: {
      Cvv: "123",
      Token: "token",
    },
    AddressDetails: getMockAddressDetails(),
    Brand: "Visa",
    ...overrides,
  };
};
```

## TypeScript-Specific Naming Conventions

- **Types**: `PascalCase` (e.g., `PaymentRequest`, `UserProfile`)
- **Files**: `kebab-case.ts` for all TypeScript files
- **Test files**: `*.test.ts` or `*.spec.ts`

## Type-Safe Error Handling Patterns

```typescript
// Result type pattern with proper TypeScript typing
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

const processPayment = (
  payment: Payment
): Result<ProcessedPayment, PaymentError> => {
  if (!isValidPayment(payment)) {
    return { success: false, error: new PaymentError("Invalid payment") };
  }

  return { success: true, data: executePayment(payment) };
};
```

## Utility Type Usage

Leverage TypeScript's built-in utility types effectively:

```typescript
// Extract configuration types
type CreatePaymentOptions = {
  amount: number;
  currency: string;
  cardId: string;
  customerId: string;
  description?: string;
  metadata?: Record<string, unknown>;
};

// Use utility types for variations
type UpdatePaymentOptions = Partial<Pick<CreatePaymentOptions, 'description' | 'metadata'>>;
type PaymentSummary = Omit<CreatePaymentOptions, 'cardId' | 'customerId'>;
```

## TypeScript Strict Mode in Tests

**CRITICAL**: Test code must follow the same TypeScript strict mode rules as production code. No exceptions for:

- `any` types in test mocks
- Type assertions without justification
- Ignoring TypeScript errors
- Looser type checking

```typescript
// ❌ Wrong - Using any in tests
const mockApiResponse: any = { /* mock data */ };

// ✅ Correct - Properly typed test data
const mockApiResponse: ApiResponse = {
  success: true,
  data: getMockPaymentData(),
  timestamp: new Date().toISOString(),
};
```