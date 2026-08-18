## Your task

Review the suite edit that states a change, and accept or reject it. You are
standing in for a person, and this is the review that decides what gets built:
**the diff is the specification.** Nothing downstream re-reads the sentence — the
builder is judged only by the tests in this diff.

Task: {WORKFLOW}
Suite: `{SUITE_DIR}`

The change this diff is supposed to state:

{TASK_SPEC}

The judged findings are in `{PAPERS}/findings.yml`, and they are
part of what you are checking against.

## Read the diff

```
git diff {BASE}...HEAD -- {SUITE_DIR}
```

Read all of it. A specification you have skimmed is not one you have reviewed.

## What makes it right

{CRITERIA}

## Your verdict

Write `{PAPERS}/REVIEW.md` — that path is absolute, so use it exactly as given rather
than shortening it; your working directory is not necessarily what you assume, and a verdict
written one directory away from where slipway looks is a verdict nobody reads.

Its **first line must be exactly one of**:

```
VERDICT: accept
VERDICT: reject
```

Then, underneath, your reasoning — what you checked, what convinced you, and for a
rejection, precisely what must change before it can be accepted. Name tests and
findings by id.

Reject when the diff is wrong. An acceptance that was not earned is worse than no
review, because everything downstream treats it as a person's judgement.

Do not edit the suite, the application, or the findings. Your output is the
verdict and its reasoning.
