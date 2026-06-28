# Project: Bank Statements AI

Read ARCHITECTURE.md before planning features.
Update ARCHITECTURE.md when making changes that affect its content.

## Database Migrations

The SQLAlchemy models are the source of truth for the schema; Alembic migrations are derived from them.

- ALWAYS generate migrations with `alembic revision --autogenerate`. Never hand-write a migration's schema operations. Review the generated migration and only edit it for things autogenerate cannot infer (data backfills, renames, server defaults).
- After any model change, regenerate and verify: `alembic check` must report no pending operations. CI enforces this.
- `migrations/env.py` imports `app.domain.models` so every model registers on `Base.metadata`. Keep that import — without it autogenerate and `alembic check` silently see an empty schema.
- Tests build the schema by running migrations (`alembic upgrade head`), never `Base.metadata.create_all`. This keeps tests on the same schema as production.

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