## Your task

Edit the behavioural suite so that it states the change below. You are in SPEC mode:
the behaviour does not exist yet, so the tests you write and change are **red on
purpose**. Do not touch the application.

Application under test: {APP_DIR}
Suite being specified: {SUITE}

## The change

{SPEC}

## What you will be judged on

A reviewer decides whether this diff states the change, against the standard below. It is
the same text they are given — you are not being asked to guess it.

{CRITERIA}

**`constrained` is not a licence to restate the rule.** A surface marked `constrained` in
`SCOPE.yml` was described deeply because the rule governs it, not because this change
must say something new there. What you may state is decided by the judged findings: a `change`
verdict, and nothing else.

## Where a new test goes

`{PAPERS}/SCOPE.yml` names the surfaces this change touches. **File every test you add
under its surface's key**, turning the dots into directories: `items.creation` means
`{SUITE_DIR}/items/creation/`. The tests already there are filed that way, and the
directory a test sits in is how it is traced back to the behaviour it describes.

The change lands on the surfaces marked `constrained`. If what you are stating genuinely
belongs to none of them, say so in your report rather than inventing a directory — either
the scout missed a surface or the specification reaches further than anyone thought, and
both are worth a person knowing.

## The judged findings decide what you may edit

`{PAPERS}/findings.yml` carries a verdict per finding, and it is a contract
rather than background reading. Read it before you edit anything.

- **`change`** — you *must* flip the tests it names in `pinned_by`. That flip is how the
  change gets stated.
- **`keep`** and **`defer`** — those tests are **protected**. Their names, their assertions
  and their expected values must survive your diff untouched. A `defer` is a bug someone
  decided not to fix now, and its test is what holds it in place until they do; a `keep` is
  behaviour someone decided is correct.

Only a `change` verdict authorises editing a test, and only the tests that verdict names —
check the `pinned_by` patterns rather than assuming a file is covered because a sibling in it
is.

**A protected test may still collide with your change.** It will use fixture data that the
new rule now rejects, and it will go red through no fault of its own. Do not weaken it,
rename it, or teach it about the new behaviour — that silently converts someone's `defer`
into a fix, and their `keep` into a change. **Move it out of the way instead**: give it data
that stays clear of the new boundary — a larger quantity, a different id, an amount below the
new limit — so every assertion it already makes still holds, unchanged, for the same reason
as before.

If a protected test genuinely cannot be kept green without altering what it asserts, stop and
say so in your summary, naming the test and the finding. That is a judgement for a person, not
one for you to make by editing.

## What to produce

- **Flip** the tests the change invalidates, so they assert the new behaviour.
- **Add** tests for what the change introduces.
- **Add** tests for what must *not* move — the behaviour adjacent to this change that
  a careless implementation would break.

The application is at `{APP_SUBDIR}` and the suite at `{SUITE_DIR}`, relative to your
working directory. Run the suite with `{VERIFY_CMD}` — it starts the application, runs the
tests against it and stops it again; never start the application yourself. How to reach it,
how to authenticate, and the conventions the existing tests follow are yours to discover.

Every test you leave green must still be green — but green *for the reason it was already
green*, not because you rewrote what it checks. Every test you flip or add should be red, and
you should be able to say which and why: that diff is the specification.
