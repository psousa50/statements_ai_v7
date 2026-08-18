---
name: behavioural-harness
description: Stand up the harness that runs a behavioural suite against a real application — the verify command, the application lifecycle, the machine-readable invocation record, and the isolation strategy. Use this when starting behavioural testing on an application or a new surface of one (an HTTP API, a websocket protocol), porting a harness to another stack, or when a tool that drives the suite — a builder loop, CI, a mutation campaign — needs a contract it can rely on. Not for writing the tests themselves; that is behavioural-stress. This is a working session with the developer, not a specification to execute unattended.
---

# Behavioural harness

A behavioural suite is worthless to an automated caller unless the thing that runs it is
predictable. This skill specifies **the contract a harness must satisfy** and walks the
decisions that precede it. It is deliberately not a template: the implementation is
per-stack, and copying a harness from another language teaches you nothing about which
parts were load-bearing.

The contract exists because the caller is usually **not a human**. A builder agent under a
cap, a CI job, or a mutation campaign firing the suite ten thousand times all need to answer
"what happened" from an exit code and a file, without reading prose.

## This is a conversation

Build the harness **with** the developer. Most of what follows is a decision, not a
discovery — reading the repository harder will not produce an answer, and guessing produces
a harness that is subtly about the wrong application. Ask, propose, and record what was
decided.

A harness is built roughly once per application, or once per surface. That is precisely why
it is worth an hour of someone's attention rather than an unattended run.

### If slipway set this repository up, the names are already decided

Read `.slipway/components/*/config`. **The directory name is the harness's name** and
`SUITE_DIR` inside is where it lives, and between them they fix four things you would
otherwise invent:

| `components/bsai/` with `SUITE_DIR=tests/behavioural` | |
| --- | --- |
| `tests/behavioural/bin/bsai-verify` | the command — slipway puts that `bin/` on the builder's `PATH` |
| `$BSAI_RECORD_DIR` | where slipway tells the harness to write its record |
| `$BSAI_APP_SUBDIR` | where this component's application sits in the checkout |
| `BSAI_DATABASE_URL`, `BSAI_PORT` | yours, sharing the namespace — slipway never sets these |

**Use those names exactly.** A harness that reads a variable slipway does not set does not
fail: it quietly writes its record somewhere else, and slipway sees no invocations at all.
`slipway doctor` catches it, but only after you have built the wrong thing.

If there is no `.slipway/components/` yet, pick a name now and use it consistently — it is the
same decision, made in a different order.

**Every application in the repository is a component**, one or several, each with its own suite
and its own command — `.slipway/components/api/config`, `.slipway/components/ui/config`. **A
component's directory name is its prefix** — there is no separate `PREFIX` to set, because a
second name for one harness is a second thing to keep in sync, and the root config configures
runs rather than harnesses. `components/api/` means `api-verify`, `$API_RECORD_DIR` and
`$API_APP_SUBDIR`, and the config file inside holds only `SUITE_DIR` and `APP_SUBDIR`. Pick a
name that is distinctive on a shared `PATH` and in a shared environment; that is the only
constraint on it. Where there are several you are building one of those harnesses, not all
of them.
`slipway component list` says which. The rule below about one command still applies to the
one you are building; see *Where the one-command rule stops*.

### Settle these before writing anything

1. **What is the application under test?** API only, or API and UI? One service or several?
   If the system has more than one interface — HTTP and websockets, say — they still share
   **one command**: it brings the application up once, runs both suites against it, appends
   one record with ids namespaced by surface (`http.…`, `ws.…`), and exits with the worse of
   the two codes. Two commands means two records, and a caller cannot combine two verdicts
   into one answer to *am I green*. What genuinely differs between surfaces is lifecycle and
   isolation, and both belong inside the one harness that owns them.

   ### Where the one-command rule stops

   It stops at the component boundary, and only there. A FastAPI service and a React UI in
   one repository are two applications: two lifecycles, two runtimes, two isolation
   strategies, and a red UI test that says nothing about whether the API is shippable.
   Forcing them under one command buys a combined verdict nobody wanted and a harness that
   is subtly about neither.

   So they are two components with two commands, and **slipway combines the verdicts** — it
   runs the harness of every component the change constrains and takes the worst outcome.
   Be clear about what that costs: with more than one component, no single command answers
   *am I green* any more, and slipway is the only thing that can. Within a component the
   rule is unchanged and is not negotiable.

   The test: would a red result here make you hold the other application's release? If yes,
   one command. If no, two components.
2. **What does "started" mean?** A process listening is not the same claim as *migrations
   applied, dependencies up, authentication reachable*. A readiness endpoint answering
   proves the first and says nothing about the second. Decide which one `ready` asserts.
