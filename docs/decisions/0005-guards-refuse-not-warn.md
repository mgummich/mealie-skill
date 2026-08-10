---
title: "0005 — Guards refuse; they do not warn"
description: Every failure the tool can see coming aborts before the first write.
---

# 0005 — Guards refuse; they do not warn

**Status:** accepted · **Recorded:** 2026-08-10

## Context

The failures this tool has to prevent share a property: they are silent. A
patch that shortens a list field does not error, it deletes. A merge that
lost its references answers exactly like one that worked. A cookbook filter
in the wrong shape is accepted and matches everything. A delete of a food in
use does not fail, it strips the ingredient from every recipe that had it.

A warning about a silent failure is read after the fact, in a log, by someone
who already believes the run went well.

## Decision

Anything the tool can detect before the write **aborts the run**, before the
first action, with a message naming the fix. Warnings are reserved for
matters of taste.

Currently refusing:

| Guard | Prevents |
|---|---|
| execution order | referencing an object before it exists; deleting before retagging |
| name collision on rename | two records both claiming one name — that is a merge |
| shortening a list field | a silent deletion of ingredients, steps or notes |
| deleting an object in use | the object being stripped from every recipe that had it |
| deleting without an index | making that check impossible and calling it fine |
| pre-2.0 cookbook payload | a cookbook with no filter, matching everything |
| non-metric unit in the lint | a unit the rules say is never created |
| merge verification (after) | a merge that left references behind |

Everything else the lint finds — a food without a label, an over-long
description, a tag with two concepts — prints as `WARN` and lets the run
proceed. Those are judgement calls where the plan may be right and the rule
approximate.

## Consequences

- A refused plan is rewritten, not overridden. Where an intent is genuinely
  meant, it is stated on the action — `"replace": true` for a deliberate list
  removal — rather than by a flag that switches the guard off wholesale.
- `--dry-run` runs every guard, so a plan can be checked before it is
  approved.
- Guards need something to check against, which is why the index is required
  for deletions ([0004](0004-index-first.md)).
- New operations inherit the obligation: an operation that can fail silently
  is not finished until the guard exists.

## Alternatives rejected

**`--force`.** It would be typed the second time, by the same person, in the
same minute, and the guard would protect nothing.

**Warn and continue.** The whole class of failure here is one nobody notices;
a warning is only useful for failures somebody looks for.
