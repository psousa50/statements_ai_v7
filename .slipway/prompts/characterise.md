## Your task

Describe the *current* behaviour of this application as behavioural tests. Do not
change the application. Never write an expectation you have not observed.

Application under test: {APP_DIR}
Suite being characterised: {SUITE}

The application is at `{APP_SUBDIR}` and the suite at `{SUITE_DIR}`, relative to
your working directory. Run the suite with `{VERIFY_CMD}` — it starts the
application, runs the tests against it and stops it again; never start the
application yourself. How to reach it and how to authenticate are yours to
discover.

Every test must be green against the unchanged application. Record each surprising
behaviour in `{PAPERS}/findings.md` with an id, and add one `decision: pending` entry
per id to `{PAPERS}/findings.yml`.

## The surfaces decide what to describe, and how deeply

`{PAPERS}/SCOPE.yml` names the surfaces this change touches. It is the scope of this
step. Read it first.

**File every test under its surface's key**, turning the dots into directories:
`items.creation` means `{SUITE_DIR}/items/creation/`. One surface, one directory. That
path is how a test is traced back to the behaviour it describes, so a test filed
anywhere else belongs to nothing.

Two depths, and `role` decides which:

- **`role: constrained`** — the change lands here. Describe it **exhaustively**: every
  input class it accepts and refuses, every boundary, what it leaves unchanged when it
  refuses, and how it behaves **at each address**, since two reached_by reaching one
  surface may not agree with each other.
- **`role: depends_on`** — the change must not disturb it. Describe only **enough to
  notice if it moves**: its ordinary behaviour and whatever it already refuses. Not its
  edges. A handful of tests.

A surface named nowhere in that file is **out of scope for this step**. Do not describe
it, however interesting it looks. If you believe the scout missed a surface the change
genuinely touches, record that as a finding and leave it undescribed — that is a
judgement for a person, not a reason to widen the step.

Every finding names what it belongs to, on a `describes:` line in `findings.yml`, using the
key exactly as the scout wrote it.

## The invariants in scope

Some behaviour belongs to no single surface — a relation between things several surfaces
write. slipway has already worked out which of them this change reaches, and which surfaces
each is to be described across. **That list is complete: do not widen it, and do not invent
an invariant that is not on it.**

{INVARIANTS}

Describe each one **only across the surfaces named against it**. The other surfaces it spans
are set-up on the way to observing it — reach for them to construct a state, not to explore
their own edges, which the roles above have already settled.

**Never write an expectation you have not observed** applies here hardest. These relations are
where an application is most often quietly wrong, and your job is to say what it does, not
what it ought to do. If the relation does not hold, that is the finding — write the test that
shows it holding false, green, and record it.

**Those paths are absolute.** Write to them exactly as given — do not shorten them to a
relative path, because your working directory is not necessarily what you assume, and
findings written one directory away from where slipway looks are findings nobody reads.

## Where the application ends

Test the application, not the stack it runs on. The line is not where the network
is — it is **whose code decides the answer**.

Ask it of every assertion you are about to write: *if I changed nothing in this
application, could this still break?* If a runtime upgrade, a different server
library or a different operating system could change the answer, you are pinning
somebody else's behaviour and the suite will fail for reasons no one here caused.

Do not assert:

- **error pages, phrases or status codes the framework produces on its own**, for
  requests the application never sees — an unrouted method, an unparseable request,
  a malformed protocol frame. Their wording belongs to the library and changes
  with it.
- **connection framing, keep-alive, teardown or socket-level behaviour.** Whether a
  connection closes cleanly or is reset is decided by the server and the kernel,
  it is timing-dependent, and a test that pins which way that race resolves will
  be flaky — it will pass when you write it and fail once in a hundred runs
  afterwards, failing correct work.
- **the shape of a response the application did not construct.**

Do assert anything the application's own code decides: what it accepts, what it
rejects and with which status *it* chose, what it stores, what it returns, what it
leaves unchanged when it refuses.

A defect that lives at that boundary is still worth **recording as a finding** —
"a chunked request is misread as an empty body" is real and someone should know.
Write it in `findings.md` in prose. Just do not pin it with a test that asserts
the library's error text or which side of a teardown race wins; pin the part the
application decides, and say the rest in the note.

## The two halves of the findings

Two files, one per finding, and slipway validates that they agree.

`{PAPERS}/findings.md` is prose — what you observed and how. One section per
finding, headed exactly:

```
### CAT-01 — every transaction writer accepts a root category · known-wrong
```

`{PAPERS}/findings.yml` is the machine-readable index. Every id in one must
appear in the other:

```yaml
suite: {SUITE}

findings:
  - id: CAT-01
    summary: every transaction writer accepts a root category
    describes: transactions.categorisation    # the surface or invariant key it belongs to
    known_wrong: true
    decision: pending          # you write pending; a human judges it
    pinned_by:                 # the test ids that hold this behaviour in place
      - transactions.categorisation.*
      - transactions.splits.split_parts_may_each_carry_a_root_category
    note: >
      anything a reviewer needs in order to judge it
```

`pinned_by` is not decoration. It is how a red test months from now is traced back to the
behaviour someone judged, so **every finding must name the tests that pin it** — exact ids,
or a prefix ending in `*`.

`decision` is always `pending` when you write it. Only a human sets `keep`, `change` or
`defer`.