3. **How does a test authenticate?** Many applications have a test-mode bypass; if one
   exists, using it is usually right, and how it is gated is worth reading before relying
   on it.
4. **Which dependencies are real?** Databases, queues and caches are normally real in a
   behavioural suite. Third-party APIs usually are not. Say which, and why.
5. **What is the isolation strategy?** See below — this is the one that constrains every
   assertion anyone writes afterwards.

Write the answers down where the suite can find them. That record is what stops the third
test author inventing a different convention from the first.

## What the harness is

One command. It:

1. starts the application under test,
2. waits for it to be ready,
3. runs the suite against it over its real interface,
4. writes a machine-readable record,
5. stops the application,
6. exits with a code that distinguishes *kinds* of failure.

It owns the application's lifecycle. A caller that must start the app itself before running
the suite has a harness that is half-built — and two callers racing to bind the same port is
a real failure mode, not a hypothetical.

## The contract

### Inputs, from the environment

| variable | meaning |
| --- | --- |
| `APP_DIR` | which checkout to test. **Required** — the whole point is running the same suite against different versions of the application. Defaulting it to the current directory is a convenience, never an assumption. |
| `<PREFIX>_APP_SUBDIR` | where **this component's** application sits inside that checkout. Take it rather than probing for it; a hardcoded directory name inside the suite is a bug waiting for the next repository. |
| `APP_SUBDIR` | the same value, set only where the repository holds one application. Where it holds several, a bare `APP_SUBDIR` could not say which one it meant, so slipway does not set it — read the prefixed variable and fall back to this one. |
| `<PREFIX>_RECORD_DIR` | where to append the invocation record. Defaults to `$APP_DIR/.<prefix>/`. A caller that keeps its own evidence sets this so nothing it writes lands inside the checkout under test — otherwise an agent running `git add -A` commits the caller's bookkeeping. |
| `<PREFIX>_DATABASE_URL`, `<PREFIX>_PORT` | where the application's dependencies live. Defaults are fine; overrides must exist so two runs can coexist. |

`<PREFIX>` is the same word the command is named after — `bsai-verify` reads
`BSAI_RECORD_DIR` — so nothing collides with the application's own configuration and the
caller can derive every name from one value. Where slipway set the repository up, that word
is the component's directory name under `.slipway/components/` and is not yours to change
unilaterally: rename the directory and the command together, or the caller and the harness
stop agreeing without either of them erroring.

### Exit codes — the part callers actually branch on

| code | meaning | what a caller does |
| --- | --- | --- |
| `0` | every test passed | done |
| `1` | the application did not start, or died mid-run | the change is broken in a way the suite never got to judge |
| `2` | the suite ran, tests failed | the interesting case: read the record |
| `3` | the harness itself failed | the result is not evidence of anything |

**Do not collapse these.** `1` versus `2` is the difference between "your code doesn't
compile" and "your code is wrong", and an agent iterating towards green needs to tell them
apart. `3` is what stops a broken harness being scored as a broken application.

It also makes mutation testing tractable without parsing anything: a mutant that exits `1`
did not build, so discard it rather than counting it as a survivor.

### The invocation record

Append one JSON object per invocation to `$<PREFIX>_RECORD_DIR/invocations.jsonl`, which
defaults to `$APP_DIR/.<prefix>/invocations.jsonl` when the caller sets nothing.

**Append, never overwrite.** The single most valuable number in an agent experiment is how
many times the agent invoked the suite before it went green; a `last-report.json` that is
rewritten each time destroys exactly that. Ask how many iterations a run took and you will
find the answer gone.

Each line carries at least:

```json
{
  "runId": "…", "startedAt": "…", "durationMs": 14312,
  "outcome": "passed" | "failed" | "app_failure" | "harness_error",
  "summary": { "total": 152, "passed": 145, "failed": 7, "skipped": 0 },
  "failed": ["area.thing.behaviour", "…"],
  "seed": "…",
  "appExitCode": null
}
```

`failed` carries **stable test ids**, not descriptions. They are how a caller maps a red test
back to a decision, a finding, or a specification — so they must survive a test being renamed
for clarity. Dotted, area-first, behaviour-last reads well and sorts usefully:
`transactions.categorize.rejects_parent_category`.

`seed` makes a run reproducible when the suite generates data. Record it even when nothing
consumes it yet; you cannot reconstruct it afterwards.

### Human output as well

The same run should print something a person can read: the outcome, counts, and for each
failure what was expected, what happened, and enough of the interaction to diagnose it
without a debugger. Two audiences, one run — the file for the tool, the prose for you.

## Application lifecycle

