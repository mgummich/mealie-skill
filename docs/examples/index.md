---
title: Examples
description: Complete actions files for the common passes, each one checked against the dry run.
---

# Examples

Five plans, copy-pasteable. Every one of them passes
`apply --dry-run` as written — the ids are placeholders, so replace them with
real ones from `ctx` or `audit` before applying anything.

```bash
python3 .../mealie_ctx.py apply plan.json --dry-run   # always first
python3 .../mealie_ctx.py apply plan.json
```

## Creating a label, a food and a unit

[`label-and-food.json`](label-and-food.json)

```json
{"actions": [
  {"op": "create_label", "id_as": "lbl_spices",
   "payload": {"name": "Spices & Herbs", "color": "#8B5E3C"}},
  {"op": "create_food", "id_as": "food_cumin",
   "payload": {"name": "cumin",
               "pluralName": "cumin",
               "description": "Ground cumin seed.",
               "labelId": "$ref:lbl_spices",
               "aliases": [{"name": "ground cumin"}, {"name": "Kreuzkümmel"}]}},
  {"op": "create_unit",
   "payload": {"name": "gram", "pluralName": "grams", "abbreviation": "g"}}
]}
```

`$ref:lbl_spices` becomes the id of the label created two lines above. The
order is not a style choice: `create_label` precedes `create_food` in `ORDER`
precisely so a food can reference a label made in the same run.

The aliases are the point of the whole entry. Without them the next import
writes `ground cumin` as a second food and the duplicate audit finds it next
quarter.

## Merging two foods

[`foods-merge.json`](foods-merge.json)

```json
{"actions": [
  {"op": "merge_food",
   "payload": {"from": "…0001", "to": "…0002"}},
  {"op": "update_food",
   "payload": {"id": "…0002",
               "name": "tomato",
               "pluralName": "tomatoes",
               "description": "Fresh tomatoes, raw weight.",
               "aliases": [{"name": "tomatoes"}, {"name": "Tomate"},
                           {"name": "Tomaten"}]}}
]}
```

The merge repoints every recipe that used the loser, then the update gives
the survivor the loser's name as an alias. Skip the second action and the
duplicate comes back at the next import.

Two things happen without being asked: the loser's whole record goes into the
changelog before the merge, and the affected recipes are read back
afterwards. A merge that left references behind stops the run.

## Repairing a recipe

[`recipe-repair.json`](recipe-repair.json)

```json
{"actions": [
  {"op": "patch_recipe", "replace": true,
   "payload": {
     "slug": "red-lentil-curry",
     "name": "Red Lentil Curry",
     "description": "A quick lentil curry with coconut milk and tomatoes, ready in half an hour and better the next day.",
     "recipeServings": 4,
     "totalTime": "35 min",
     "prepTime": "10 min",
     "recipeIngredient": [
       {"quantity": 200, "unit": {"id": "…0010"}, "food": {"id": "…0011"},
        "note": "Original: 1 cup red lentils",
        "originalText": "1 cup red lentils"}
     ],
     "notes": [
       {"title": "Variation",
        "text": "With spinach stirred in at the end it stretches to five servings."}
     ]}},
  {"op": "set_image",
   "payload": {"slug": "red-lentil-curry",
               "url": "https://upload.wikimedia.org/wikipedia/commons/example.jpg"}}
]}
```

Three things to copy from this one:

- **`"replace": true`** sits next to `"op"`, not in the payload, and is
  required whenever a list field comes back shorter than it was. Here the two
  original lines were merged into fewer; without the flag the run aborts.
- **`Original:`** on the converted line — English in every language version,
  because it is one detection rule for the whole database and the marker that
  stops the next pass converting the same line again.
- **The rename and the field changes are one action.** Mealie re-derives the
  slug from the name, so a second `patch_recipe` afterwards would address a
  slug that no longer exists. `set_image` is fine: it runs after
  `patch_recipe` and follows the new slug automatically.

## Moving a category into a tag

[`organizer-transfer.json`](organizer-transfer.json)

```json
{"actions": [
  {"op": "create_tag", "id_as": "tag_italian", "payload": {"name": "italian"}},
  {"op": "retag_recipe",
   "payload": {"slug": "ragu-bolognese", "kind": "tags",
               "add": ["$ref:tag_italian"]}},
  {"op": "retag_recipe",
   "payload": {"slug": "ragu-bolognese", "kind": "categories",
               "remove": ["…0030"]}},
  {"op": "delete_organizer",
   "payload": {"kind": "categories", "id": "…0030"}}
]}
```

Create, retag, then delete — in that order, because the enforced order says
so and because doing it the other way round loses the association before
anything holds it. One `retag_recipe` per affected recipe.

## Creating and repairing a cookbook

[`cookbook.json`](cookbook.json)

```json
{"actions": [
  {"op": "create_cookbook",
   "payload": {"name": "Weeknight, under 30",
               "description": "Dishes for evenings when time is short - under half an hour, mostly in a single pot.",
               "queryFilterString": "tags.name CONTAINS ALL [\"quick\", \"one-pot\"]",
               "public": false}},
  {"op": "update_cookbook",
   "payload": {"id": "…0020",
               "queryFilterString": "recipeCategory.name IN [\"Dessert\"] AND rating > 3"}}
]}
```

One filter string, not three name lists — see
[the cookbook guide](../guides/cookbooks.md). `update_cookbook` changes the
rule in place, so every link to the cookbook survives the repair.

## What a dry run prints

```console
$ python3 .../mealie_ctx.py apply cookbook.json --dry-run
[dry-run] nothing configured: name collisions and recipe list fields NOT checked
[dry-run] create_cookbook: {"name": "Weeknight, under 30", …}
[dry-run] update_cookbook: {"id": "…0020", "queryFilterString": "recipeCategory.name IN [\"Dessert\"] AND rating > 3"}
```

The first line is the honest part: without credentials the checks that need
the instance cannot run, and it says which ones rather than implying the plan
passed them.
