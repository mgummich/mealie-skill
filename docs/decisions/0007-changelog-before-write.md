---
title: "0007 — The before-state is logged before the next action runs"
description: Per action, not per run — a run that dies halfway still leaves a record of what it changed.
---

# 0007 — The before-state is logged before the next action runs

**Status:** accepted · **Recorded:** 2026-08-10

## Context

Mealie has no undo. This tool has no rollback command, and deliberately does
not attempt repair after a failure ([0001](0001-three-phases.md)): a
half-applied plan is a known state, a half-unwound one is not.

That leaves the record as the only path back. A record written at the end of
a run is worthless exactly when it is needed — the run that fails is the run
that never reaches the end.

## Decision

Every applied action appends one line to `.mealie.changelog.jsonl`, holding
the state it overwrote, **before the next action runs**. Writing that line is
part of the operation, not part of the run.

If the changelog cannot be written, the run aborts rather than continuing
unlogged.

## What is recorded

`before` holds only the fields the action touched — enough to put them back,
small enough that the file stays readable. Two operations record more,
because they destroy more: a merge stores the loser's entire record plus the
slugs of every recipe that referenced it, and a deletion stores the whole
object.

One thing cannot be recorded: a replaced image. Mealie serves it under a
fixed path that the new image takes over, so the entry notes that there was
one.

## Consequences

- Every new writing operation is unfinished until it reads the state it is
  about to replace and logs it. That is the fourth requirement on a new
  operation, next to `ORDER`, the reference table and the dry run test.
- The file grows without bound and is never rotated. A rotation that
  discarded the record of the merge you are undoing would defeat its only
  purpose.
- It contains your data. It belongs out of version control, and out of any
  paste into a bug report without a read-through first.
- Recovery is a hand-written plan, not a command. That is honest about what
  it is: [Recovering a run](../guides/recovering-a-run.md).

## Alternatives rejected

**A rollback command.** It would have to reverse merges and deletions
correctly, in order, against a database that may have changed since — a
second write path with all the risks of the first and none of the testing.

**Log at the end of the run.** Fails precisely in the case it exists for.

**Log only destructive operations.** Every write is destructive to whatever
was in the field before it.
