# Development Commands

Run all commands from the root directory using pnpm.

## Quick Start
```bash
pnpm start              # Start db + dev servers (API :8000, Web :5173)
pnpm dev                # Dev servers only (assumes db running)
```

## Testing
```bash
pnpm test               # Run all tests (unit + integration + web)
pnpm test:api           # Backend tests only
pnpm test:web           # Frontend tests only
pnpm test:e2e           # E2E tests (Playwright)
```

## Database
```bash
pnpm db:start           # Start db container + run migrations
pnpm db:migrate         # Run migrations only
pnpm test:db:up         # Start test db (port 15432)
pnpm test:db:migrate    # Migrate test db
```

## Linting & Formatting
```bash
pnpm format             # Format all code
pnpm lint               # Lint all code
pnpm lint:fix           # Lint and fix
pnpm check              # Type check (web) + lint (api)
pnpm verify             # Format + lint + test (both)
```

## Deployment
```bash
pnpm deploy:setup       # Sync settings.prod.yaml to GitHub secrets + Render env vars
```

## Notes
- Hot reload enabled on both services
- Update tests when changing behaviour

## Local Auth Bypass (for Chrome MCP / automation)

To bypass Google Auth locally, the app must be running with `E2E_TEST_MODE=true`.

For Chrome MCP, the correct order is:
1. Navigate to the app (e.g., `http://localhost:5173`)
2. Call the test-login endpoint
3. Reload the page (required for React auth state to sync)

```javascript
await fetch('/api/v1/auth/test-login', { method: 'POST', credentials: 'include' });
location.reload();
```

This creates a test user (`e2e-test@example.com`) and sets auth cookies without requiring Google OAuth.
