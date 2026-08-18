## Your task

Cross the state combinations this code branches on into a table, mark every cell
that the suite already covers, and fill the interesting empty ones.

Application under test: {APP_DIR}
Suite being extended: {SUITE}

The application is at `{APP_SUBDIR}` and the suite at `{SUITE_DIR}`, relative to
your working directory. Run the suite with `{VERIFY_CMD}`. Which state dimensions
matter is yours to discover from the code the suite exercises.

This is still characterisation: every new test must be green against the
unchanged application. Write the table to `{PAPERS}/gaps.md` and append
new findings to the two findings files beside it.

## Cross the surfaces the change governs, and only those

`{PAPERS}/SCOPE.yml` names the surfaces this change touches, and `role` says which
matter here.

- **`role: constrained`** — the rule governs this surface. Cross its state dimensions
  and fill the interesting cells. **Cross them against each *way in* as well**: a
  surface reached two ways may behave differently at each, and a cell filled at one
  address says nothing about the other.
- **`role: depends_on`** — leave it alone. It already has enough tests to notice if it
  moves, and a state matrix over behaviour the specification freezes buys nothing.

A surface named nowhere in that file is out of scope. Do not cross it, however
interesting its state space looks.

**File every test under its surface's key**, turning the dots into directories:
`items.creation` means `{SUITE_DIR}/items/creation/`. The directory a test sits in is
how it is traced back to the behaviour it describes.

Your table in `{PAPERS}/gaps.md` is **one section per constrained surface**, naming the
dimensions you crossed and which cells you filled — that record is what tells the next
change what has already been explored here, so write it for someone who was not present.

Every finding names what it belongs to, on a `describes:` line in `findings.yml`, using the
key exactly as it appears in `SCOPE.yml`.

## Cross the invariants too

An invariant is a relation several surfaces write and none owns. slipway has worked out which
are in scope and which surfaces each is crossed against:

{INVARIANTS}

Give each one **its own section in `gaps.md`**, naming the dimensions you crossed and the
cells you filled, exactly as you do for a surface. The dimensions of an invariant are the
orderings and magnitudes of the writes that move it — write then over-write, a large figure
after a small one, one surface's write following another's — crossed only over the surfaces
named against it.

This is still characterisation: every new test green against the unchanged application. Where
the relation does not hold, the test says so and stays green.

**Those paths are absolute.** Write to them exactly as given — do not shorten them to a
relative path; findings written one directory away from where slipway looks are
findings nobody reads.

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
