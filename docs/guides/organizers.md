---
title: Organizers
description: Categories, tags and tools — the vocabulary everything else filters on, and how to keep it small enough to mean something.
---

# Organizers

Categories, tags and tools are one vocabulary with three shapes. They are
what cookbooks filter on, what the sidebar navigates by, and the first thing
to collapse in a library that grew by importing.

The rules for each — what a category axis is, why tools have no aliases, how
many tags a recipe may carry — are in the rule set:
[categories]({{ site.baseurl }}/rules/en/04-categories-create-EN.md) ·
[tags]({{ site.baseurl }}/rules/en/05-tags-create-EN.md) ·
[tools]({{ site.baseurl }}/rules/en/06-tools-create-EN.md).

## Audit

```bash
python3 .../mealie_ctx.py audit categories
python3 .../mealie_ctx.py audit tags
python3 .../mealie_ctx.py audit tools
```

All three print totals, the unused, the rare, duplicate suspicions, the
largest entries and how many recipes exceed the cap from `lint.json`
(2 categories, 8 tags, 4 tools by default). Each adds one check of its own:

- **categories** — the average per recipe. Above 1.5 the axis has collapsed:
  categories are no longer one question with one answer but a second tag
  system. Also the count of recipes with no category at all.
- **tags** — tags on more than 90 % of recipes. A tag that is everywhere
  filters nothing; it is a fact about your library, not a selector.
- **tools** — entries failing the gating test, checked against the everyday
  equipment list in `lint.json`. `Knife` and `Bowl` are not tools worth
  recording; an air fryer is, because someone might not own one.

## The three questions before touching anything

**Is this an axis or a pile?** Categories answer one question — usually dish
type. If some categories say *Dessert* and others say *Italian*, the axis is
already two axes and the second one belongs in tags.

**Is this tag one concept?** `quick-vegetarian` is two, and no filter can use
it as either. Split it; the plan lint flags conjunctions.

**Would anyone filter by this?** A tag nothing filters by is a note, and
notes belong on the recipe.

## Moving, not deleting

An entry in the wrong entity is transferred, never deleted and retyped:
create the target, retag the recipes, compare the counts, then delete the
source. That is exactly the order `apply` enforces —
`create_tag` → `retag_recipe` → `delete_organizer` — and a plan that tries it
the other way round aborts before the first write.

```json
{"actions": [
  {"op": "create_tag", "id_as": "tag_italian", "payload": {"name": "italian"}},
  {"op": "retag_recipe",
   "payload": {"slug": "ragu", "kind": "tags", "add": ["$ref:tag_italian"]}},
  {"op": "retag_recipe",
   "payload": {"slug": "ragu", "kind": "categories", "remove": ["cat-italian"]}},
  {"op": "delete_organizer", "payload": {"kind": "categories", "id": "cat-italian"}}
]}
```

`$ref:` is replaced at runtime with the id of the object created in the same
run. Existing objects are always addressed by their real id.

## Which recipes does this affect?

Before any merge or deletion:

```bash
python3 .../mealie_ctx.py usage tag <id>
```

It reads the index, so it costs nothing and is worth running on every entry
you are about to touch.

## After the pass, check the cookbooks

Cookbooks filter on this vocabulary and break silently when it moves — the
cookbook does not disappear, it empties, and nobody opens an empty cookbook.
Checking them is the closing step of an organizer cleanup, not a project of
its own: [cookbooks](cookbooks.md).
