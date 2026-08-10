---
title: Actions format
description: The JSON a plan is written in, the order it is executed in, and every check that runs before the first write.
---

# Actions format

A plan is a JSON file. The model writes it, you read it, `apply` executes it.
Separating the two is the point: the thing you approve is the thing that
runs.

```json
{"actions": [
  {"op": "create_label", "id_as": "lbl_spices",
   "payload": {"name": "Spices & Herbs", "color": "#8B5E3C"}},
  {"op": "create_food", "id_as": "food_cumin",
   "payload": {"name": "Cumin", "labelId": "$ref:lbl_spices"}}
]}
```

`"$ref:<id_as>"` is replaced at runtime with the id of the object created in
the same run. Existing objects are always addressed by their real id.

## The canonical operation table

Every operation and its payload fields live in **`skill/references/actions.md`**
in the repository — the file the agent reads and the standalone prompts are
rendered from. It is the single source; this page does not copy it, so that
the two cannot drift apart.

[Read it on GitHub](https://github.com/mgummich/mealie-skill/blob/main/skill/references/actions.md)

What follows is what that file cannot tell you: what the script does with
the plan.

## Execution order

Enforced, and violations abort before the first write:

```
create_label -> merge_food -> merge_unit -> create_food -> create_unit
-> create_category -> create_tag -> create_tool -> update_food
-> update_unit -> update_organizer -> retag_recipe -> delete_organizer
-> delete_food -> delete_unit
-> create_cookbook -> update_cookbook -> patch_recipe -> set_image
```

Two rules produce that sequence: **retag before deleting**, and **create
before referencing**. Repeats are fine — the order fixes the sequence of the
operations, not their number.

The order lives in `ORDER` in the script and in the reference the model
reads. Changing one without the other means every plan the model writes hits
the guard.

## Content, not chat

`description`, preparation steps, notes and cookbook descriptions are
database content. They go in as full prose in the content language, even
when the conversation around them is compressed. They stay in the instance
permanently and are read by people who never saw this workflow.

## What runs before the first write

In order:

1. **Unknown operations.** Anything not in `ORDER` aborts.
2. **The order itself.**
3. **Name collisions.** A rename into a name another food or unit already
   holds is refused — that is a merge, not a rename, and doing it as a
   rename leaves two records that both claim the name.
4. **Shortening list fields.** Mealie replaces list fields instead of
   merging them, so a `patch_recipe` carrying fewer entries than the recipe
   holds is a deletion. Refused unless the action carries `"replace": true`.
5. **The plan lint.** Mechanical rules from `lint.json` — a new food without
   label or aliases, an over-long description, a tag carrying two concepts,
   a tool with a brand name, a label left on the default colour, a note
   title outside the vocabulary. Printed as `WARN`. One finding is fatal:
   creating a non-metric unit.
6. **Organizer kinds.** `update_organizer` and `delete_organizer` accept
   `categories`, `tags`, `tools`, `labels` and nothing else.
7. **Cookbook payloads.** A filter written in the pre-2.0 shape is refused,
   because Mealie would ignore it and leave a cookbook matching everything.
8. **Deletions in use.** `delete_food` and `delete_unit` are refused while
   the index shows a recipe using the object, and refused without an index,
   because then the check cannot be made.

`--dry-run` runs all of it. Where it needs the instance and has no
credentials, it names what it could not check instead of passing over it.

## What happens during the run

- **Every write logs its before-state first.** `.mealie.changelog.jsonl`,
  written before the next action runs. See
  [Recovering a run](../guides/recovering-a-run.md).
- **A write that changes nothing is not sent.** Updates are compared against
  the current record and reported as `UNCHANGED`. A plan applied twice — after
  a partial failure, say — does not double anything.
- **Merges are verified.** The affected recipes are read back; if any still
  points at the merged-away object, the run stops.
- **A rename is followed.** Mealie re-derives the slug from the name; the new
  one is read from the response, printed as `SLUG old -> new (renamed)`, and
  used by a later `set_image` in the same run.
- **The index is deleted** after a writing run, because everything it
  measured has changed.

## A failing run

```console
!! ABORTED after 4/11 actions: 500 Server Error for url: ...
applied actions and what they overwrote: .mealie.changelog.jsonl
not applied: patch_recipe, patch_recipe, set_image
No repair attempt is made. Report the state reached and ask.
```

No repair is attempted, deliberately: a half-applied plan is a known state,
a half-unwound one is not.

## Adding an operation

Four places, all of them required: an entry in `ORDER`, a branch in
`cmd_apply` that logs its before-state, a row in the table in
`skill/references/actions.md`, and a case in the dry run test. See
[Development](../development.md).
