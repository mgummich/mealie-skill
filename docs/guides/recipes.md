---
title: Recipes
description: Repairing ingredient lines, filling fields, images and sources — and the one number that says whether the library is machine-readable.
---

# Recipes

A recipe is only as useful as its ingredient lines. Everything Mealie does
beyond displaying text — shopping lists, scaling, diet tags, duplicate
detection — reads the parsed line: an amount, a unit, a food. A library of
beautiful prose with unparsed lines is a scrapbook.

The rules for recipe content are the rule set's:
[creating]({{ site.baseurl }}/rules/en/07-recipes-create-EN.md) ·
[cleanup]({{ site.baseurl }}/rules/en/07-recipes-cleanup-EN.md).

## The headline number

```console
$ python3 .../mealie_ctx.py audit recipes
2 recipes, 0 name duplicates
LINES WITH A LINKED FOOD: 10 (59 %) of 17 – the headline number, target above 95 %
AMOUNT STRANDED IN THE NOTE: 1 recipes – red-lentil-curry
LINES WITHOUT originalText: 1 recipes – fill it from the display value before repairing them
LINES CARRYING Original:: 2
NOTE TITLES OUTSIDE THE VOCABULARY: Original
ONE SINGLE STEP: 0 · OVER 15 STEPS: 0
COOKED (lastMade set): 1 · RATED: 1 – work these first, they are the ones in use
```

Read it in this order:

1. **Linked food percentage.** Below 95 %, fix parsing before anything else.
2. **Lines without `originalText`.** Repair these first — without the
   original text there is no evidence of what was imported, and a repair
   becomes a guess. Fill it from the display value.
3. **Amount stranded in the note.** The importer put `400` into the note
   instead of the quantity field. Common, mechanical, worth a pass of its own.
4. **Cooked and rated recipes.** Those are the ones in use. If you clean a
   subset, clean that one.

## One recipe at a time

```bash
python3 .../mealie_ctx.py ctx recipe red-lentil-curry --search lentil onion
```

Returns the recipe in a slimmed form — the bookkeeping fields no mode reads
are dropped, which roughly halves the payload — plus the foods matching each
search term and the available organizers. That is the whole context for a
repair: what the line says now, and what it could point at.

`--full` gives the unabridged JSON. Rarely needed; useful when something
looks wrong and you suspect the slimming.

## Writing a repair

`patch_recipe` carries the changed fields:

```json
{"op": "patch_recipe",
 "payload": {"slug": "red-lentil-curry",
             "recipeIngredient": [
               {"quantity": 200, "unit": {"id": "u-g"}, "food": {"id": "f-lentil"},
                "note": "Original: 1 cup red lentils", "originalText": "1 cup red lentils"}
             ]}}
```

**List fields are replaced, not merged.** Mealie takes `recipeIngredient`,
`recipeInstructions`, `notes`, `tags` and the rest wholesale: a payload with
three lines leaves the recipe with exactly three lines. A patch carrying
fewer lines than the recipe holds is therefore a deletion, and `apply`
refuses it unless the action says `"replace": true`. See
[decision 0005](../decisions/0005-guards-refuse-not-warn.md).

Two more things the tool does on your behalf:

- **A write that changes nothing is not sent.** Every patch is compared
  against the current record and reported as `UNCHANGED` instead. A second
  run over a clean library produces zero changes.
- **A rename changes the slug.** Mealie re-derives it from the name, and the
  tool reads the new one back so a later `set_image` in the same run still
  finds the recipe.

## Text, and what language it is in

Descriptions, steps and notes go into the database in full prose, in the
content language the skill was built with — never compressed, never in the
style of the chat. They stay in the instance permanently and are read by
people who never saw this workflow. The rule is stated in `SKILL.md` and in
the actions reference because it is the one an agent is most tempted to
break.

## Images and sources

```json
{"op": "set_image", "payload": {"slug": "red-lentil-curry",
                                "url": "https://example.com/curry.jpg"}}
```

Mealie fetches the URL itself. The replaced image is not recoverable — it
lives under a fixed path that the new one takes over — so the changelog
records that there was one, not what it looked like.

For dead links and missing images across the library:

```bash
python3 .../mealie_ctx.py audit links --check-urls
```

Without `--check-urls` it counts what is missing; with it, it actually
requests every source URL, which takes a while and is worth doing once a
year.

## Duplicate recipes

```bash
python3 .../mealie_ctx.py audit recipes
```

reports name duplicates and ingredient-overlap suspicions. They are
**presented only**. There is no operation for deleting a recipe and there
will not be one — you delete in the UI, having looked at both. See
[decision 0002](../decisions/0002-no-recipe-deletion.md).
