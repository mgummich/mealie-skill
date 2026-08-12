# ACTIONS format

Plan and execution are separate: you write `actions.json`, check it with
`--dry-run`, get approval, then the script executes it.

<!-- agent-only -->
**Content in `actions.json` is database content, not chat.** Even when the
output style is compressed (see caveman in SKILL.md): `description`,
preparation steps, notes and cookbook descriptions are written here as full
${CONTENT_LANG} prose. They stay in the instance permanently and are read by
people who do not know this workflow.
<!-- standalone: **Content in the ACTIONS block is database content, not chat.** `description`, preparation steps, notes and cookbook descriptions always as full ${CONTENT_LANG} prose — they stay in the instance permanently and are read by people who do not know this workflow. -->

```json
{"actions": [
  {"op": "create_label", "id_as": "lbl_spices",
   "payload": {"name": "Spices & Herbs", "color": "#8B5E3C"}},
  {"op": "create_food", "id_as": "food_cumin",
   "payload": {"name": "Cumin", "labelId": "$ref:lbl_spices"}}
]}
```

`"$ref:<id_as>"` is replaced at runtime with the id of the object created in
the same run. Always reference existing objects by their real id. A
reference whose `id_as` is missing or created later is refused by the dry
run, before the first write.

Aliases are objects in Mealie: `"aliases": [{"name": "tomatoes"}]`. A plain
list of strings is accepted as shorthand and converted.

## Order

Mandatory, violations abort before the first write:

    create_label -> merge_food -> merge_unit -> create_food -> create_unit
    -> create_category -> create_tag -> create_tool -> update_food
    -> update_unit -> update_organizer -> retag_recipe -> delete_organizer
    -> delete_food -> delete_unit
    -> create_cookbook -> update_cookbook -> patch_recipe -> set_image

The reason: retag before deleting; create before referencing.

**Deleting a food or unit is not merging one.** A merge repoints every
recipe that used the loser; a delete strips it from them. So `delete_food`
and `delete_unit` are for orphans only - a test artefact, a leftover of an
old import, a non-metric unit whose last line has been converted - and the
script refuses them while the index shows any recipe using the object. It
also refuses them without an index, because it cannot check. Freeing the
last reference and deleting it in the same run is refused too: audit again
first, then delete.

## Operations

| op | payload |
|---|---|
| `create_label` | `name`, `color` (hex) |
| `create_food` | `name`, `pluralName`, `description`, `labelId`, `aliases` |
| `create_unit` | `name`, `pluralName`, `abbreviation` |
| `create_category` / `create_tag` / `create_tool` | `name` |
| `merge_food` / `merge_unit` | `from`, `to` (ids) |
| `update_food` / `update_unit` | `id` + only the fields to set |
| `update_organizer` | `kind` (`categories`/`tags`/`tools`/`labels`), `id`, fields |
| `retag_recipe` | `slug`, `kind` (no labels - nothing to retag), `add` (ids), `remove` (ids) |
| `delete_organizer` | `kind`, `id` |
| `delete_food` / `delete_unit` | `id`; refused while any recipe uses it |
| `create_cookbook` | `name`, `description`, `queryFilterString` (the filter, see `references/cookbooks.md`), optional `public` |
| `update_cookbook` | `id` + fields to change |
| `patch_recipe` | the changed recipe fields - list fields in full, see below - plus `slug` for the recipe (or `--slug` for the whole run) |
| `set_image` | `url`, plus `slug` (or `--slug`) |

A `slug` in the payload wins over `--slug`, so one file can patch many
recipes: `--slug` is the shorthand for the single-recipe case. Several
`patch_recipe` actions in a row are fine — `ORDER` allows repeats, it fixes
the sequence of the operations, not their number.

## Renaming a recipe changes its slug

Mealie derives the slug from the name, so a `patch_recipe` that carries
`name` makes the old slug a 404 the moment it lands. Anything that addresses
the recipe afterwards has to use the new one.

Within one run this is handled: the script reads the slug back from the
response and prints `SLUG old -> new (renamed)`, and `set_image` — the only
op that comes after `patch_recipe` — follows it. Beyond that run it is
yours to track. Take the new slug from that line, do not guess it from the
name, and do not reuse a slug you noted before the rename.

That is also why a rename belongs in the **same** `patch_recipe` as the
other field changes, never in a second one afterwards.

## Partial updates

`update_food`, `update_unit`, `update_organizer` and `update_cookbook` read
the existing record and lay the given fields over it - list only what should
change.

Exception: list fields are **replaced**, not extended. For `aliases` always
include the existing entries as well.

The same holds for a recipe, where it costs more: `recipeIngredient`,
`recipeInstructions`, `notes`, `tags`, `recipeCategory` and `tools` are
replaced, so a `patch_recipe` carrying three ingredient lines leaves the
recipe with three. **Send list fields back whole.** Scalars (`name`,
`description`, times, yield) can be patched on their own.

A patch whose list is shorter than the recipe's is refused. When the removal
is meant - two lines merged, a note dropped - say so on the action, next to
`"op"`:

```json
{"op": "patch_recipe", "replace": true,
 "payload": {"slug": "lentil-curry", "notes": []}}
```

An ingredient line carries `food` and `unit` as **objects with an id**:

```json
{"op": "patch_recipe",
 "payload": {"slug": "lentil-curry", "recipeIngredient": [
   {"quantity": 80,
    "unit": {"id": "$ref:ml", "name": "Milliliter"},
    "food": {"id": "d77f8eb4-…", "name": "Milk"},
    "note": "heated", "originalText": "80 ml milk, heated",
    "referenceId": "0e2b1c7a-…"}]}}
```

`foodId`/`unitId`, or a plain name in `food`, are dropped by Mealie without
an error and leave the line with null where the food was - the run refuses
them instead. Keep the `referenceId` a line already has, and omit `unit`
entirely on a line that has none.

## What the dry run checks, what a run leaves behind

`--dry-run` also lints the plan and prints `WARN` per finding: new food
without label or aliases, over-long description, tag with two concepts or a
`no X` phrasing, tool with a brand or an inch size, label on the default
colour, over eight tags, note title outside the vocabulary, rename dropping
the old name, an ingredient line setting `display` or naming two foods, a
recipe name or a note over its length, a tool every kitchen has, a
cookbook with no filter or with more than three conditions. One finding is
fatal: a non-metric unit. Cup, ounce, pound, pint and stick are converted
with `convert`, never stored.

Overwriting an ingredient line's `originalText` is refused outright, like a
shortening list field - it is the raw imported line and the evidence a
parse error is proved against. Filling an empty one is the documented
repair and passes.

An update whose value is already there is not sent: the run prints
`UNCHANGED` and logs nothing. A `retag_recipe` counts as such an update -
adding a tag the recipe already carries writes nothing, and the `+n -n` it
prints are the tags that actually moved. So a plan applied twice - after a partial
failure, or built from an audit that was already acted on - changes the
instance once, and a second run over a clean corpus is provably a no-op.

Every applied action is appended to `.mealie.changelog.jsonl` with the state
it overwrote - whole object for merges and deletions, touched fields for
updates. That file is the only way back; do not delete it mid-cleanup. A
merge is verified afterwards against the recipes that used the source. A
replaced image is the one thing the log cannot restore.

<!-- agent-only -->
## Invocation

    python scripts/mealie_ctx.py apply actions.json --dry-run
    python scripts/mealie_ctx.py apply actions.json              # no recipe
    python scripts/mealie_ctx.py apply actions.json --slug <slug>  # with one
<!-- standalone: (The script handles dry run and execution after your approval.) -->
