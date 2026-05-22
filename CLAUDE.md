# Project: Bank Statements AI

Read ARCHITECTURE.md before planning features.
Update ARCHITECTURE.md when making changes that affect its content.

## Local Auth Bypass

For Chrome MCP / automation, the app must be running with `E2E_TEST_MODE=true`.

Start the app:
- `pnpm start:e2e` — logs in as the default `e2e-test@example.com` user (empty data).
- `pnpm start:as [email]` — logs in as the given user (defaults to `git config user.email`).

Then in the browser:

```javascript
await fetch("/api/v1/auth/test-login", {
  method: "POST",
  credentials: "include",
});
location.reload();
```

The endpoint sets httpOnly auth cookies without Google OAuth. It is gated by `E2E_TEST_MODE` and the impersonation email comes from the server's env (not from the HTTP request), so a leaked flag in production cannot be exploited to log in as an arbitrary user.