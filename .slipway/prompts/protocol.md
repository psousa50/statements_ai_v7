## How to work

TODO — this file is app-specific. Describe how a builder should work in *this*
repository: how to start the application, where the tests live, what it may and
may not touch.

The behavioural suite is the oracle. You may run it, you may not read it, and you
may never edit it.

Run the suite with the verify command configured for this repository. Iterate
until it is green.

## The suite keeps a record — leave it where it is

Every run of the verify command appends one line to a record of what happened:
when it ran, the outcome, and which tests failed. The location is already set for
you in the environment, and it is already **outside** the repository you are
working in, so running the suite leaves nothing behind in your working tree.

**Do not set that variable yourself.** Passing your own directory — a scratch
path, somewhere under `/tmp` — sends your runs somewhere nobody reads, and the
record of your work is silently lost. It is a tidy instinct and the untidiness it
avoids does not exist here.

The record is not a check on you. slipway runs the suite itself once your work is
done, and that run alone decides whether the change is good. Yours is a second,
independent observation of the same code — and when the two disagree, that is how
a flaky test gets caught instead of being blamed on your implementation. Keeping
your runs visible protects your work, not the tool's.
