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
