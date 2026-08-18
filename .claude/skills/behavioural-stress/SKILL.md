---
name: behavioural-stress
description: "Author behavioural test suites that stress the system under test, not just prove the happy path. Two modes: SPEC mode writes tests for behaviour that does not exist yet, from a specification; CHARACTERISATION mode writes tests for behaviour an existing application already has, by probing the running app. Use this skill whenever the user asks for behavioural tests, acceptance tests, integration tests, a test suite, characterisation tests, tests for a brownfield app, or 'tests for feature X' — especially when those tests are meant as a guard rail for trusting the code rather than a quick sanity check. Also use when the user says 'stress tests', 'adversarial tests', 'tests that catch real bugs', 'pin down current behaviour', or talks about the test suite as something a reviewer would rely on. Generic across languages, frameworks and harness shapes — this skill designs the scenarios and invariants, the author adapts them to their stack. Authoring only — does not run tests, does not iterate on red/green, does not replace code review."
---
# Behavioural Stress

Design behavioural test suites that *earn trust*. A test suite that only asserts the happy path is a floor, not a ceiling — and on a system anyone depends on (ledgers, payment rails, auth, anything with shared state), the floor is not enough. A reviewer reading "all green" should have caught the real bugs because the suite looked for them.

This skill helps author those suites. It designs scenarios and invariants adversarially. It does **not** run tests, does **not** pick a framework, and does **not** replace code review.

## Two modes — establish which one you are in

**SPEC mode.** The behaviour does not exist yet. A specification says what it should do, and the suite is written against that. The suite is red until the feature is built.

**CHARACTERISATION mode.** The behaviour already exists and nobody wrote it down. The suite describes what the application *currently* does, and every test must be **green on first run**. This is brownfield work: legacy migration, or pinning down existing behaviour before changing it.

The two modes have opposite failure signals, so mixing them silently is the most expensive mistake available here. In SPEC mode a red test is expected. In CHARACTERISATION mode a red test means *the test is wrong*, never that the app is.

**The mode is an input, supplied by whatever invokes this skill.** Do not ask for it.

If it genuinely was not supplied, determine it rather than asking: exercise the behaviour against the running application. If it is already there, this is CHARACTERISATION. If it is not, this is SPEC. That probe is more reliable than an answer would be, because it also tells you what the current behaviour actually is.

## The mandate

When the user asks for a test suite under this skill, hold three things in mind throughout:

1. **Happy-path tests are the floor.** A feature's suite is incomplete if it only proves the spec's stated behaviour on a single well-behaved run. If the draft looks like a series of "user does X, system responds Y" scripts and nothing else, push back — name the categories below that are missing and ask whether they apply.
2. **Think adversarially.** For every mutation, endpoint, or operation, ask: what breaks this under concurrency? What happens on retry? What happens at the boundary of a limit? What state was the data in when the call arrived? What if the caller rings the bell in the wrong order? The test author's job is to try to break the thing, not to confirm it works.
3. **Invariants are what give scenarios teeth.** A scenario that mutates state but asserts nothing afterwards catches almost no bugs. Every feature needs a small set of global properties — checkable against persistent state or externally-visible output — that must hold regardless of what the scenarios did. Scenarios drive traffic, invariants catch the damage.

## Characterisation mode

### The rule that makes generated tests safe

**Never write an expectation you have not observed.** Call the endpoint against the running application, look at what came back *and* at what changed in persistent state, then encode that. Not "what should this return" — "what did it return".

**Every characterisation test must be green on its first run.** This is not a quality target, it is the validation mechanism. A characterisation test that passes against the base application is, by construction, a faithful description of that application. You cannot write a *wrong* one that goes green.

That collapses the risk from "silently wrong" to "visibly incomplete", which is a far easier problem. It also means generated characterisation tests are trustworthy in a way generated spec tests are not.

When a characterisation test comes back red: **fix or discard the test.** Never change the application to make it pass. The red is telling you the test is wrong — a bad fixture, a wrong payload, missing auth, or an assertion about a state the application cannot actually reach.

### Write current behaviour even for endpoints about to change

Counter-intuitive but load-bearing. A test written directly against future behaviour is unfalsifiable until the feature exists: it is red from birth and you cannot tell whether that is the missing feature or a broken test.

Writing it against current behaviour first, and confirming it green, proves the plumbing — fixtures, authentication, payload shapes, reachable states — before anyone relies on it. Flipping the assertion afterwards is then safe, because the only thing that changed is the expectation.

