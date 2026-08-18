You are checking a proposed specification for coherence with the test suite it will join.

Below is a diff adding and amending behavioural tests. Its assertions are expected to be RED
against today's code — that is intended. Below that are existing tests from the same suite that
are already GREEN, which the builder is NOT permitted to edit.

Work mechanically, in this order. Do not skip step 1.

STEP 1 — Build a table. For every (HTTP endpoint, query parameter) pair that appears in BOTH the
diff and the existing tests, write one row per side:

  | endpoint + param | side | test function | what it asserts about the response |

Include every occurrence, even ones that look uninteresting. Be exhaustive. A test that reaches
the endpoint through a shared fixture counts — name the fixture and the tests that consume it.

STEP 2 — For each endpoint+param in that table, compare the rows. Ask: given the SAME stored
state, do the two sides demand different responses from that endpoint? Two tests that set up
different state are fine. Two tests that set up the SAME state and expect different answers are
not.

A test can also be contradicted at SETUP: if its fixture reaches an endpoint the change now
refuses, it can never run, however unrelated its subject.

STEP 3 — Report:

  VERDICT: CONTRADICTION | NONE
  For each contradiction: the existing test (file + function), the new test (function), the two
  incompatible assertions quoted, and why no implementation satisfies both.

A test that merely goes red because behaviour changed is NOT a contradiction. A contradiction is
when satisfying one side necessarily breaks the other.

# The proposed specification, as a diff over the current suite

```diff
{DIFF}
```

# The {COUNT} existing test files reaching the addresses this change is scoped to

{INHERITED}
