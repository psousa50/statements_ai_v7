- **Every `change` verdict is stated.** Each finding judged `change` must have its
  pinning test flipped, and the flip must say what should happen now.
- **Every `defer` verdict is untouched.** A deferred bug stays pinned green. A
  diff that quietly fixes one is out of scope, and that is a rejection.
- **Every `keep` verdict is untouched.**
- **The tests are behavioural.** They go through the application's real interface
  and assert on what it does. A test that reaches inside the implementation
  specifies the implementation, not the behaviour, and locks in one design.
- **The change is stated once.** Tests that restate the same rule against the same
  path add cost and no coverage. Tests that state it against a *different* writer
  are not duplicates — they are the point.
- **The negative space is covered.** What must *not* change is as much a part of a
  specification as what must. A diff that only adds happy paths lets a builder
  satisfy it by breaking something adjacent.
- **Nothing but the suite is touched.** Application code in this diff is a
  rejection outright.

A specification the application already satisfies states nothing. So does one that
asserts something no reasonable implementation could fail. If the diff would go green
against a builder that did nothing of substance, it states nothing — that is the single
failure this step exists to catch.
