# Patch series — Task 1 (Phase 0)

Fourteen commits, each named for the invariant it adds. They apply on top of
your current `main` (the commit that has `SUBSTRATE.md` v0.3 and the render
mock, before any Task 1 work).

The working tree in this repository is already the *result* of applying them,
so you only need these if you want the history rather than the end state.

## To replay the history

```bash
cd /mnt/c/AI/signal-lab
git checkout -b task-1-phase-0 <your-pre-task-1-commit>
git am patches/*.patch
```

If `git am` stops, `git am --abort` returns you to where you were; the working
tree already on disk is unaffected either way.

## To skip the history

Do nothing. The files are already in place. Commit them however you like:

```bash
git checkout -b task-1-phase-0
git add -A && git commit -m "Task 1: phase 0 scaffold"
```

## The commits

| # | Invariant |
|---|---|
| 0001 | every threshold lives in params/, nothing key-shaped is tracked |
| 0002 | params are hashed and travel with every run |
| 0003 | the loader refuses every date on or after HOLDOUT_START |
| 0004 | every panel carries per-series metadata, and macro is bitemporal |
| 0005 | the seven loader rules of SUBSTRATE 5.1, as functions |
| 0006 | the synthetic panel has the vendors' shape and a known plant |
| 0007 | run history cannot be rewritten |
| 0008 | all ten vetoes, and a veto that cannot be evaluated fails |
| 0009 | tests: pass, fail and boundary for every veto; the holdout lock by name |
| 0010 | a hypothesis without a direction or a rationale never runs |
| 0011 | an unconfigured budget refuses the call, it does not allow it |
| 0012 | one sort, failures visible, gross IR never rendered |
| 0013 | a snapshot is immutable and hashed, and a cycle invents nothing |
| 0014 | ten open questions, the conservative option taken in each |
