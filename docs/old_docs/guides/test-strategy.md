# Test Strategy

* Repository tests must be **integration tests**.
* They should connect to a real database configured with a `DATABASE_URL` environment variable.
* Each test must:

  * Start a transaction at the beginning.
  * Roll back the transaction at the end.
  * Be isolated and independent of others.

* All other components must be tested using **unit tests**.

* Avoid mocking libraries — use real or in-memory implementations for tests.
* Use dependency injection to provide alternate dependencies in tests.
* Never place test logic in production code.
* Ensure tests are fully isolated and independent.

