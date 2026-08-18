# The behavioural suite

Black-box tests that drive the API over HTTP, against a real Postgres, exactly as a client
would. They are the oracle: what ships is their verdict, not any agent's account of itself.

Run them with one command:

```
APP_DIR=<checkout> bank-statements-api/tests/behavioural/bin/bsai-api-verify
```

## The decisions this suite is built on

Settled before the first test was written. Change them deliberately, not incidentally —
every assertion in here depends on them.

**What is under test.** `bank-statements-api` only, over HTTP at `/api/v1`. The React
application is a separate component with its own suite and its own command; a red test here
says nothing about whether it is shippable.

**What "started" means.** Migrations applied, Postgres reachable, and the application
answering a request that touches the database. `GET /health` is *not* the readiness signal —
it returns a literal `{"status": "ok"}` and would answer with the database down. `bin/up`
polls `POST /api/v1/auth/test-login` instead, which proves routing, test mode, the `users`
table and cookie issuance in one request. It never sleeps a fixed interval.

**How a test authenticates.** `POST /api/v1/auth/test-login`, the application's own test-mode
bypass, gated on `E2E_TEST_MODE`. It resolves to one fixed user, `e2e-test@example.com`, and
**every test in this suite is that same user.** That is chosen, not accidental — see the
isolation strategy below.

**Which dependencies are real.** Postgres is real, on the compose `test-db`. The LLM provider
is not: `E2E_TEST_MODE=true` swaps in `NoopLLMClient`. **So any test touching AI
categorisation or chat describes the stub, not a real model.** Do not write assertions here
that only a real provider could satisfy, and do not read a green suite as evidence that
categorisation works.

## Isolation: unique identifiers, no cleanup

**Every test creates its own entities under generated names, and asserts only on the ids it
created.** Nothing is torn down. Tests share one long-lived database, one application process
and one user, so the data a test can see includes everything every earlier test left behind.

**What this forbids.** No test may assert a global count, or that a collection is *exactly*
some set. `GET /accounts` returns every account this suite has ever created. A test may say
"the account I created is in the response". It may never say "the response contains three
accounts".

Be clear about what that costs: a change that wrongly returns *too much* — a filter silently
ignored, a scope dropped — cannot be caught by an assertion of this shape. If a task turns on
exactly that, the test must create its own user and assert within it.

**Creating extra users is allowed and is a different thing.** Multi-tenancy is a behaviour of
the application, and a test proving user B cannot see user A's transactions should register
both. That is testing scoping, not opting out of the strategy.

**Growth, said out loud.** Rows accumulate forever under `e2e-test@example.com`. List
endpoints get slower and more pagination-dependent as the suite is run, and a test written
today against 200 rows behaves differently against 200,000. The reset is to destroy the
database and let `bin/up` migrate a fresh one:

```
docker compose --profile test rm -sfv test-db
```

Do that between tasks, and always before a mutation campaign.

**Re-runnability is a property we get from this and should keep.** Running the whole suite
twice against the same database must give the same result. That is a real check — the unique
constraints `uq_accounts_user_name` and `uq_tags_user_id_lower_name` sit inside the shared
user, so a test that hardcodes a name passes once and 409s forever after. Use the `unique`
fixture. Note what it does *not* prove: the order never varies between those runs, so a test
that depends on an earlier one having run stays invisible. That needs a file run alone.

## Stable test ids

Every test carries `@pytest.mark.behaviour("accounts.creation.…")`, enforced at collection —
an unmarked test is a collection error, not a warning. The id is what the invocation record
names when a test fails, and what a caller maps back to a decision or a specification. It is
deliberately not derived from the function name, so a test can be renamed for clarity without
breaking anything downstream. Dotted, area first, behaviour last.

## Helpers

Grown, not designed. The rule: hand-roll the first two tests, and extract a helper only when a
third test needs the same thing. Nothing lives in `conftest.py` that fewer than three tests
use.

## The contract this satisfies

| | |
| --- | --- |
| `APP_DIR` | the checkout to test. Required. |
| `BSAI_API_APP_SUBDIR` | where the application sits inside it. Falls back to `APP_SUBDIR`, then to this suite's own location. |
| `BSAI_API_RECORD_DIR` | where `invocations.jsonl` is appended. Defaults to `$APP_DIR/.bsai-api/`. |
| `BSAI_API_DATABASE_URL` | defaults to the compose `test-db` on 15432. |
| `BSAI_API_PORT` | defaults to 8020. |
| `BSAI_API_SEED` | seeds generated names. Recorded every run. |

Exit codes: `0` passed, `1` the application did not start or died mid-run, `2` the suite ran
and tests failed, `3` the harness itself broke. These are not interchangeable — `1` versus `2`
is "your code never ran" versus "your code is wrong".

One JSON object is **appended** per invocation to `$BSAI_API_RECORD_DIR/invocations.jsonl`.
Never overwritten: how many times a builder invoked the suite before it went green is the
measurement, and a file that is rewritten each run destroys it.

**One deviation from the harness contract, deliberate.** `bin/down` stops the application but
leaves the database container running. Tearing it down per invocation would cost a container
start and a full migration on every one of a builder's iterations, and the isolation strategy
above expects accumulation across invocations anyway. The reset is manual and per-task.
