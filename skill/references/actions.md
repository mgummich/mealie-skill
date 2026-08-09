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
the same run. Always reference existing objects by their real id.

## Order

Mandatory, violations abort before the first write:

    create_label -> merge_food -> merge_unit -> create_food -> create_unit
    -> create_category -> create_tag -> create_tool -> update_food
    -> update_unit -> update_organizer -> retag_recipe -> delete_organizer
    -> create_cookbook -> update_cookbook -> patch_recipe -> set_image

The reason: retag before deleting; create before referencing.

## Operations

| op | payload |
|---|---|
| `create_label` | `name`, `color` (hex) |
| `create_food` | `name`, `pluralName`, `description`, `labelId`, `aliases` |
| `create_unit` | `name`, `pluralName`, `abbreviation` |
| `create_category` / `create_tag` / `create_tool` | `name` |
| `merge_food` / `merge_unit` | `from`, `to` (ids) |
| `update_food` / `update_unit` | `id` + only the fields to set |
| `update_organizer` | `kind` (`categories`/`tags`/`tools`), `id`, fields |
| `retag_recipe` | `slug`, `kind`, `add` (ids), `remove` (ids) |
| `delete_organizer` | `kind`, `id` |
| `create_cookbook` | `name`, `description`, `categories`/`tags`/`tools`, `requireAll*` |
| `update_cookbook` | `id` + fields to change |
| `patch_recipe` | only the changed recipe fields (needs `--slug`) |
| `set_image` | `url` (needs `--slug`) |

## Partial updates

`update_food`, `update_unit`, `update_organizer` and `update_cookbook` read
the existing record and lay the given fields over it - list only what should
change.

Exception: list fields are **replaced**, not extended. For `aliases` always
include the existing entries as well.

<!-- agent-only -->
## Invocation

    python scripts/mealie_ctx.py apply actions.json --dry-run
    python scripts/mealie_ctx.py apply actions.json              # no recipe
    python scripts/mealie_ctx.py apply actions.json --slug <slug>  # with one
<!-- standalone: (The script handles dry run and execution after your approval.) -->
