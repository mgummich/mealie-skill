---
title: Cookbooks
description: Filter strings, hit counts, and repairing the one entity in Mealie that breaks without saying so.
---

# Cookbooks

A cookbook in Mealie is not a folder you put recipes into. It is a saved
filter: recipes fall into it when they match and fall out again when their
tags change. Everything else about cookbooks follows from that.

The rules — when a cookbook is worth creating, what to name it, what belongs
in the description — are the rule set's:
[creating]({{ site.baseurl }}/rules/en/08-cookbooks-create-EN.md) ·
[cleanup]({{ site.baseurl }}/rules/en/08-cookbooks-cleanup-EN.md).

## Look at the hit counts

```bash
python3 .../mealie_ctx.py ctx cookbooks
```

prints every cookbook as `id|name|hits|filter|description`, followed by the
categories, tags and tools with their recipe counts.

The hit count is the only metric that matters. Zero means the filter is
broken or the vocabulary is gone. Over 50, or over 30 % of the library, means
the cookbook is the library with an extra click.

## The filter is one string

Since Mealie 2.0 a cookbook carries a single `queryFilterString`. The three
name lists and their `requireAllCategories` / `requireAllTags` /
`requireAllTools` switches are gone.

```json
{"op": "create_cookbook",
 "payload": {"name": "Weeknight, under 30",
             "description": "Dishes for under 30 minutes, mostly in a single pot.",
             "queryFilterString": "tags.name CONTAINS ALL [\"quick\", \"one-pot\"]"}}
```

| Pattern | Example |
|---|---|
| Match any of | `tags.name IN ["Dinner", "Lunch"]` |
| Match all of | `tags.name CONTAINS ALL ["Vegan", "Quick"]` |
| Exclude | `tags.name NOT IN ["Dessert"]` |
| Combine | `recipeCategory.name IN ["Dessert"] AND rating > 3` |
| By date | `createdAt > "2026-01-01"` |
| By equipment | `tools.name IN ["Air Fryer"]` |
| Never cooked | `lastMade = null` |

Operators: `IN`, `NOT IN`, `CONTAINS ALL`, `LIKE`, `NOT LIKE`, `=`, `<>`,
`>`, `<`, `>=`, `<=`, joined with `AND` / `OR` and grouped with brackets.
Filterable are the recipe fields and their relations — categories, tags,
tools, `rating`, `lastMade`, `createdAt`, household and user. `extras` is not
filterable at all, which is why anything meant to drive a selection belongs
in a tag.

Mealie validates the string on write and answers 422 for one it cannot
build. The syntax is version-dependent, so where you can reach the
interface, the safest filter is the one built there and copied out of the
cookbook editor.

**An empty filter is not a neutral default.** A cookbook without one matches
every recipe. That is exactly what a payload in the pre-2.0 shape produces,
because Mealie ignores unknown fields instead of rejecting them — so `apply`
refuses such a payload before the first write:

```console
$ python3 .../mealie_ctx.py apply actions.json --dry-run
create_cookbook: tags, requireAllTags is not a cookbook field since Mealie 2.0
and would be ignored, leaving a cookbook that matches everything. Use one
"queryFilterString", e.g. tags.name IN ["Quick"] AND rating > 3
```

## Repairing after a cleanup

Cookbooks are the only entity that breaks silently. A merged tag, a deleted
category, a renamed tool — and the filter grasps at nothing. So: after every
cleanup of categories, tags or tools, check the filters. It is the closing
step of those runs.

| Cause | Repair |
|---|---|
| tag was merged | rewrite the filter onto the survivor |
| tag moved to another entity | rewrite onto that entity |
| category demoted to a tag | change the condition from category to tag |
| tool deleted by the gating test | drop the condition or use the method tag |
| filter references an id | switch to the name — names survive a rebuild |
| the vocabulary is gone entirely | delete the cookbook |

`update_cookbook` changes the rule in place, so links to the cookbook stay
valid:

```json
{"op": "update_cookbook",
 "payload": {"id": "<cookbook-id>",
             "queryFilterString": "tags.name IN [\"quick\"]"}}
```

Deleting a cookbook loses no recipe, only a saved filter — the one entity in
the whole rule set where deletion is nearly consequence-free. Be generous:
zero hits with an intact filter means the need was not real, and two
cookbooks with largely the same hit set are one.

## Order

Cookbooks come last. They filter on vocabulary, so building them before the
categories and tags are settled means building on terms that get merged away
in the next pass — and the filter empties without a sound. `ORDER` puts
`create_cookbook` after every organizer operation for that reason.
