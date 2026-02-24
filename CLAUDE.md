# Project: Bank Statements AI

Read ARCHITECTURE.md before planning features.
Update ARCHITECTURE.md when making changes that affect its content.

## Local Auth Bypass

For Chrome MCP / automation, the app must be running with `E2E_TEST_MODE=true`.

1. Navigate to the app (e.g., `http://localhost:5173`)
2. Call the test-login endpoint
3. Reload the page (required for React auth state to sync)

```javascript
await fetch("/api/v1/auth/test-login", {
  method: "POST",
  credentials: "include",
});
location.reload();
```

This creates a test user (`e2e-test@example.com`) and sets auth cookies without requiring Google OAuth.