Two scripts and a readiness signal, kept **inside the application's repository** rather than
the suite's, because they change when the application's own startup changes:

- **`up`** — bring up dependencies, apply migrations, start the app, exit non-zero if any
  step fails. Idempotent: free the port first rather than failing because a previous run
  died badly.
- **`down`** — stop everything it started.
- **a readiness endpoint** — polled until it answers, with a timeout. Never sleep a fixed
  number of seconds; that is a race that passes on your laptop and fails in CI.

Watch the process for the whole run, not just at boot. An application that dies at test 40
must produce `app_failure` and exit `1` — not a cascade of confusing assertion failures that
look like the suite's fault.

## Isolation — the one decision that cannot wait

A suite that accretes across features shares one long-lived database and one application
process. The strategy dictates what every assertion may say, so it is a harness decision,
not a per-test one, and it cannot be retrofitted across a suite that already exists.

| strategy | how | cost |
| --- | --- | --- |
| **Unique identifiers, no cleanup** | every test creates its own entities under generated names and asserts only on ids it created | nothing may assert a global count; data grows forever |
| **Tenant-scoped** | every test registers its own user or tenant, and the application scopes rows to it | needs the application to enforce that scoping — but then a test *may* say "my accounts are exactly these two" |
| **Transactional rollback** | each test runs in a transaction that is rolled back | impossible when the application owns its own connections — rules out most black-box HTTP harnesses |
| **Reset between tests** | truncate or re-migrate per test | slow, and rules out parallelism against a shared database |

Read the application before choosing. Tenant-scoped is stronger than unique identifiers and
available more often than people expect — if every row already carries a user id, the
application has done the work for you.

**Write the decision down, in the suite, in prose, before the first test** — what the strategy
is, what it therefore forbids, and what it costs. A paragraph is enough. Say the growth cost
out loud, because it is invisible until it is not: a suite run ten thousand times in a
mutation campaign needs a reset between campaigns.

## Helpers — grow them, do not design them

Tests should read as behaviour rather than plumbing, and helpers are how. But a helper
surface designed before the tests exist is a guess, and it is a guess every later test has to
live inside.

**The rule: hand-roll the first two tests. Extract a helper only when a third test needs the
same thing.** No helper should exist that fewer than three tests use.

Applied honestly this produces a transport client and some way of attaching evidence to a
failure quite quickly, because nearly every test needs both — and it does *not* produce
entity builders for resources nobody has tested yet, or a data generator serving a builder
nothing calls.

The surfaces that tend to earn their place, in roughly the order they usually do:

- **transport** — a client that carries authentication, and an unauthenticated variant, so
  "this endpoint requires auth" is one line
- **evidence** — failures that attach the request, the response and the expectation. This is
  what makes a red test actionable to something that cannot set a breakpoint; a bare
  `expected 422, got 200` costs an agent an entire iteration to diagnose
- **state** — direct read access to what persisted, because *what the API returned* and *what
  was stored* are different claims and both matter
- **fixtures** — one call per common starting state. This is where the isolation strategy
  becomes the path of least resistance rather than a rule people remember: if
  `createCustomer()` generates its own unique name, a test author gets isolation by calling
  it and has to work to lose it
- **seeded randomness** — a single generator, seeded per run and recorded

That is a menu, not a checklist. Build each one the third time you reach for it.

## Proving it

Prove these yourself, because nothing else will:

- [ ] **Runs green against an unmodified checkout.** A harness that has never been green is
      not a harness. One real test is enough — but it must exercise the real interface and
      reach the database, because a readiness probe answering proves neither.
- [ ] Break one line of the application deliberately: exits `2`, and `failed` names the right
      test.
- [ ] Make the application fail to start: exits `1`, not `2`.
- [ ] Run a single test file alone and then in the full suite: same outcome. If not,
      isolation is broken — and this is the failure that costs the most later, discovered
      weeks after tests started being trusted.

`slipway doctor` independently checks the mechanical half: that the record appends rather than
truncates, carries `outcome` and `failed`, gives the same answer twice, honours `APP_DIR` and
`<PREFIX>_RECORD_DIR`. **Do not hand-verify what doctor
verifies.** It costs an application boot each time, and an independent checker stops being
independent once the harness author has rehearsed against it.

## Non-goals

- **Not the tests.** Scenario design is `behavioural-stress`. This is the machinery.
- **Not CI configuration.** One command with honest exit codes is what CI needs; anything
  else is that platform's concern.
- **Not performance measurement.** Duration is recorded because it is useful, not as a budget
  to assert on. Timing assertions in a behavioural suite fail for reasons unrelated to
  behaviour.
- **Not a substitute for the application's own tests.** This runs the application as a black
  box, over its real interface, against a real database.