### Characterisation captures bugs as faithfully as features

The application's current behaviour includes its defects. A faithful suite will assert them, and once asserted they become "required behaviour" — so a later fix reads as a regression.

Mark them. Any behaviour that looks wrong gets a third state alongside pass and fail: **known-wrong** — asserted so it cannot change silently, flagged so that changing it deliberately is not scored as a regression. Surface every one of these to the user rather than encoding it quietly; this is the single highest-value thing a human reviewer does with the output.

### What generation is bad at

Left alone, generation writes what is easy to observe: status codes, response bodies, the obvious happy path. It under-serves three things, so supply them explicitly:

- **Persisted state.** Assert what changed in the database, queue, or event log — not only what the response said. Reported values and actual effects diverge, and that divergence is exactly the class of bug worth catching. (A real case: a preview endpoint reported 5, an apply endpoint reported 5, and 2 rows actually changed. A suite asserting only the two reported numbers would have called that correct.)
- **State combinations.** See the category below.
- **Awkward setup.** Scenarios needing an unusual prior state get quietly skipped unless named.

## Output shape

Produce **three artefacts**, in this order:

1. **Invariants** — global properties that must always hold for this feature. Each invariant has an id, a one-sentence description, and a concrete check (what to query, what's a violation). Examples: "no two accounts share an owner_id", "the sum of all transaction amounts for an account equals its balance", "every state-change event has a matching state in the aggregate table", "same idempotency key always returns the same response body and status". Invariants are the things you'd keep checking even after the scenarios have run — they describe *state*, not *behaviour*.

   Not every domain has strong invariants. Ledgers have conservation laws; a CRUD application may have only ownership and referential rules ("every category on a transaction belongs to the transaction's owner", "split parts sum to the parent amount"). Say so if the domain is thin here rather than inventing weak ones — three sharp invariants beat ten vacuous ones.

2. **Scenarios** — grouped by the categories in the next section. Each scenario has a name, a setup, a sequence of operations, and an explicit assertion about the outcome (including which invariants it expects to hold). Name scenarios so a reviewer skimming the list understands what each one is trying to break — not just "test_open", but "open.concurrent_same_key.returns_identical_response".

3. **Coverage checklist** — a short table the author fills in per mutation, with a tick or a "not applicable" and a reason. Forces the author to decide consciously rather than by omission.

## Scoping invariants

Every invariant is one of two kinds, and naming them separately matters — more than it sounds like it should.

- **Feature-local.** Asserts properties of rows / events the feature itself produces. Lives with the feature, moves with it, dies with it. Prefix the id with the feature name (`deposit.amount_cents_positive`, `account.unique_owner`).
- **Cross-feature / global.** Asserts properties of state *any* feature can mutate — balances, conservation laws, event ordering across aggregates, type allowlists. Prefix with a non-feature name (`ledger.*`, `cross.*`).

The most common authoring failure is a cross-feature invariant wearing a feature-local id. It passes in the world where only the authoring feature exists, then silently becomes wrong when another feature lands and mutates the same state — "silently" because the existing scenarios never produce the new mutation and the invariant keeps returning green. By the time the gap fires, the failure looks like an app bug rather than a stale test.

**Diagnostic question when writing an invariant:** "If a future feature adds a new row / event / status / transaction type that also touches this state, does my invariant still hold without modification?" If yes, the invariant is genuinely feature-local. If no, the prefix must be cross-feature, and the invariant must be written with that lifecycle in mind (typically an explicit allowlist — see below).

### Trip-wire invariants for exhaustive lists

When a cross-feature invariant has an exhaustive `CASE`, a signed-type list, a status enum, or any other set of known values, add a **companion invariant** that fails on any value *outside* the allowlist. Two invariants, not one:

1. The main invariant — asserts the conservation / consistency property for values in the known set.
2. The sentinel — asserts no value outside the known set exists.

When a future feature introduces a new type without updating the allowlist, the sentinel fires *first*, with a clear message: "unknown type X found — extend the allowlist, then the main invariant's branch for X, then re-run". That turns the most common drift mode (silent omission) into an immediate, specific failure with an obvious fix.

Don't write a main invariant with an exhaustive branch and *no* sentinel. That's the trip-wire that burned a previous feature-addition cycle — a deposit-only signed-sum invariant kept passing through the deposit+withdrawal era, then silently broke the moment interest materialisation added `interest_credit`/`interest_debit` rows that mutated balances outside its branch.

## Categories to cover

For every mutating operation, endpoint, or lifecycle transition the feature exposes, walk through these categories. Don't silently skip one. If a category genuinely doesn't apply, say so and say why.

### State combinations

This category is about *what state the data is in when the call arrives*, as distinct from *how the call is made*. It is the one most often missed, because the other categories all concern the shape of the request rather than the shape of the world.

- **Enumerate the dimensions the code branches on.** Every `if` in the path under test names one: a status enum, a nullable field, an ownership relation, the presence of children, whether a value already equals the one being set.
- **Cross them, then cover the interesting cells.** Not every cell — the ones where behaviour should differ, plus every cell where two dimensions interact.
- **Pay attention to "already in the target state".** The most commonly missed cell is the one where the operation would produce no visible change. Systems routinely report having done work they did not do.

A worked failure: a rule-application path branched on `status ∈ {UNCATEGORIZED, RULE_BASED, MANUAL, FAILURE}` and on whether the transaction's category already equalled the rule's. Eight cells; the suite covered three. The uncovered `FAILURE × already-matching` cell hid a real defect — two independent implementations, both green, only one correct. Drawing the table takes five minutes and needs no cleverness.

**Caveat, and it matters in characterisation mode:** deriving dimensions from the existing code inherits that code's blind spots. A dimension the code *should* branch on but does not will never appear in the table. This technique describes what is; it does not discover what is missing.

### Concurrency

- **N parallel identical requests** — same input, same idempotency key (if applicable), fired simultaneously. Assert exactly one state change and identical responses.
- **N parallel conflicting requests on the same resource** — e.g. two concurrent closes on the same account, two concurrent transfers debiting the same balance. Assert one wins cleanly, others get a deterministic error.
- **Interleaved lifecycle operations** — suspend and reactivate firing in rapid alternation, open and close racing, reads happening mid-mutation. Assert final state is internally consistent.

### Retry and idempotency (where the system claims idempotency)

If the system makes no idempotency claim anywhere, say so once and mark the whole category not-applicable rather than inventing a contract the application does not offer.

- **Same key + same body** — must return the identical outcome (same status, same body), not re-execute.
- **Same key + different body** — must be rejected explicitly (typically 422). The key is bound to the request, not a free pass.
- **Concurrent retries with the same key** — N parallel requests with the same key and same body, fired simultaneously. All N responses must be byte-identical, and exactly one state change must occur. This tests the idempotency store itself (the race between "execute the operation" and "record the outcome"), which is a distinct layer from any DB-level protection on the underlying resource. Sequential same-key retries do not exercise this race; they pass as long as the first call has fully committed before the retry arrives.
- **Retry after apparent success** — the caller got a 2xx, but retries anyway (network glitch, client crash). Must not duplicate side effects.
- **Retry after apparent failure** — the caller got an error or timeout, retries. Must be safe to re-run; the eventual state must be consistent with exactly-one or zero executions, never partial.
- **Retry across the validity window** — if idempotency keys expire, test at the boundary: just before expiry (stored outcome), just after (treated as fresh).

### Ordering

- **Out-of-sequence lifecycle calls** — reactivate before suspend, close before open, two closes in a row. Assert each rejection is explicit and does not corrupt state.
- **Operations in the wrong aggregate state** — withdraw from a closed account, transfer from a suspended account, interest accrual on an account that was closed mid-cycle.
- **Operations before creation or after termination** — acting on an id that has never existed; acting on one that was just closed/deleted.

### Boundary values

- **Zero and negative** where not expected.
- **Min and max of the underlying type** — especially for `int64` money fields: what happens at `INT64_MAX`, what happens just before overflow, what happens at `INT64_MIN`.
- **The exact threshold of any limit** — overdraft at `-€500.00` exactly (allowed), at `-€500.01` (rejected). Both sides of every numeric threshold.
- **Off-by-one on time windows** — idempotency at 23h59m59s vs 24h00m01s; rate limits at the last allowed request vs the first denied one.

### Partial failure (where the harness supports fault injection)

- **Crash between commit and response** — DB row written, client never sees the 2xx. Client retries; assert no duplicate side effects.
- **Connection drop mid-operation** — pool loses the connection between two queries in the same transaction. Assert rollback is clean.
- **Timeout during a multi-step flow** — step 1 commits, step 2 times out. Assert the state is either fully-applied or fully-absent, never half.

If the current harness does not support fault injection, **say so explicitly** rather than silently omitting the category. The user needs to know what they're *not* testing so they can decide whether to invest in fault-injection tooling separately.

**Fault injection asserts behaviour, not wall-clock budgets.** A fault-injection test is a behavioural test — it forces a specific race, rollback, or retry path and asserts the resulting state. It is *not* a performance test. Keep two guardrails in mind:

1. **Injected latency must stay well below the harness's HTTP client timeout.** If you inject enough latency that a single request can't complete before the test client aborts, the failure you observe is "fetch timed out / truncated body", not the behaviour under test. That's a silent perf assertion — a future, behaviourally-correct refactor that adds one more query will fail this test for reasons unrelated to what the test claims to prove. Sub-client-timeout latency (enough to *force* serialisation or overlap) is plenty; more than that is a smell. If the only way to force the race is large latency, prefer concurrency primitives (`Promise.all`, barriers) over latency.
2. **Never assert "operation completed within M ms".** Wall-clock bounds belong in a separate perf suite, not a guard-rail behavioural suite. Assert on persisted state, response bodies, and event rows — things that would still be wrong six months from now regardless of how fast the DB happens to be.

Similarly, **pool-exhaustion / load-shape tests are perf tests** wearing a behavioural hat. "N parallel requests under K ms latency return sensible outcomes" is testing pool sizing and latency budgets; neither is a behavioural property of the feature. If you need to prove that concurrent writes don't corrupt state, write a test that fires concurrent requests against a normal DB and asserts the persisted state — that's the behaviour. Latency is incidental.

## Behavioural tests are blind to cost

A behavioural suite bounds behaviour. It says nothing about response time, query count, or memory. An implementation that is behaviourally perfect and operationally far worse passes silently, and nothing in a green report hints at the difference.

Do not fix this by adding timing assertions — that is the fault-injection mistake in another costume. Note it as a known limit of the suite, and if it matters, put it in a separate performance suite with its own thresholds.

## The feature as a suite diff

When a suite already characterises current behaviour and a new feature changes some of it, the specification of that feature **is the diff to the suite**. Flip every test the feature must invalidate — `201` becomes `422`, in each place it applies — and no prose spec is needed.

Two consequences worth stating to the user:

- Every flipped test is a deliberate decision, so the diff doubles as a reviewable list of exactly which behaviours are being changed. Anything not in that list must still hold.
- You then know precisely which tests should be red before implementation starts. If anything *else* goes red, the predicted blast radius was wrong — and that is worth knowing before any implementation effort is spent.

## Coverage checklist

After producing scenarios and invariants, emit a checklist the author can tick off. One row per mutation. Suggested columns:

| Mutation | state-combinations | concurrent-same-key | retry-same-key-same-body | retry-same-key-different-body | concurrent-different-keys-same-resource | out-of-order-state | boundary-at-limit | partial-failure |
| -------- | ------------------ | ------------------- | ------------------------ | ----------------------------- | --------------------------------------- | ------------------ | ----------------- | --------------- |

Mark each cell as covered (with the scenario id), not applicable (with a one-line reason), or gap (the category applies but isn't yet written). Gaps are fine — they're the starting point for the next round of work. What's not fine is cells left blank because the author didn't think about them.

## Pushing back on happy-path drafts

If the model catches itself producing a draft that reads like "open succeeds, suspend succeeds, close succeeds, the end" — stop. The skill is not doing its job. Re-open the categories above and ask: which of these applies to each mutation? For every one that applies, the draft needs a scenario or a justified "not applicable".

Happy-path tests are worth keeping as sanity checks. They are not worth *shipping on*.

## Establishing the surface

This skill runs unattended. Determine each of the following from the codebase, the schema and the running application. Do not ask.

- **Which operations mutate state.** These drive almost all the scenarios. Find them in the routes and the service layer.
- **Which code paths write the data this behaviour constrains.** Ask it as a write-set question — "what writes this field" — not as "which endpoints are about X". The first has a mechanical answer; the second is a judgement call, and it under-reports.
- **Whether the system claims idempotency, and where.** If nothing in the codebase implements an idempotency store or honours an idempotency header, it makes no claim. Mark the category not-applicable and move on.
- **Which invariants hold.** In SPEC mode, extract them from the specification rather than inventing them. In CHARACTERISATION mode there is no specification — derive candidates from the schema's constraints (foreign keys, uniqueness, not-null, check constraints) and from what the application demonstrably enforces.
- **What the harness supports.** Parallel requests? Fault injection? This decides which categories are authorable now and which get recorded as parked.
- **Explicit limits, thresholds and time windows.** These drive the boundary-value scenarios, and they are usually literals in the code.

When something genuinely cannot be determined, record it as an explicit gap in the coverage checklist with the reason. A stated gap is useful output; a silent omission is not.

### How tests coexist — establish the strategy before writing anything

A suite that accretes across features usually shares one long-lived database and one application process. The isolation strategy dictates what an assertion may say, so settle it before the first test.

**If the harness already states one, follow it** — it will be written down in the suite, or visible in what the fixtures do on setup and whether anything runs on teardown. **If nothing states one, you are choosing it**, and that choice binds every test written afterwards: say which strategy, what it forbids, and what it costs, in prose, in the suite, before writing tests. Do not leave it implicit for the next author to infer.

The common strategies, and what each forbids:

| strategy | what it means | what you must not do |
|---|---|---|
| **Unique identifiers** — no cleanup at all | Every test creates its own entities under randomly generated names, and asserts only on ids it created. Data from every previous test and every previous run is still present. | Assert on global counts, "the only", "the first", or list endpoints without filtering to your own marker. Assume an empty starting state. |
| **Tenant-scoped** | Every test registers its own user or tenant and the application scopes rows to it. Stronger than unique identifiers, and available whenever every row already carries an owner. | Read across tenants, or assume another tenant's data is absent rather than merely invisible. |
| **Transactional rollback** | Each test runs in a transaction that is rolled back. | Assume writes survive the test, or that a second connection (the application's) can see them. Rules out most black-box HTTP harnesses. |
| **Truncate between tests** | State is reset per test. | Run tests in parallel against the shared database. |

Under the first two — the most common for black-box HTTP suites, because they are the fastest and the only ones that work when the application owns its own connections — **isolation is a property of the fixtures, not of any cleanup step**. Where helpers exist, use them rather than hand-rolling entities: if `createCategory()` already generates a random name, calling it gives you isolation for free, and building the payload yourself quietly removes it.

**Where they do not exist yet, do not invent a helper surface up front.** Hand-roll the first two tests and extract a helper only when a third needs the same thing — a fixture written before three tests want it is a guess that every later test then has to live inside. The first extraction is usually the transport client and a way of attaching the request and response to a failure, because nearly every test needs both.

Two consequences worth stating explicitly, because both produce tests that pass today and fail later for reasons unrelated to the behaviour:

- **A test that asserts on a global count is order-dependent and run-count-dependent.** It will pass in isolation and fail in the suite, or pass today and fail after fifty runs. Scope every read to the entities the test created.
- **The database grows without bound.** That is an accepted trade for speed, not an oversight — but it means the suite's runtime drifts upward over its life, and campaigns that run it thousands of times (mutation testing) need a reset between campaigns. Say so in the report rather than discovering it later.

Then produce the three artefacts. Keep scenario names descriptive — a glance at the list should tell a reviewer what's being stressed. Keep invariants small in number but precise; five sharp invariants beat fifteen vague ones.

## Non-goals

State these up front if the user seems to expect otherwise:

- **No execution.** This skill does not run tests, does not invoke verify/CI, does not iterate on red/green. It authors the suite; the author integrates it with their harness and runs it themselves.
- **No framework choice.** This skill gives generic scenarios and invariants. Adapting them to pytest vs JUnit vs node:test, to a black-box harness vs an in-process one, to a SQL invariant check vs an event-stream invariant check — that's the author's call.
- **No substitute for review.** A stressed suite reduces the surface of bugs humans need to catch, but it never eliminates that surface. In characterisation mode this is sharper still: review is what turns a *description* of the application into a *specification* for it, and nothing else does that job.
- **No discovery of what was never there.** Both characterisation and state-combination analysis describe the system as built. Behaviour the application should have and does not will not appear.

## Style

- British English.
- Direct. Push back on drafts that are thin. The user is asking for a guard rail; a thin suite isn't one.
- Explain the *why* of each category the first time it's introduced in a given session — the categories are not rote, they correspond to real bug classes, and the author is more likely to adapt them well if they understand the motivation.
