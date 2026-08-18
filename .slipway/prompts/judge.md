## Your task

Judge each finding. You are standing in for a person, and the
question you are answering is the one a person would answer: **does this
behaviour need to move for the change to be made?**

Task: {WORKFLOW}
Findings, in prose: `{PAPERS}/findings.md`
Findings, as data: `{PAPERS}/findings.yml`

The change being made is stated here, and it is the only thing that decides a
verdict:

{TASK_SPEC}

## The three verdicts

Every finding currently reads `decision: pending`. Replace each one with exactly
one of:

- **`keep`** — the behaviour is correct. Its pinning test stays as it is.
- **`change`** — the behaviour is wrong *and fixing it is part of this change*.
  Flipping its test is how the change gets stated. Use this only for behaviour a
  correct implementation of the sentence above must touch anyway.
- **`defer`** — the behaviour is wrong, but fixing it is a **different** change.
  The test stays green and pins the bug until someone picks it up.

`defer` is the right answer far more often than it looks. A bug you found along
the way is not part of this task merely because you found it. If you cannot say
which clause of the sentence above requires a finding to move, it is `defer`, not
`change`.

## What is required of you

- Read `findings.md` in full before deciding anything. The findings interact:
  several may be one behaviour seen from different angles.
- Read the code that produces each behaviour. A verdict formed from the
  prose alone is a guess.
- Every finding must end judged. `pending` is not a verdict and the run is
  refused while any remains.
- Every judged finding must name the tests that pin it in `pinned_by`, so a red
  test months from now traces back to a decision rather than to a grep.
- Write a `note:` on every `change` and every `defer` saying **why**, in one or
  two sentences. For `change`, which part of the sentence requires it. For
  `defer`, what the separate change would be.

Do not edit `findings.md`, do not add findings, and do not touch the suite or
the application. You are judging what was found, not looking for more.

## When you are done

Edit `{PAPERS}/findings.yml` in place, leaving its structure and
its ids exactly as they are. Change only `decision` and `note`, and fill
`pinned_by` where it is empty.

Then summarise: how many of each verdict, and the reasoning for any finding you
found genuinely hard to call.
