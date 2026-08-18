## Your task

Do not change any code. Read the repository and predict the surface this change
will touch.

The application is at `{APP_SUBDIR}`, relative to your working directory. Read it.
Everything else — its entry points, its layers, where state is written — is yours to
discover.

Produce a report saying:

- **X** — what the specification constrains.
- **Y** — what that constraint depends on.
- **Writers** — every code path that writes X or Y, including scripts and bulk
  operations, not only the obvious endpoint.

Tier each finding T1 (certain), T2 (likely), T3 (possible). If the specification
contradicts what the application actually does, say so before anything else — a premise
nobody checked is worth more than a tidy report.

## And write the surfaces as a file

Write `{SCOPE}` — **that absolute path exactly**, not a relative one, because your
working directory is not necessarily what you assume and a file written one directory
away is a file nobody reads. Every step after this one is scoped by it.

```yaml
surfaces:
  - key: items.creation
    does: "one line — what a user of this application can do here"
    reached_by: ["POST /items", "POST /items/import"]
    role: constrained
    tier: T1
    proposed: false
    why: "one line"
```

`role` decides how deeply the next step describes each surface, so it is the field to
think hardest about. The test is **what the change's rule governs**, not what its code
touches:

- **`constrained`** — the rule this change states governs what this surface may do.
  **Whether or not it already obeys it.** A surface that complies today is the one most
  likely to regress quietly, and describing it thinly is how that goes unnoticed.
- **`depends_on`** — the rule does not govern it, but it shares state or machinery with
  something that does, it is how the change is observed, or the specification freezes it.

Do not ask *will this surface's behaviour change*. That question splits a rule across the
surfaces it governs according to which of them happen to be buggy today — and if two ways
into one surface disagree, you would describe only the broken one.

Name both roles. What a change must not break is as much of its surface as what it alters.

`reached_by` is every way this surface can be reached from outside — an HTTP method and
route, a CLI invocation, an exported function, a message type: whatever this application
actually exposes. **Always a list**, even of one. Every free-text value is **always a
quoted string**: several of them naturally begin with a quotation mark or contain a
colon, and one unquoted value makes the whole file unreadable.

## What a surface is

Something **observable from outside** — a thing the application can be asked to do, and
whose behaviour a test could describe by talking to the application rather than by
importing it. Not a function, a module or a line of code; those belong under
**Writers**, where they already are.

Two rules, and they are where the judgement is:

- **A surface may be reached more than one way.** If two entry points let a user do the
  same thing, that is one surface with two entries in `reached_by`, not two surfaces. A
  rule enforced at one and forgotten at the other is exactly what this catches.
- **One way in may serve more than one surface.** If a single entry point lets a user do
  two different things, say so — the same entry under two keys.

Group them the way the application behaves, not the way its routing table is written.

## And the claims that belong to no single surface

Some behaviour is not a surface and never will be. *available always equals quantity minus
reserved* is written by creating, restocking, reserving and releasing, and belongs to none of
them. It is not **reached**; it is **violated**. Left out, it is described nowhere and nothing
reports its absence.

So `{SCOPE}` takes a second block, beside `surfaces:`:

```yaml
invariants:
  - key: stock.availability
    about: "how available stands to quantity and reserved"
    over: [items.creation, items.restock, items.reserve, items.release]
    observed_by: [items.read]
    proposed: false
    why: "one line"
```

- **`over`** — the surfaces that can move it. **Every one must appear in your `surfaces:`
  list**, at least as `depends_on`, and there must be **at least two**: something that
  governs a single surface is that surface's behaviour and belongs to it.
- **`observed_by`** — the surface a test **watches it through**. An invariant has no address
  of its own, so without this a test has nothing to look at.
- **No `role`.** slipway works out how deeply to describe an invariant from the roles you
  gave the surfaces it spans. You do not decide it and cannot override it.

`over` and `observed_by` name **surface keys, never addresses**. An invariant describes no
ground of its own — it is a relation between ground already described.

**`about:`, not "should".** Say what the relation *is between*, not what it ought to be. The
next step describes what the application actually does with it, and on many applications the
answer is that the relation does not hold. That is a finding, not a failure.

Two or three is usually right. If you find yourself writing one per surface, they are not
invariants.

## Names are the point, so reuse them

`{SURFACE_MAP}` is this application's surface map, if it exists. **Read it before you
name anything.** It grows one change at a time and is expected to be incomplete.

It holds both kinds — `surfaces:` and `invariants:` — and the keys share one namespace, so
one key never names both.

**Reuse an existing `key` whenever one already covers what you are describing**, even if
you would have worded it differently. These keys are how a description written today is
found again in a year, so a near-duplicate under a new name is worse than an awkward name
kept. If an existing surface covers your ground but its `reached_by` is incomplete, add
the missing way in to that surface rather than creating another.

Invent a key only for something genuinely not there yet, and mark it `proposed: true`.
