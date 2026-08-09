# Cookbooks

A cookbook in Mealie is not a collection of recipes but a **saved filter
rule**. It fills itself: whatever matches the rule appears in it, including
recipes imported later. Almost everything else follows from that.

## Phase 1 - Analysis

    ctx cookbooks

Returns the existing cookbooks plus categories, tags and tools, each with a
recipe count. From that you can estimate how large a planned cookbook would
be.

Ask about the purpose before designing rules. Typical patterns:

- **Everyday** - quick, few ingredients, meal-prep
- **Occasion** - guests, holidays, barbecue
- **Diet** - vegetarian, vegan, gluten-free
- **Course** - desserts, side dishes, breakfast
- **Season** - summer, autumn
- **Pantry** - one-pot, oven dish, leftovers

## Phase 2 - Plan, then stop

Plan per cookbook:

    Cookbook: Quick weeknight cooking
      RULE     tags: quick AND one-pot
      MATCHES  about 18 recipes
      DESCR.   Dishes for under 30 minutes, mostly in a single pot.
      GAP      "quick" has only 6 recipes – check its assignment?

Always give the estimated number of matches. Below about five matches a
cookbook is not worth it; say so and propose assigning the tags more widely
first.

### Designing rules

`requireAllCategories`, `requireAllTags`, `requireAllTools` switch between
AND and OR. The default is OR - which quickly produces cookbooks containing
half of everything. Set them deliberately:

- **OR** for collections: desserts = category Dessert OR tag sweets
- **AND** for intersections: quick AND vegetarian

More than two or three conditions makes a cookbook unpredictable. Build two
cookbooks instead.

Use only objects that already exist. If the rule needs a new tag, that is a
separate task: create the tag and assign it to recipes first (see
`references/organizers.md`), then the cookbook. A cookbook built on a
freshly created tag that is assigned nowhere is empty.

### Description

One or two sentences naming the purpose, not repeating the rule. Not:
"Recipes tagged quick and one-pot." Instead: "Dishes for under 30 minutes,
mostly in a single pot - for evenings when time is short."

### Public

`public: true` makes the cookbook reachable via the public group link. Ask
instead of setting it.

## Phase 3 - Execution

    apply actions.json

Afterwards check whether the number of matches meets the estimate - if it is
far off, the AND/OR setting is usually wrong. Report: CREATED (name, rule,
matches) · CHANGED · OPEN (discarded ideas with a reason).

## Reworking existing cookbooks

Common findings: empty cookbooks (the rule points at deleted or renamed
tags), oversized cookbooks (OR instead of AND), duplicates with a marginally
different rule. `update_cookbook` changes the rule without recreating the
cookbook - links to it stay valid.

## With the MCP server

`create_cookbook(name=..., tags=[...], categories=[...], tools=[...])` takes
the same name lists and writes the filter itself, matching your names to
Mealie's stored casing. `require_all=True` is the AND/OR switch, one flag for
all three lists instead of three.

`list_cookbooks()` is the analysis call and the only source of the ids the
other three need - names alone address nothing here.

`update_cookbook(cookbook_id, ...)` takes the same arguments and only changes
the fields you pass - never delete and recreate, that throws away the id.
`query_filter=""` clears the filter. `delete_cookbook(cookbook_id)` is for a
cookbook that should not exist at all; it removes the rule, not the recipes,
but any link to the cookbook dies with it - so it belongs in the plan and
needs approval like any other destructive step.

Reach for `query_filter` only for what names cannot express; it cannot be
combined with the name lists:

| Pattern | Example |
|---|---|
| Match any of | `tags.name IN ["Dinner", "Lunch"]` |
| Match all of | `tags.name CONTAINS ALL ["Vegan", "Quick"]` |
| Combine | `recipeCategory.name IN ["Dessert"] AND rating > 3` |
| By date | `createdAt > "2026-01-01"` |
| By equipment | `tools.name IN ["Air Fryer"]` |

Verify with `get_cookbook_recipes(cookbook_id)` afterwards - an overly narrow
filter matches nothing, which is easy to miss.
