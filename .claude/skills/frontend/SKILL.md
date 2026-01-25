---
name: frontend
description: Explains this project's frontend architecture, components, and UI patterns
---

# Frontend Guide

## Framework

**React 18** with TypeScript, built with **Vite**.

Key libraries:
- `@mui/material` (v7) - Component library with custom amber/gold theme
- `@tanstack/react-query` (v5) - Server state management with caching
- `react-router-dom` (v7) - Client-side routing
- `axios` - HTTP client
- `recharts` - Charting
- `react-day-picker` - Date selection
- `react-dropzone` - File uploads
- `date-fns` - Date utilities

## Component Structure

```
bank-statements-web/src/
├── api/                    # API clients and context
│   ├── ApiClient.ts        # Client interface aggregating domain clients
│   ├── ApiContext.tsx      # React context for API access
│   ├── *Client.ts          # Domain-specific API clients (TransactionClient, CategoryClient, etc.)
│   └── AuthClient.ts       # Authentication API
├── auth/                   # Authentication
│   ├── AuthContext.tsx     # Auth state + token refresh
│   └── ProtectedRoute.tsx  # Route guard
├── components/             # Reusable UI components
│   ├── layout/             # AppLayout, AppNavigation, UserMenu
│   ├── upload/             # File upload components
│   ├── DatePeriodNavigator/# Date navigation with own CSS
│   └── *.tsx               # Feature components (TransactionTable, CategorySelector, etc.)
├── pages/                  # Route page components
│   └── *.tsx               # One per route (Transactions, Categories, Charts, etc.)
├── services/hooks/         # Custom data hooks
│   └── use*.ts             # useTransactions, useCategories, useAccounts, etc.
├── theme/                  # Theme configuration
│   └── ThemeContext.tsx    # MUI theme + light/dark mode
├── types/                  # TypeScript types
│   └── *.ts                # Transaction, EnhancementRule, Auth, etc.
├── utils/                  # Utility functions
│   ├── format.ts           # Currency/date formatting
│   └── categoryColors.ts   # Category colour utilities
├── App.tsx                 # Router configuration
└── main.tsx                # App entry point with providers
```

## State Management

**Three-tier approach:**

1. **Server State** - TanStack Query
   - 5-minute stale time by default
   - Manual cache invalidation via `queryClient.invalidateQueries()`
   - Query keys defined per-hook (e.g. `TRANSACTION_QUERY_KEYS`)

2. **Global UI State** - React Context
   - `AuthContext` - User session, login/logout, token refresh
   - `ThemeContext` - Light/dark/system mode with localStorage persistence
   - `ApiContext` - Provides API client to components

3. **Local State** - useState/useCallback
   - Filter state with URL sync via `useSearchParams`
   - Modal open/close states
   - Debounced input values

**Data Hooks Pattern:**
```tsx
// Services layer wraps API calls with caching and mutation logic
const { transactions, loading, fetchTransactions, categorizeTransaction } = useTransactions()
```

## Routing

React Router v7 with nested routes:

- `/login`, `/register`, `/auth/callback` - Public routes
- `/` - Protected route wrapper with `AppLayout`
  - `/transactions` (index)
  - `/categories`
  - `/accounts`
  - `/charts`
  - `/recurring`
  - `/enhancement-rules`
  - `/categorizations`
  - `/statements`
  - `/upload`
  - `/settings`

Route guards via `ProtectedRoute` component checking `AuthContext`.

## Styling

**Hybrid approach:**

1. **CSS Variables** (`index.css`)
   - Design tokens: `--bg-primary`, `--text-accent`, `--button-primary`, etc.
   - Dark mode via `[data-theme='dark']` selector
   - Typography: Sora (display), DM Sans (body), JetBrains Mono (numbers)

2. **MUI Theme** (`ThemeContext.tsx`)
   - Extends CSS variables into MUI components
   - Component overrides for Drawer, AppBar, TableCell, etc.
   - Amber/gold accent colour scheme

3. **Component CSS** (co-located `*.css` files)
   - Page-specific styles: `TransactionsPage.css`, `CategoriesPage.css`
   - Component-specific: `Pagination.css`, `CategorySelector.css`

4. **MUI Overrides** (in `index.css`)
   - Global button, input, dialog styling
   - Icon button states and colours

## Creating Components

**Page Components:**
1. Create `src/pages/MyPage.tsx`
2. Add corresponding `src/pages/MyPage.css` if needed
3. Register route in `App.tsx`
4. Add navigation entry in `components/layout/AppNavigation.tsx`

**Feature Components:**
1. Create in `src/components/MyComponent.tsx`
2. Use MUI components + CSS variables for styling
3. Accept data/callbacks as props, avoid internal API calls

**Data Hooks:**
1. Create in `src/services/hooks/useMyData.ts`
2. Use `useApi()` for API access
3. Define query keys for cache management
4. Wrap mutations with error handling

**API Clients:**
1. Create `src/api/MyClient.ts` with typed methods
2. Add to `ApiClient` interface
3. Instantiate in `createApiClient.ts`

## Key Patterns

- **URL Filter Sync**: Pages sync filter state to URL params for shareable links
- **Debounced Inputs**: Text/amount filters use local state + debounce before API call
- **Optimistic Updates**: Mutations update local state immediately, then invalidate cache
- **Responsive Layout**: `AppLayout` switches between permanent/temporary drawer based on screen size and touch detection
- **Modal Pattern**: State managed in parent page, data passed as props
