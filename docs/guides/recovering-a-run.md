---
title: Recovering a run
description: What the changelog holds, how to put a field back, and what to do when a run aborts halfway.
---

# Recovering a run

Mealie has no undo, and this tool has no rollback command. What it has is a
record: every applied action is appended to `.mealie.changelog.jsonl`
together with the state it replaced, **before the next action runs**. A run
that dies halfway still leaves the actions it did apply on record.

## What a record looks like

One JSON object per line:

```json
{"ts": 1786000000.0,
 "run": "1786000000",
 "op": "update_food",
 "target": {"kind": "foods", "id": "f-lentil"},
 "before": {"description": "", "pluralName": ""},
 "payload": {"description": "Split red lentils, cook in 15 minutes.",
             "pluralName": "red lentils"}}
```

- `run` — shared by every action of one `apply`, so one run is one `grep`.
- `target` — what was addressed.
- `before` — only the fields the action touched. Enough to put them back,
  small enough that the file stays readable.
- `payload` — what was sent.
- `result` — present where the action produced something, e.g. a created id.

Two operations record more, because they destroy more:

- **Merges** store the loser's entire record plus the slugs of every recipe
  that referenced it. That is the only place the loser survives.
- **Deletions** store the whole object.

One thing is not recoverable: a replaced image. Mealie serves it under a
fixed path that the new image takes over, so the record says there was one,
not what it was.

## Putting something back

Read the run:

```bash
grep '"run": "1786000000"' .mealie.changelog.jsonl | python3 -m json.tool --json-lines
```

Then write an actions file that sets the `before` values again — the reverse
of a patch is a patch. For a food:

```json
{"actions": [
  {"op": "update_food",
   "payload": {"id": "f-lentil", "description": "", "pluralName": ""}}
]}
```

Apply it like any other plan, with `--dry-run` first.

A **merge** is not reversible this way: recreate the food from the stored
record, then repoint the recipes listed under `recipes` in the changelog
entry. A **deletion** is: recreate from the stored object, but the new object
gets a new id, so anything that referenced the old one needs repointing too.

This is the point where the backup you took before the run is worth more
than any of this. Take one before any run containing a merge or a delete.

## When a run aborts

`apply` stops at the first failing request and prints what happened:

```console
!! ABORTED after 4/11 actions: 500 Server Error for url: ...
applied actions and what they overwrote: .mealie.changelog.jsonl
not applied: patch_recipe, patch_recipe, set_image
No repair attempt is made. Report the state reached and ask.
```

It deliberately does not try to repair. A half-applied plan is a known
state; a plan that tried to unwind itself and failed halfway through the
unwinding is not. Report the state, decide what to do, write a new plan.

The first four actions are in the changelog with their before-state. The
seven that did not run changed nothing.

## The index after a failure

A writing `apply` deletes `.mealie_index.json`, because everything it
measured has just changed. After an abort the index is gone too, and the next
audit rebuilds it — which is what you want, since the corpus is now in a
state neither the old index nor your plan describes.

## Verifications that run without being asked

- **Merges are read back.** The affected recipes are fetched after the merge;
  if any still points at the merged-away object, the run stops. Mealie
  answers a merge that lost references exactly like one that worked.
- **Nothing is deleted while it is in use.** `delete_food` and `delete_unit`
  are refused while the index shows a recipe using the object — and refused
  without an index, because then the check is impossible.
- **A shortening list field is refused** unless the action says
  `"replace": true`.
- **A payload for an older Mealie API is refused**, because Mealie ignores
  unknown fields rather than rejecting them.

Each of these exists because the failure it prevents is silent. See
[the decisions](../decisions/).
