## Your task

Do not change any code. Read this application and say **what it can be asked to do**.

The application is at `{APP_SUBDIR}`, relative to your working directory. Read it, and
run it if that settles a question — a behaviour you have observed beats one you inferred.

Write your answer to `{PROPOSAL}` — **that absolute path exactly**, not a relative one,
because your working directory is not necessarily what you assume and a file written one
directory away is a file nobody reads.

```yaml
reachable:
  - POST /items
  - POST /items/import
  - GET /items/{id}

surfaces:
  - key: items.creation
    does: bring an item into existence with a name and a starting quantity
    reached_by: ["POST /items", "POST /items/import"]
```

Two halves, and they must agree.

- **`reachable`** — every way into this application, one per line, whatever form its
  entry points take. Find them from the code: a route table, a dispatch chain, an
  argument parser, a set of exported symbols. This is the complete list, so the effort
  is in being sure it *is* complete.
- **`surfaces`** — what a user can do, grouped by behaviour. **Every entry in
  `reachable` must appear in some surface's `reached_by`**, and a `reached_by` naming
  something absent from `reachable` is a contradiction. slipway checks this, and
  reports anything left undescribed.

## What a surface is

Something **observable from outside** — a thing the application can be asked to do, and
whose behaviour a test could describe by talking to the application rather than by
importing it. Not a function, a module or a line of code.

Two rules, and they are where the judgement is:

- **A surface may be reached more than one way.** If two entry points let a user do the
  same thing, that is one surface with two entries in `reached_by`. A rule enforced at
  one and forgotten at the other is exactly what this catches, so look for the second
  way in rather than assuming the obvious one is the only one.
- **One way in may serve more than one surface.** If a single entry point lets a user do
  two different things, say so — the same entry under two keys.

Group them the way the application behaves, not the way its routing table is written.

## The keys are the point

These names are read by every later change to this application, and by people a year
from now. A key is a short dotted slug, lower case. Spend the effort here: a surface
whose name nobody recognises is one that gets described twice under two names.

`does` is one line, in the language of somebody using the application — not of its
implementation.

## What is already named

These surfaces exist, and you must **reuse them exactly** rather than re-word them.
Someone may have corrected their wording by hand; a key that moves is a description
nobody can find again.

{ESTABLISHED}

If one of them is reachable a way it does not yet list, add that way to it rather than
inventing a second key for the same behaviour.

## What this is not

Not a description of behaviour — that comes later, as tests. Do not say what the
application does *correctly* or *incorrectly*, what it validates, or what it returns.
Say only what it can be **asked** to do, and how you ask.

A defect you notice is worth mentioning in prose. It is not a surface.
